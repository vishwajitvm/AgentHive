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
        timeout_seconds: int = 120,
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
            "\n\nInstructions:\n"
            "You run in a loop. You can think, call tools, and reply. "
            "To call a tool, respond with:\n"
            "[TOOL] tool_slug | {\"arg_key\": \"arg_value\"}\n"
            "To provide your final answer to the user, respond with:\n"
            "[ANSWER] your final message\n\n"
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
            tool_match = re.search(r'\[TOOL\]\s*([a-zA-Z0-9_\-]+)\s*\|\s*({.*?})', llm_output, re.DOTALL)
            answer_match = re.search(r'\[ANSWER\]\s*(.*)', llm_output, re.DOTALL)

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
                final_response = answer_match.group(1).strip()
                break
            else:
                # Fallback: if no tag is found, treat entire text as answer
                logger.info("No action tag found in agent output, using full text as answer", run_id=agent_run_id)
                final_response = llm_output.strip()
                break

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
