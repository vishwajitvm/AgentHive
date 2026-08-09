import time
import json
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.models import Agent
from app.agents.orchestrator import orchestrator
from app.llm.router import router as llm_router
from app.logging.logger import get_logger
from app.core.exceptions import AgentRunError

logger = get_logger(__name__)

class MultiAgentEngine:
    """Core Multi-Agent Orchestration Engine supporting Supervisor, Swarm, and Router patterns.

    Pattern A - Hierarchical / Supervisor:
        Decomposes query into specialized sub-tasks, dispatches sub-tasks to target agents,
        collects results, and synthesizes a unified final answer.

    Pattern B - Swarm:
        Executes dynamic agent-to-agent handoff loop where agents transfer control
        using `[HANDOFF] agent_slug | {context}` tags.

    Pattern C - Router:
        Fast dynamic intent classification that analyzes user prompt and routes to
        the single optimal specialized agent.
    """

    async def get_candidate_agents(
        self,
        db: AsyncSession,
        target_agents: Optional[List[str]] = None
    ) -> List[Agent]:
        """Retrieves active candidate agents from DB, optionally filtered by slug or ID."""
        stmt = select(Agent).where(Agent.status == "active")
        res = await db.execute(stmt)
        all_active = res.scalars().all()

        if not target_agents:
            return list(all_active)

        target_set = {str(t).lower() for t in target_agents}
        filtered = [
            a for a in all_active
            if a.slug.lower() in target_set or str(a.id) in target_set or a.name.lower() in target_set
        ]
        return filtered if filtered else list(all_active)

    async def generate_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        use_parallel_llm: bool = False
    ) -> str:
        """Helper to invoke LLM router in either parallel speculative racing or standard mode."""
        if use_parallel_llm:
            return await llm_router.generate_parallel(
                prompt=prompt,
                system_prompt=system_prompt,
                db=db
            )
        else:
            return await llm_router.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                db=db
            )

    async def execute_router(
        self,
        query: str,
        db: AsyncSession,
        target_agents: Optional[List[str]] = None,
        use_parallel_llm: bool = False
    ) -> Dict[str, Any]:
        """Fast dynamic intent classification router."""
        start_time = time.time()
        candidates = await self.get_candidate_agents(db, target_agents)
        if not candidates:
            raise AgentRunError("No active candidate agents available for routing.")

        if len(candidates) == 1:
            selected_agent = candidates[0]
            reasoning = "Only one candidate agent available."
        else:
            agent_descriptions = "\n".join([
                f"- Slug: '{a.slug}' | Name: '{a.name}' | Type: '{a.agent_type}' | Tools: {a.tools_enabled} | Description: {a.description or 'None'}"
                for a in candidates
            ])

            routing_system_prompt = (
                "You are an Intent Classifier Router for a multi-agent system. "
                "Analyze the user query and select the single best agent to execute the request.\n\n"
                "Respond ONLY with valid JSON in the format:\n"
                "{\n"
                '  "selected_agent": "<agent_slug>",\n'
                '  "reasoning": "<brief explanation of why this agent was chosen>"\n'
                "}\n"
            )

            routing_user_prompt = f"User Query: {query}\n\nAvailable Agents:\n{agent_descriptions}"

            llm_output = await self.generate_llm(
                prompt=routing_user_prompt,
                system_prompt=routing_system_prompt,
                db=db,
                use_parallel_llm=use_parallel_llm
            )

            # Parse selection
            selected_slug = None
            reasoning = "Routed based on intent classification."
            try:
                # Clean markdown blocks if present
                clean_output = llm_output
                if "```json" in clean_output: clean_output = clean_output.split("```json")[1]
                if "```" in clean_output: clean_output = clean_output.split("```")[0]

                data = json.loads(clean_output.strip())
                if isinstance(data, dict):
                    selected_slug = data.get("selected_agent")
                    reasoning = data.get("reasoning", reasoning)
            except Exception:
                # Regex fallback for agent slug extraction
                match = re.search(r'"selected_agent"\s*:\s*"([^"]+)"', llm_output)
                if match:
                    selected_slug = match.group(1)

            # Match slug to agent object
            selected_agent = None
            if selected_slug:
                for a in candidates:
                    if a.slug.lower() == selected_slug.lower():
                        selected_agent = a
                        break

            if not selected_agent:
                selected_agent = candidates[0]
                reasoning += f" (Fallback to default agent '{selected_agent.slug}')"

        logger.info("Router pattern selected agent", selected_agent=selected_agent.slug, query=query)

        # Execute chosen agent
        run_res = await orchestrator.execute_run(
            agent_id=selected_agent.id,
            query=query,
            db=db
        )

        elapsed = round(time.time() - start_time, 2)
        return {
            "success": run_res.get("status") == "completed",
            "status": run_res.get("status", "unknown"),
            "pattern": "router",
            "selected_agent": selected_agent.slug,
            "reasoning": reasoning,
            "response": run_res.get("output", ""),
            "steps_count": run_res.get("steps_count", 1),
            "execution_time_seconds": elapsed,
            "details": {
                "agent_id": selected_agent.id,
                "agent_name": selected_agent.name,
                "candidate_agents": [a.slug for a in candidates],
                "agent_run_id": run_res.get("agent_run_id")
            }
        }

    async def execute_supervisor(
        self,
        query: str,
        db: AsyncSession,
        target_agents: Optional[List[str]] = None,
        use_parallel_llm: bool = False
    ) -> Dict[str, Any]:
        """Hierarchical / Supervisor orchestration pattern."""
        start_time = time.time()
        candidates = await self.get_candidate_agents(db, target_agents)
        if not candidates:
            raise AgentRunError("No active candidate agents available for supervisor orchestration.")

        agent_descriptions = "\n".join([
            f"- Slug: '{a.slug}' | Name: '{a.name}' | Tools: {a.tools_enabled} | Description: {a.description or 'None'}"
            for a in candidates
        ])

        decomp_system_prompt = (
            "You are a Supervisor Agent in a multi-agent orchestration architecture. "
            "Your job is to analyze the complex user request, break it down into distinct sub-tasks, "
            "and assign each sub-task to the most appropriate specialized subagent.\n\n"
            "Respond ONLY with valid JSON in this exact structure:\n"
            "{\n"
            '  "reasoning": "<High-level decomposition strategy>",\n'
            '  "subtasks": [\n'
            '    {"agent_slug": "<valid_agent_slug>", "sub_query": "<detailed subtask instruction>"}\n'
            "  ]\n"
            "}\n"
        )
        decomp_user_prompt = f"User Request: {query}\n\nAvailable Specialized Agents:\n{agent_descriptions}"

        decomp_output = await self.generate_llm(
            prompt=decomp_user_prompt,
            system_prompt=decomp_system_prompt,
            db=db,
            use_parallel_llm=use_parallel_llm
        )

        subtasks = []
        reasoning = "Decomposed request into specialized sub-tasks."
        try:
            clean_output = decomp_output
            if "```json" in clean_output: clean_output = clean_output.split("```json")[1]
            if "```" in clean_output: clean_output = clean_output.split("```")[0]
            parsed = json.loads(clean_output.strip())
            if isinstance(parsed, dict):
                subtasks = parsed.get("subtasks", [])
                reasoning = parsed.get("reasoning", reasoning)
        except Exception:
            logger.warning("Failed to parse supervisor decomposition JSON, falling back to direct routing.")

        if not subtasks:
            # Fallback to single router execution
            return await self.execute_router(query=query, db=db, target_agents=target_agents, use_parallel_llm=use_parallel_llm)

        # Dispatch subtasks to subagents
        subagent_results = []
        agent_map = {a.slug.lower(): a for a in candidates}

        for st in subtasks:
            st_slug = str(st.get("agent_slug", "")).lower()
            st_query = st.get("sub_query", query)

            agent_obj = agent_map.get(st_slug)
            if not agent_obj:
                # Pick fallback agent
                agent_obj = candidates[0]
                st_slug = agent_obj.slug

            logger.info("Supervisor dispatching subtask", subagent=st_slug, sub_query=st_query)
            run_res = await orchestrator.execute_run(
                agent_id=agent_obj.id,
                query=st_query,
                db=db
            )
            subagent_results.append({
                "agent_slug": agent_obj.slug,
                "agent_name": agent_obj.name,
                "sub_query": st_query,
                "status": run_res.get("status"),
                "output": run_res.get("output", "")
            })

        # Synthesis step
        results_formatted = "\n\n".join([
            f"=== Result from [{sr['agent_name']} ({sr['agent_slug']})] ===\nSub-Task: {sr['sub_query']}\nStatus: {sr['status']}\nOutput:\n{sr['output']}"
            for sr in subagent_results
        ])

        synthesis_system_prompt = (
            "You are a Supervisor Agent. You have received completed sub-task outputs from specialized subagents. "
            "Synthesize these findings into a comprehensive, cohesive, and unified response to the original user request."
        )
        synthesis_user_prompt = (
            f"Original User Request: {query}\n\n"
            f"Decomposition Logic: {reasoning}\n\n"
            f"Subagent Execution Findings:\n{results_formatted}\n\n"
            "Synthesize the complete final answer now:"
        )

        final_synthesis = await self.generate_llm(
            prompt=synthesis_user_prompt,
            system_prompt=synthesis_system_prompt,
            db=db,
            use_parallel_llm=use_parallel_llm
        )

        elapsed = round(time.time() - start_time, 2)
        return {
            "success": True,
            "status": "completed",
            "pattern": "supervisor",
            "reasoning": reasoning,
            "subtasks": subtasks,
            "subagent_results": subagent_results,
            "response": final_synthesis,
            "execution_time_seconds": elapsed,
            "details": {
                "candidate_agents": [a.slug for a in candidates],
                "num_subtasks": len(subtasks)
            }
        }

    async def execute_swarm(
        self,
        query: str,
        db: AsyncSession,
        initial_agent: Optional[str] = None,
        target_agents: Optional[List[str]] = None,
        max_handoffs: int = 5,
        use_parallel_llm: bool = False
    ) -> Dict[str, Any]:
        """Swarm orchestration pattern with dynamic agent-to-agent handoffs."""
        start_time = time.time()
        candidates = await self.get_candidate_agents(db, target_agents)
        if not candidates:
            raise AgentRunError("No active candidate agents available for swarm execution.")

        agent_map = {a.slug.lower(): a for a in candidates}

        # Resolve initial agent
        current_agent = None
        if initial_agent:
            current_agent = agent_map.get(initial_agent.lower())

        if not current_agent:
            # Route initial query to find best starting agent
            current_agent = candidates[0]

        handoff_chain = []
        current_query = query
        handoff_count = 0
        final_response = ""

        candidate_slugs = ", ".join([a.slug for a in candidates])

        while handoff_count < max_handoffs:
            handoff_chain.append(current_agent.slug)
            logger.info("Swarm execution step", step=handoff_count + 1, current_agent=current_agent.slug, query=current_query)

            # Append handoff tag instructions to current query
            swarm_context_prompt = (
                f"{current_query}\n\n"
                "DYNAMIC SWARM HANDOFF INSTRUCTIONS:\n"
                f"You are agent '{current_agent.slug}' in a Swarm. If your capabilities/tools are insufficient or another agent is better suited, "
                "you MAY hand off execution to another agent by including this tag at the very beginning of your output:\n"
                "[HANDOFF] target_agent_slug | {\"context\": \"Refined task instructions or context for the target agent\"}\n"
                f"Available swarm agents: [{candidate_slugs}]\n"
                "If no handoff is needed, provide your final response using [ANSWER] as standard."
            )

            run_res = await orchestrator.execute_run(
                agent_id=current_agent.id,
                query=swarm_context_prompt,
                db=db
            )

            output_text = run_res.get("output", "")

            # Check for handoff tag: [HANDOFF] target_slug | {json or text}
            handoff_match = re.search(r'\[HANDOFF\]\s*([a-zA-Z0-9_\-]+)\s*\|\s*({.*?}|.*)', output_text, re.DOTALL)
            
            if handoff_match:
                next_slug = handoff_match.group(1).strip().lower()
                next_context_raw = handoff_match.group(2).strip()

                # Extract context if JSON
                next_context = next_context_raw
                try:
                    parsed_ctx = json.loads(next_context_raw)
                    if isinstance(parsed_ctx, dict) and "context" in parsed_ctx:
                        next_context = parsed_ctx["context"]
                except Exception:
                    pass

                next_agent = agent_map.get(next_slug)
                if next_agent and next_agent.slug != current_agent.slug:
                    logger.info("Swarm handoff triggered", from_agent=current_agent.slug, to_agent=next_slug)
                    current_agent = next_agent
                    current_query = f"Handoff Context from previous agent ({handoff_chain[-1]}):\n{next_context}"
                    handoff_count += 1
                    continue
                else:
                    logger.warning("Swarm handoff target invalid or self-referential", target=next_slug)

            # No handoff triggered, loop ends with final answer
            final_response = output_text
            break

        if not final_response:
            final_response = f"Swarm process concluded after max handoffs ({max_handoffs}). Chain: {' -> '.join(handoff_chain)}"

        elapsed = round(time.time() - start_time, 2)
        return {
            "success": True,
            "status": "completed",
            "pattern": "swarm",
            "initial_agent": handoff_chain[0] if handoff_chain else current_agent.slug,
            "final_agent": current_agent.slug,
            "handoff_chain": handoff_chain,
            "handoffs_count": len(handoff_chain) - 1,
            "response": final_response,
            "execution_time_seconds": elapsed,
            "details": {
                "candidate_agents": [a.slug for a in candidates]
            }
        }

    async def orchestrate(
        self,
        query: str,
        db: AsyncSession,
        pattern: str = "router",
        target_agents: Optional[List[str]] = None,
        initial_agent: Optional[str] = None,
        use_parallel_llm: bool = False,
        max_handoffs: int = 5
    ) -> Dict[str, Any]:
        """Main entry point for multi-agent dynamic orchestration."""
        pattern_clean = (pattern or "router").strip().lower()

        if pattern_clean == "auto":
            # Classify pattern
            auto_prompt = (
                "Analyze the user query and classify the best orchestration pattern:\n"
                "1. 'supervisor': For complex multi-step tasks requiring multiple specialized perspectives/sub-tasks.\n"
                "2. 'swarm': For sequential multi-stage workflows or collaborative problem solving with handoffs.\n"
                "3. 'router': For single-intent questions or tasks easily handled by one specialized agent.\n\n"
                "Respond ONLY in JSON format:\n"
                '{"pattern": "supervisor" | "swarm" | "router"}'
            )
            llm_res = await self.generate_llm(prompt=f"User Query: {query}", system_prompt=auto_prompt, db=db, use_parallel_llm=use_parallel_llm)
            try:
                clean_res = llm_res
                if "```json" in clean_res: clean_res = clean_res.split("```json")[1]
                if "```" in clean_res: clean_res = clean_res.split("```")[0]
                parsed = json.loads(clean_res.strip())
                pattern_clean = parsed.get("pattern", "router").lower()
            except Exception:
                pattern_clean = "router"

        if pattern_clean == "supervisor":
            return await self.execute_supervisor(
                query=query,
                db=db,
                target_agents=target_agents,
                use_parallel_llm=use_parallel_llm
            )
        elif pattern_clean == "swarm":
            return await self.execute_swarm(
                query=query,
                db=db,
                initial_agent=initial_agent,
                target_agents=target_agents,
                max_handoffs=max_handoffs,
                use_parallel_llm=use_parallel_llm
            )
        else:
            return await self.execute_router(
                query=query,
                db=db,
                target_agents=target_agents,
                use_parallel_llm=use_parallel_llm
            )

multi_agent_engine = MultiAgentEngine()
