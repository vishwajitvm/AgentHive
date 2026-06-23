const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function getHealth() {
  const response = await fetch(`${API_URL}/health`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Health check failed');
  return response.json();
}

export async function getReadyStatus() {
  const response = await fetch(`${API_URL}/ready`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Ready check failed');
  return response.json();
}

// Agents API
export async function listAgents() {
  const response = await fetch(`${API_URL}/api/agents`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to list agents');
  return response.json();
}

export async function getAgent(id: number) {
  const response = await fetch(`${API_URL}/api/agents/${id}`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to fetch agent details');
  return response.json();
}

export async function listTools() {
  const response = await fetch(`${API_URL}/api/tools`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to list tools');
  return response.json();
}

export async function runTool(slug: string, payload: any) {
  const response = await fetch(`${API_URL}/api/tools/${slug}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to execute tool');
  }
  return response.json();
}

export async function createAgent(payload: any) {
  const response = await fetch(`${API_URL}/api/agents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to create agent');
  }
  return response.json();
}

export async function updateAgent(id: number, payload: any) {
  const response = await fetch(`${API_URL}/api/agents/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error('Failed to update agent');
  return response.json();
}

export async function deleteAgent(id: number) {
  const response = await fetch(`${API_URL}/api/agents/${id}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete agent');
  return response.json();
}

export async function runAgent(agentId: number, query: string, background: boolean = false) {
  const response = await fetch(`${API_URL}/api/agents/${agentId}/run?background=${background}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  if (!response.ok) throw new Error('Failed to run agent');
  return response.json();
}

export async function uploadToWorkspace(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_URL}/api/agents/workspace/upload`, {
    method: 'POST',
    body: formData
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to upload file');
  }
  return response.json();
}

export async function getRunStatus(runId: number) {
  const response = await fetch(`${API_URL}/api/agents/runs/${runId}`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to fetch run status');
  return response.json();
}

export async function getRunSteps(runId: number) {
  const response = await fetch(`${API_URL}/api/agents/runs/${runId}/steps`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to fetch run step details');
  return response.json();
}

// Models & Policies API
export async function listProviders() {
  const response = await fetch(`${API_URL}/api/models/providers`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to list providers');
  return response.json();
}

export async function configureProvider(payload: any) {
  const response = await fetch(`${API_URL}/api/models/providers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error('Failed to update provider configuration');
  return response.json();
}

export async function listPolicies() {
  const response = await fetch(`${API_URL}/api/models/policies`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to list policies');
  return response.json();
}

export async function createPolicy(payload: any) {
  const response = await fetch(`${API_URL}/api/models/policies`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error('Failed to create fallback policy');
  return response.json();
}

export async function activatePolicy(policyId: number) {
  const response = await fetch(`${API_URL}/api/models/policies/${policyId}/activate`, {
    method: 'PUT'
  });
  if (!response.ok) throw new Error('Failed to activate policy');
  return response.json();
}

// Workflows API
export async function listWorkflows() {
  const response = await fetch(`${API_URL}/api/workflows`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to list workflows');
  return response.json();
}

export async function createWorkflow(payload: any) {
  const response = await fetch(`${API_URL}/api/workflows`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to create workflow');
  }
  return response.json();
}

export async function runWorkflow(id: number, query: string) {
  const response = await fetch(`${API_URL}/api/workflows/${id}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  if (!response.ok) throw new Error('Failed to execute workflow');
  return response.json();
}

export async function getWorkflowRun(runId: number) {
  const response = await fetch(`${API_URL}/api/workflows/runs/${runId}`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to retrieve workflow run status');
  return response.json();
}

export async function resumeWorkflowRun(runId: number) {
  const response = await fetch(`${API_URL}/api/workflows/runs/${runId}/resume`, {
    method: 'POST'
  });
  if (!response.ok) throw new Error('Failed to resume workflow run');
  return response.json();
}

// Logs API
export async function getAgentRuns(agentId?: number, status?: string) {
  let url = `${API_URL}/api/logs/runs?limit=25`;
  if (agentId) url += `&agent_id=${agentId}`;
  if (status) url += `&status=${status}`;
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to fetch runs');
  return response.json();
}

export async function getLlmCalls(agentRunId?: number) {
  let url = `${API_URL}/api/logs/llm-calls?limit=25`;
  if (agentRunId) url += `&agent_run_id=${agentRunId}`;
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to fetch LLM call details');
  return response.json();
}

export async function getSystemStats() {
  const response = await fetch(`${API_URL}/api/logs/stats`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to fetch telemetry metrics');
  return response.json();
}

// Settings API
export async function getEnvSettings() {
  const response = await fetch(`${API_URL}/api/settings/env`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to fetch environment variables');
  return response.json();
}

export async function saveEnvSetting(key: string, value: string) {
  const response = await fetch(`${API_URL}/api/settings/env`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key, value })
  });
  if (!response.ok) throw new Error('Failed to update secret value');
  return response.json();
}
