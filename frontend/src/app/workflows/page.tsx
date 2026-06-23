'use client';

import React, { useEffect, useState } from 'react';
import { listWorkflows, createWorkflow, runWorkflow, listAgents } from '../../lib/api';
import { Workflow, Play, Plus, Clock, CheckCircle, AlertTriangle, Layers, ListCollapse } from 'lucide-react';

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<number | null>(null);
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [firstAgentId, setFirstAgentId] = useState<number | ''>('');
  const [secondAgentId, setSecondAgentId] = useState<number | ''>('');

  const [loading, setLoading] = useState(true);
  const [success, setSuccess] = useState('');

  const fetchWorkflows = async () => {
    try {
      const data = await listWorkflows();
      setWorkflows(data);
      
      const agentList = await listAgents();
      setAgents(agentList);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !firstAgentId || !secondAgentId) {
      alert("Name and both agents are required to link a pipeline DAG.");
      return;
    }

    // Build standard 2-node DAG definition JSON
    const definition = {
      nodes: [
        { id: "node_1", type: "agent", agent_id: parseInt(firstAgentId as string), input_template: "{input}" },
        { id: "node_2", type: "agent", agent_id: parseInt(secondAgentId as string), input_template: "Review and format details from node_1 output: {node_1.output}" }
      ],
      edges: [
        { source: "node_1", target: "node_2" }
      ]
    };

    try {
      await createWorkflow({
        name,
        description,
        definition_json: definition
      });
      setSuccess("Workflow pipeline DAG registered successfully.");
      setName('');
      setDescription('');
      setFirstAgentId('');
      setSecondAgentId('');
      fetchWorkflows();
      setTimeout(() => setSuccess(''), 4000);
    } catch (e) {
      alert("Failed to compile workflow DAG.");
    }
  };

  const handleRun = async (wfId: number) => {
    if (!query) {
      alert("Please enter a query instruction to run the workflow.");
      return;
    }
    try {
      await runWorkflow(wfId, query);
      setSuccess("Workflow scheduled in background queue.");
      setQuery('');
      setTimeout(() => setSuccess(''), 4000);
    } catch (e) {
      alert("Failed to queue workflow run.");
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight">Multi-Agent Workflows</h2>
        <p className="text-slate-400 text-sm mt-1">Connect multiple AI agents together in Directed Acyclic Graph (DAG) pipelines.</p>
      </div>

      {success && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-semibold flex items-center gap-2">
          <CheckCircle size={16} /> {success}
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Left Column: Registered workflows list */}
        <div className="lg:col-span-2 space-y-6">
          <h3 className="font-bold text-lg flex items-center gap-2 border-b border-slate-900 pb-3">
            <Workflow size={18} className="text-emerald-400" /> Pipeline Definitions
          </h3>

          <div className="space-y-4">
            {workflows.map((wf) => (
              <div key={wf.id} className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 space-y-4 hover:border-slate-800 transition-colors">
                <div className="flex justify-between items-start border-b border-slate-900/60 pb-3">
                  <div>
                    <h4 className="font-bold text-base">{wf.name}</h4>
                    <p className="text-xs text-slate-500 mt-1">{wf.description || 'No description.'}</p>
                  </div>
                  <span className="text-[10px] bg-slate-900 border border-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
                    DAG Active
                  </span>
                </div>

                {/* Graph visual representation */}
                <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-900/80 flex items-center justify-center gap-4 text-xs font-semibold">
                  <span className="px-3 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                    {agents.find(a => a.id === wf.definition_json.nodes[0].agent_id)?.name || 'Agent 1'}
                  </span>
                  <span className="text-slate-600">→</span>
                  <span className="px-3 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                    {agents.find(a => a.id === wf.definition_json.nodes[1].agent_id)?.name || 'Agent 2'}
                  </span>
                </div>

                {/* Execution inputs */}
                <div className="flex items-center gap-3 pt-2">
                  <input 
                    type="text" 
                    placeholder="Enter input query for workflow (e.g. 'Write a draft')"
                    value={selectedWorkflowId === wf.id ? query : ''} 
                    onChange={(e) => {
                      setSelectedWorkflowId(wf.id);
                      setQuery(e.target.value);
                    }}
                    className="flex-1 bg-slate-900 border border-slate-800 rounded px-3 py-2 text-xs focus:outline-none focus:border-emerald-500"
                  />
                  <button 
                    onClick={() => handleRun(wf.id)}
                    className="px-4 py-2 rounded bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-colors"
                  >
                    <Play size={12} fill="currentColor" /> Run DAG
                  </button>
                </div>
              </div>
            ))}

            {workflows.length === 0 && !loading && (
              <div className="text-center py-16 border border-dashed border-slate-900 rounded-xl space-y-2">
                <Layers size={32} className="text-slate-700 mx-auto" />
                <p className="text-sm text-slate-500">No multi-agent workflow DAGs defined yet.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Create Workflow form */}
        <div className="space-y-6">
          <h3 className="font-bold text-lg flex items-center gap-2 border-b border-slate-900 pb-3">
            <Plus size={18} className="text-emerald-400" /> Define 2-Agent Pipeline
          </h3>

          <form onSubmit={handleCreateWorkflow} className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Workflow Name</label>
              <input 
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Document Summary Flow"
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Description</label>
              <textarea 
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Explain the purpose of this flow..."
                rows={2}
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">First Node (Source Agent)</label>
              <select 
                value={firstAgentId}
                onChange={(e) => setFirstAgentId(e.target.value ? parseInt(e.target.value) : '')}
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
              >
                <option value="">Select first agent</option>
                {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Second Node (Target Agent)</label>
              <select 
                value={secondAgentId}
                onChange={(e) => setSecondAgentId(e.target.value ? parseInt(e.target.value) : '')}
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
              >
                <option value="">Select second agent</option>
                {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>

            <button 
              type="submit"
              className="w-full py-2.5 mt-2 rounded bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
            >
              <Plus size={14} /> Register Pipeline DAG
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
