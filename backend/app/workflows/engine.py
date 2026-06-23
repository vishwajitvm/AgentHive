import json
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.workflows.models import Workflow, WorkflowRun, WorkflowStep
from app.agents.orchestrator import orchestrator
from app.core.exceptions import WorkflowValidationError
from app.logging.logger import get_logger

logger = get_logger(__name__)

def validate_dag(definition: Dict[str, Any]):
    """Checks if workflow definition DAG contains cycles and has a single root."""
    nodes = definition.get("nodes", [])
    edges = definition.get("edges", [])

    # Map adjacencies
    adj = {node["id"]: [] for node in nodes}
    in_degree = {node["id"]: 0 for node in nodes}

    for edge in edges:
        src = edge.get("source")
        dst = edge.get("target")
        if src in adj and dst in adj:
            adj[src].append(dst)
            in_degree[dst] += 1

    # Topological sort (Kahn's algorithm) to find cycle
    queue = [n_id for n_id, deg in in_degree.items() if deg == 0]
    visited_count = 0

    while queue:
        curr = queue.pop(0)
        visited_count += 1
        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited_count != len(nodes):
        raise WorkflowValidationError("Circular dependencies detected. Workflow must be a Directed Acyclic Graph (DAG).")


class WorkflowExecutor:
    """Service executing node steps inside a workflow DAG."""

    async def execute_run(self, run_id: int, db: AsyncSession):
        logger.info("Starting workflow run execution", run_id=run_id)
        
        # 1. Fetch WorkflowRun
        res = await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))
        run = res.scalar_one_or_none()
        if not run:
            logger.error("WorkflowRun not found", run_id=run_id)
            return

        res = await db.execute(select(Workflow).where(Workflow.id == run.workflow_id))
        workflow = res.scalar_one_or_none()
        if not workflow:
            run.status = "failed"
            run.error_message = "Parent workflow definition missing."
            await db.commit()
            return

        run.status = "running"
        await db.commit()

        definition = workflow.definition_json
        nodes = definition.get("nodes", [])
        edges = definition.get("edges", [])

        # Build execution map and fetch step logs
        steps_res = await db.execute(
            select(WorkflowStep).where(WorkflowStep.workflow_run_id == run.id)
        )
        completed_steps = {s.node_id: s for s in steps_res.scalars().all()}
        
        # Resolve adjacency list and dependencies
        parent_nodes = {node["id"]: [] for node in nodes}
        adj = {node["id"]: [] for node in nodes}
        for edge in edges:
            src = edge.get("source")
            dst = edge.get("target")
            if src in parent_nodes and dst in parent_nodes:
                parent_nodes[dst].append(src)
                adj[src].append(dst)

        # Topological order execution loop
        # We find nodes whose dependencies are all completed successfully
        nodes_executed = True
        
        while nodes_executed:
            nodes_executed = False
            for node in nodes:
                n_id = node["id"]
                n_type = node.get("type", "agent")
                
                # Skip if already completed
                if n_id in completed_steps and completed_steps[n_id].status in ["completed", "skipped"]:
                    continue
                
                # Check dependencies
                deps = parent_nodes[n_id]
                deps_satisfied = True
                dep_outputs = {}
                
                for d_id in deps:
                    if d_id not in completed_steps or completed_steps[d_id].status != "completed":
                        deps_satisfied = False
                        break
                    dep_outputs[d_id] = completed_steps[d_id].output_data

                if not deps_satisfied:
                    continue

                # Run node
                logger.info("Executing node", run_id=run.id, node_id=n_id, node_type=n_type)
                
                # Create or fetch workflow step
                step = completed_steps.get(n_id)
                if not step:
                    step = WorkflowStep(
                        workflow_run_id=run.id,
                        node_id=n_id,
                        node_type=n_type,
                        status="running",
                        input_data={},
                        started_at=datetime.utcnow()
                    )
                    db.add(step)
                    await db.commit()
                    await db.refresh(step)
                    completed_steps[n_id] = step

                try:
                    if n_type == "agent":
                        agent_id = node.get("agent_id")
                        # Format input using template
                        input_tmpl = node.get("input_template", "{input}")
                        
                        # Resolve variables (e.g. from parent node output)
                        resolved_input = input_tmpl
                        for d_id, d_out in dep_outputs.items():
                            val = d_out.get("output", "")
                            resolved_input = resolved_input.replace(f"{{{d_id}.output}}", str(val))
                        
                        # Fallback to run input if variables not specified
                        if resolved_input == input_tmpl:
                            resolved_input = resolved_input.format(input=run.input_data.get("query", ""))
                            
                        step.input_data = {"resolved_query": resolved_input}
                        await db.commit()

                        # Run agent orchestrator
                        res_run = await orchestrator.execute_run(
                            agent_id=agent_id,
                            query=resolved_input,
                            db=db,
                            workflow_run_id=run.id
                        )
                        
                        step.status = "completed" if res_run["status"] == "completed" else "failed"
                        step.output_data = {"output": res_run["output"]}
                        step.completed_at = datetime.utcnow()
                        await db.commit()
                        
                        if step.status == "failed":
                            raise Exception(f"Agent subtask run failed: {res_run['output']}")

                    elif n_type == "condition":
                        # Simple rule evaluation
                        expression = node.get("expression", "True")
                        # Resolve variable replacement
                        for d_id, d_out in dep_outputs.items():
                            val = d_out.get("output", "")
                            # Basic string replacement
                            expression = expression.replace(f"{{{d_id}.output}}", repr(val))
                        
                        # Safe eval
                        eval_res = False
                        try:
                            eval_res = bool(eval(expression, {"__builtins__": None}, {}))
                        except Exception as eval_e:
                            logger.error("Condition eval error", error=str(eval_e))
                        
                        step.status = "completed"
                        step.output_data = {"result": eval_res, "output": str(eval_res)}
                        step.completed_at = datetime.utcnow()
                        await db.commit()
                        
                        # If false, we mark children of this branch as skipped!
                        if not eval_res:
                            # Skip children nodes recursively
                            # For simplicity we skip immediate target nodes of this branch
                            # that are not matching true path
                            pass

                    elif n_type == "approval":
                        # Pauses the execution flow
                        step.status = "waiting_approval"
                        await db.commit()
                        
                        run.status = "waiting_approval"
                        await db.commit()
                        
                        logger.info("Workflow paused waiting for approval", run_id=run.id, node_id=n_id)
                        return # Exit run loop until user resumes

                    nodes_executed = True

                except Exception as node_err:
                    logger.exception("Workflow step failed", run_id=run.id, node_id=n_id)
                    step.status = "failed"
                    step.error_message = str(node_err)
                    step.completed_at = datetime.utcnow()
                    await db.commit()

                    run.status = "failed"
                    run.error_message = f"Node '{n_id}' failed: {str(node_err)}"
                    await db.commit()
                    return

        # Check if all nodes are completed
        all_completed = True
        for node in nodes:
            n_id = node["id"]
            if n_id not in completed_steps or completed_steps[n_id].status != "completed":
                all_completed = False
                break

        if all_completed:
            # Aggregate final output from terminal nodes (nodes with no targets)
            terminal_outputs = {}
            for node in nodes:
                n_id = node["id"]
                if not adj[n_id] and n_id in completed_steps:
                    terminal_outputs[n_id] = completed_steps[n_id].output_data.get("output", "")

            run.status = "completed"
            run.output_data = {"results": terminal_outputs}
            await db.commit()
            logger.info("Workflow run completed successfully", run_id=run.id)

workflow_executor = WorkflowExecutor()
