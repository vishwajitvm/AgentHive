import time
import json
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.llm.router import router as llm_router
from app.tools.registry import tool_registry
from app.core.exceptions import AgentRunError
from app.core.toon import format_agent_context, summarize_tool_result, compress_prompt
from app.logging.logger import get_logger

logger = get_logger(__name__)

class BaseAgent:
    """Core Agent class executing step-by-step reasoning and tool call actions."""

    def __init__(
        self,
        name: str,
        agent_type: str,
        system_prompt: str,
        allowed_tools: List[str] = None,
        max_steps: int = 10,
        timeout_seconds: int = 300,
        model_policy_id: Optional[int] = None
    ):
        self.name = name
        self.agent_type = agent_type
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools or []
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds
        self.model_policy_id = model_policy_id

    async def run(
        self,
        query: str,
        agent_run_id: int,
        db: AsyncSession,
        history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Runs the agent loop, executing thoughts, tools, and returns the final answer."""
        start_time = time.time()
        step_number = 1
        chat_history = list(history or [])
        
        # Import models inside function to avoid circular dependency
        from app.logs.models import AgentStep, ToolCall, AgentRun
        
        logger.info("Starting agent run", agent_name=self.name, query=query, run_id=agent_run_id)

        # Append initial task query to history
        chat_history.append({"role": "user", "content": query})

        # Base instructions on how to call tools or respond
        tool_instructions = (
            "\n\nCRITICAL INSTRUCTIONS TO PREVENT HALLUCINATION:\n"
            "1. You run in a loop. You can think, call tools, and reply.\n"
            "2. DO NOT FAKE OR HALLUCINATE TOOL OUTPUTS. If you call a tool, you MUST STOP and wait for the system to provide the real observation.\n"
            "3. To call a tool, respond exactly with this format (and NOTHING ELSE):\n"
            "[TOOL] tool_slug | {\"arg_key\": \"arg_value\"}\n"
            "4. To provide your final answer to the user, respond exactly with:\n"
            "[ANSWER] {\n"
            "  \"reasoning\": \"Step-by-step logic detailing how you arrived at this conclusion\",\n"
            "  \"confidence_score\": \"0.0 to 1.0 (e.g. 0.95)\",\n"
            "  \"answer\": \"Your final message to the user\"\n"
            "}\n\n"
            "EXAMPLE TOOL CALL:\n"
            "[TOOL] youtube_transcript_tool | {\"url\": \"https://www.youtube.com/watch?v=123\"}\n\n"
            "EXAMPLE FINAL ANSWER:\n"
            "[ANSWER] {\n"
            "  \"reasoning\": \"The transcript says X, which verifies the claim.\",\n"
            "  \"confidence_score\": \"0.99\",\n"
            "  \"answer\": \"The claims in the video are accurate based on...\"\n"
            "}\n\n"
            f"Available tools for this session: {', '.join(self.allowed_tools) or 'None'}\n"
        )
        
        comp_system_prompt = self.system_prompt + tool_instructions

        final_response = None
        
        while step_number <= self.max_steps:
            # Check for timeout
            elapsed = time.time() - start_time
            if elapsed > self.timeout_seconds:
                logger.error("Agent execution timed out", run_id=agent_run_id, elapsed=elapsed)
                raise AgentRunError(f"Agent execution timed out after {elapsed:.1f} seconds")

            # 1. Format the current prompt using TOON optimization
            toon_context = format_agent_context(
                system_prompt=comp_system_prompt,
                history=chat_history
            )

            # 2. Call LLM Router
            try:
                llm_output = await llm_router.generate(
                    prompt=toon_context,
                    agent_run_id=agent_run_id,
                    db=db
                )
            except Exception as e:
                logger.exception("LLM Router generation failed in agent loop", run_id=agent_run_id)
                raise AgentRunError(f"LLM Routing failed: {str(e)}")

            # Save thought/step log
            logger.info("Agent step completed", run_id=agent_run_id, step=step_number)
            step_log = AgentStep(
                agent_run_id=agent_run_id,
                step_number=step_number,
                action_type="thought",
                content=llm_output
            )
            db.add(step_log)
            await db.commit()

            # 3. Parse action (TOOL or ANSWER)
            # Extremely robust tool extraction: match slug | {json args}
            tool_match = None
            tool_matches = list(re.finditer(r'(?:\[TOOL\]\s*)?([a-zA-Z0-9_\-]+)(?:\])?\s*\|\s*({.*?})', llm_output, re.DOTALL))
            for tm in tool_matches:
                slug = tm.group(1).strip()
                if slug in self.allowed_tools:
                    tool_match = tm
                    break
            
            # Aggressive Universal Extraction Parser for Answer
            answer_match = re.search(r'\[ANSWER\]\s*(.*)', llm_output, re.DOTALL)
            
            if not answer_match:
                # Fallback: check if the model just output raw JSON with an "answer" key
                if '"answer":' in llm_output.lower():
                    # Attempt to extract outermost braces
                    json_match = re.search(r'(\{.*\})', llm_output, re.DOTALL)
                    if json_match:
                        # Wrap it in a fake regex match object for the rest of the code
                        class FakeMatch:
                            def group(self, idx): return json_match.group(1)
                            def start(self): return json_match.start()
                        answer_match = FakeMatch()
            
            if not answer_match:
                # Fallback: 1B models often hallucinate markdown like "### Answer" or "**Answer**:"
                # Let's extract everything after that phrase and wrap it in a mock JSON string
                md_answer_match = re.search(r'(?:###|\*\*)?\s*Answer(?:s)?\s*(?:\*\*)?:?\s*(.*)', llm_output, re.IGNORECASE | re.DOTALL)
                if md_answer_match:
                    raw_text = md_answer_match.group(1).strip()
                    # Clean up by trying to find reasoning / confidence
                    reasoning = "Extracted automatically."
                    confidence = "1.0"
                    
                    reasoning_match = re.search(r'(?:###|\*\*)?\s*Reasoning\s*(?:\*\*)?:?\s*(.*?)(?:\n###|$)', llm_output, re.IGNORECASE | re.DOTALL)
                    if reasoning_match:
                        reasoning = reasoning_match.group(1).strip()
                        raw_text = raw_text.replace(reasoning_match.group(0), "").strip()

                    conf_match = re.search(r'(?:###|\*\*)?\s*Confidence(?: Score)?\s*(?:\*\*)?:?\s*([0-9\.]+)', llm_output, re.IGNORECASE)
                    if conf_match:
                        confidence = conf_match.group(1).strip()
                        raw_text = raw_text.replace(conf_match.group(0), "").strip()

                    fake_json = json.dumps({
                        "reasoning": reasoning,
                        "confidence_score": confidence,
                        "answer": raw_text
                    })
                    class FakeMatch2:
                        def group(self, idx): return fake_json
                        def start(self): return md_answer_match.start()
                    answer_match = FakeMatch2()
            
            # If the model hallucinates both a valid tool and an answer in the same step, pick whichever came first
            if tool_match and answer_match:
                if tool_match.start() < answer_match.start():
                    answer_match = None
                else:
                    tool_match = None

            # Extreme Fallback: If it's just a raw text response and not trying to call a tool, assume it's the final answer
            if not tool_match and not answer_match and len(llm_output.strip()) > 5:
                # But only if it didn't explicitly try to call a tool and failed syntax
                if "[TOOL]" not in llm_output and "tool_slug" not in llm_output:
                    fake_json = json.dumps({
                        "reasoning": "Direct response inferred by parser.",
                        "confidence_score": "1.0",
                        "answer": llm_output.strip()
                    })
                    class FakeMatch3:
                        def group(self, idx): return fake_json
                        def start(self): return 0
                    answer_match = FakeMatch3()

            if tool_match:
                tool_slug = tool_match.group(1).strip()
                tool_args_str = tool_match.group(2).strip()

                # Parse JSON arguments
                try:
                    tool_args = json.loads(tool_args_str)
                except Exception as je:
                    tool_args = {}
                    tool_output = f"Error: Failed to parse tool arguments. JSON is invalid: {str(je)}"
                
                # Check if tool is allowed
                if tool_slug not in self.allowed_tools:
                    tool_output = f"Security Block: Tool '{tool_slug}' is not authorized for this agent."
                else:
                    # Execute tool
                    tool = tool_registry.get_tool(tool_slug)
                    if not tool:
                        tool_output = f"Error: Tool '{tool_slug}' not found in registry."
                    else:
                        tool_start = time.perf_counter()
                        try:
                            logger.info("Running tool", run_id=agent_run_id, tool=tool_slug)
                            tool_output_raw = await tool.run(**tool_args)
                            tool_latency = int((time.perf_counter() - tool_start) * 1000)
                            
                            # TOON Optimization: Summarize large tool outputs
                            tool_output = summarize_tool_result(tool_output_raw)
                            
                            # Log tool call to database
                            db_tool_call = ToolCall(
                                agent_run_id=agent_run_id,
                                tool_name=tool_slug,
                                tool_input=json.dumps(tool_args),
                                tool_output=tool_output,
                                latency_ms=tool_latency,
                                status="success"
                            )
                            db.add(db_tool_call)
                            await db.commit()
                        except Exception as te:
                            tool_latency = int((time.perf_counter() - tool_start) * 1000)
                            tool_output = f"Error: Tool execution failed: {str(te)}"
                            db_tool_call = ToolCall(
                                agent_run_id=agent_run_id,
                                tool_name=tool_slug,
                                tool_input=json.dumps(tool_args),
                                tool_output=tool_output,
                                latency_ms=tool_latency,
                                status="error"
                            )
                            db.add(db_tool_call)
                            await db.commit()

                # Add to chat history for next generation
                chat_history.append({"role": "assistant", "content": llm_output})
                chat_history.append({"role": "user", "content": f"[Observation from {tool_slug}]: {tool_output}"})

                # Log step observation
                step_log_obs = AgentStep(
                    agent_run_id=agent_run_id,
                    step_number=step_number,
                    action_type="observation",
                    content=f"Executed tool: {tool_slug}. Result: {tool_output}"
                )
                db.add(step_log_obs)
                await db.commit()

            elif answer_match:
                raw_ans = answer_match.group(1).strip()
                # Attempt to parse metrics
                try:
                    # Strip any trailing markdown block ticks or extra text small models might add
                    json_str = raw_ans
                    if '```json' in json_str: json_str = json_str.split('```json')[1]
                    if '```' in json_str: json_str = json_str.split('```')[0]
                    
                    ans_json = json.loads(json_str.strip())
                    if isinstance(ans_json, dict) and 'answer' in ans_json:
                        conf = ans_json.get('confidence_score', 'N/A')
                        reason = ans_json.get('reasoning', 'N/A')
                        ans_text = ans_json['answer']
                        final_response = f"**Agent Confidence Score**: {conf}\n\n**Reasoning Context**:\n{reason}\n\n**Final Answer**:\n{ans_text}"
                    else:
                        final_response = raw_ans
                except Exception:
                    final_response = raw_ans
                break
            else:
                # Fallback: if no tag is found, don't break, remind the model!
                logger.warning("No action tag found. Reminding the model.", run_id=agent_run_id)
                chat_history.append({"role": "assistant", "content": llm_output})
                chat_history.append({"role": "user", "content": "[System Error: You must output exactly [TOOL] or [ANSWER] with the required JSON format. Please try again.]"})
                
                # Log step observation
                step_log_obs = AgentStep(
                    agent_run_id=agent_run_id,
                    step_number=step_number,
                    action_type="observation",
                    content="[System Warning] Format violation detected."
                )
                db.add(step_log_obs)
                await db.commit()
                
                step_number += 1
                continue

            step_number += 1

        if not final_response:
            final_response = "Error: Agent exceeded maximum reasoning steps without producing a final answer."
            logger.error("Agent exceeded max steps", run_id=agent_run_id, max_steps=self.max_steps)

        # Log final step
        step_log_final = AgentStep(
            agent_run_id=agent_run_id,
            step_number=step_number,
            action_type="final_answer",
            content=final_response
        )
        db.add(step_log_final)
        
        # Update agent run status
        run_res = await db.execute(select(AgentRun).where(AgentRun.id == agent_run_id))
        agent_run = run_res.scalar_one()
        agent_run.status = "completed" if "Error:" not in final_response else "failed"
        agent_run.output_response = final_response
        await db.commit()

        logger.info("Agent run finished", run_id=agent_run_id, status=agent_run.status)
        return {
            "status": agent_run.status,
            "output": final_response,
            "steps_count": step_number,
            "elapsed_seconds": round(time.time() - start_time, 2)
        }
