'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { getAgent, runAgent, getRunSteps } from '../../../lib/api';
import { 
  Bot, 
  Play, 
  Terminal, 
  Clock, 
  HelpCircle,
  AlertTriangle,
  ChevronRight,
  Settings,
  Shield,
  Activity,
  Cpu
} from 'lucide-react';
import Link from 'next/link';

export default function AgentConsolePage() {
  const { id } = useParams();
  const agentId = parseInt(id as string);

  const [agent, setAgent] = useState<any>(null);
  const [query, setQuery] = useState('');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [trace, setTrace] = useState<any>({ steps: [], tool_calls: [] });
  const [error, setError] = useState('');

  const fetchAgentInfo = async () => {
    try {
      const data = await getAgent(agentId);
      setAgent(data);
    } catch (e) {
      console.error(e);
      setError("Failed to load agent configuration.");
    }
  };

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.strip && !query) return;

    setRunning(true);
    setResult(null);
    setTrace({ steps: [], tool_calls: [] });
    setError('');

    try {
      // Trigger synchronous execution for immediate output trace
      const data = await runAgent(agentId, query, false);
      setResult(data);
      
      // Fetch trace steps
      if (data.agent_run_id) {
        const traceData = await getRunSteps(data.agent_run_id);
        setTrace(traceData);
      }
    } catch (err: any) {
      setError(err.message || "Agent execution failed.");
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    fetchAgentInfo();
  }, [agentId]);

  if (!agent && !error) {
    return <div className="text-center py-20 text-slate-500 font-semibold animate-pulse">Loading Agent Console...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex justify-between items-center border-b border-slate-900 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-emerald-400">
            <Bot size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold">{agent?.name}</h2>
            <p className="text-slate-400 text-xs mt-0.5 capitalize">{agent?.agent_type.replace('_', ' ')} Registry Profile</p>
          </div>
        </div>

        <Link href="/agents" className="text-xs font-semibold px-3 py-1.5 rounded bg-slate-900 border border-slate-800 hover:text-slate-200 transition-colors">
          Back to list
        </Link>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm font-semibold">
          {error}
        </div>
      )}

      {/* Main console layout */}
      <div className="grid lg:grid-cols-5 gap-8">
        {/* Left Side: Input console */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 space-y-4">
            <h3 className="font-bold text-sm flex items-center gap-2 text-slate-300">
              <Terminal size={16} /> Execute Agent Instruction
            </h3>
            
            <form onSubmit={handleRun} className="space-y-4">
              <textarea 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Instruct the agent (e.g. 'Search for recent facts about FastAPI and summarize them in a markdown file called fastapi.md')"
                rows={4}
                disabled={running}
                className="w-full bg-slate-900 border border-slate-800 rounded p-3 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              />

              <button 
                type="submit" 
                disabled={running || !query}
                className="w-full py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-900 disabled:text-slate-600 text-slate-950 font-bold text-sm flex items-center justify-center gap-2 transition-all"
              >
                <Play size={14} fill="currentColor" /> {running ? 'Running Agent Loop...' : 'Execute Loop'}
              </button>
            </form>
          </div>

          {/* Configuration profile snapshot */}
          <div className="rounded-xl border border-slate-900 bg-slate-950/20 p-6 space-y-4 text-xs">
            <h3 className="font-bold text-sm text-slate-300 border-b border-slate-900 pb-2">Active Parameters</h3>
            <div className="space-y-2.5">
              <div className="flex justify-between">
                <span className="text-slate-500">Allowed Tool Bindings</span>
                <span className="font-semibold text-slate-300">{agent?.tools_enabled.join(', ') || 'None'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Loop Steps Limit</span>
                <span className="font-semibold text-slate-300">{agent?.max_steps} iterations</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Execution Timeout</span>
                <span className="font-semibold text-slate-300">{agent?.timeout_seconds} seconds</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">pgvector Memory</span>
                <span className="font-semibold text-slate-300">{agent?.memory_enabled ? 'Enabled' : 'Disabled'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Observability trace timeline */}
        <div className="lg:col-span-3 space-y-6">
          <div className="rounded-xl border border-slate-900 bg-slate-950/30 p-6 min-h-[400px] flex flex-col justify-between">
            {/* Trace logs header */}
            <div className="space-y-6 flex-1">
              <div className="flex justify-between items-center border-b border-slate-900 pb-3">
                <h3 className="font-bold text-base flex items-center gap-2 text-slate-300">
                  <Activity size={18} className="text-emerald-400" /> Observability Trace logs
                </h3>
                {running && (
                  <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5 animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" /> Analyzing steps...
                  </span>
                )}
              </div>

              {/* Steps display */}
              <div className="space-y-6 max-h-[500px] overflow-y-auto pr-2">
                {trace.steps.map((step: any) => (
                  <div key={step.id} className="space-y-2 border-l-2 border-slate-800 pl-4 relative">
                    <span className="absolute -left-1.5 top-1 w-3.5 h-3.5 rounded-full bg-slate-900 border-2 border-slate-700 flex items-center justify-center text-[8px] font-bold text-slate-400">
                      {step.step_number}
                    </span>
                    
                    <div className="flex justify-between items-center">
                      <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{step.action_type}</p>
                      <span className="text-[10px] text-slate-600">
                        {new Date(step.created_at).toLocaleTimeString()}
                      </span>
                    </div>

                    <pre className="text-xs font-mono text-slate-300 whitespace-pre-wrap bg-slate-900/40 p-3 rounded border border-slate-900/50 leading-relaxed">
                      {step.content}
                    </pre>
                  </div>
                ))}

                {/* Final response card */}
                {result && (
                  <div className="p-5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 space-y-3">
                    <div className="flex justify-between items-center border-b border-emerald-500/10 pb-2">
                      <h4 className="text-sm font-bold text-emerald-400 flex items-center gap-1.5">
                        <CheckCircle size={16} /> Final Answer Resolved
                      </h4>
                      <span className="text-[10px] text-slate-400 flex items-center gap-1">
                        <Clock size={10} /> {result.elapsed_seconds}s elapsed
                      </span>
                    </div>
                    <p className="text-sm text-slate-200 leading-relaxed font-medium whitespace-pre-wrap">{result.output}</p>
                  </div>
                )}

                {!running && trace.steps.length === 0 && !result && (
                  <div className="text-center py-20 text-slate-600 space-y-2">
                    <Cpu size={32} className="mx-auto text-slate-800" />
                    <p className="text-sm">Submit an instruction to start the reasoning agent loop.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
