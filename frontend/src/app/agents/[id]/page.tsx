'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { getAgent, runAgent, getRunSteps, uploadToWorkspace } from '../../../lib/api';
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
  Cpu,
  CheckCircle,
  UploadCloud,
  FileText
} from 'lucide-react';
import Link from 'next/link';
import TraceDiagram from '../../../components/TraceDiagram';

export default function AgentConsolePage() {
  const { id } = useParams();
  const agentId = parseInt(id as string);

  const [agent, setAgent] = useState<any>(null);
  const [query, setQuery] = useState('');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [trace, setTrace] = useState<any>({ steps: [], tool_calls: [] });
  const [error, setError] = useState('');
  
  // Context variables
  const [sessionContext, setSessionContext] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const fetchAgentInfo = async () => {
    try {
      const data = await getAgent(agentId);
      setAgent(data);
    } catch (e) {
      console.error(e);
      setError("Failed to load agent configuration.");
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    try {
      setUploading(true);
      setUploadStatus(null);
      await uploadToWorkspace(file);
      setUploadStatus(`Uploaded: ${file.name}`);
    } catch (err: any) {
      setUploadStatus(`Error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() && !query) return;

    setRunning(true);
    setResult(null);
    setTrace({ steps: [], tool_calls: [] });
    setError('');

    try {
      // Inject session context if present
      const finalQuery = sessionContext.trim() 
        ? `[SYSTEM SECRETS/CONTEXT FOR THIS SESSION]:\n${sessionContext}\n\n[USER INSTRUCTION]:\n${query}` 
        : query;

      const data = await runAgent(agentId, finalQuery, false);
      setResult(data);
      
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

          {/* Context & File Upload */}
          <div className="rounded-xl border border-slate-900 bg-slate-950/20 p-6 space-y-5">
            <h3 className="font-bold text-sm flex items-center gap-2 text-slate-300 border-b border-slate-900 pb-2">
              <Shield size={16} className="text-sky-400" /> Workspace Context & Secrets
            </h3>
            
            {/* File Upload */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 block">Upload Document to Workspace</label>
              <div className="flex items-center gap-3">
                <label className="cursor-pointer bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                  <UploadCloud size={14} /> {uploading ? 'Uploading...' : 'Choose File'}
                  <input type="file" className="hidden" onChange={handleFileUpload} disabled={uploading} />
                </label>
                {uploadStatus && (
                  <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                    <FileText size={10} /> {uploadStatus}
                  </span>
                )}
              </div>
            </div>

            {/* Session Secrets */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 block">Temporary Session Secrets (e.g. Passwords, API Keys)</label>
              <textarea 
                value={sessionContext}
                onChange={(e) => setSessionContext(e.target.value)}
                placeholder="Paste account credentials or context here. This is securely injected into the agent's memory for this run only."
                rows={2}
                className="w-full bg-slate-900 border border-slate-800 rounded p-2 text-xs font-mono focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 text-slate-300"
              />
            </div>
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
                {trace.steps && trace.steps.length > 0 && (
                  <TraceDiagram steps={trace.steps} />
                )}

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
