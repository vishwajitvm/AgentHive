'use client';

import React, { useEffect, useState } from 'react';
import { listAgents, deleteAgent } from '../../lib/api';
import { 
  Bot, 
  Trash2, 
  Settings, 
  Plus,
  Play, 
  CheckCircle, 
  AlertCircle 
} from 'lucide-react';
import Link from 'next/link';

export default function AgentsListPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  const fetchAgents = async () => {
    try {
      const data = await listAgents();
      setAgents(data);
    } catch (e) {
      console.error("Failed to load agents list", e);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this agent? This cannot be undone.")) return;
    try {
      await deleteAgent(id);
      setMessage("Agent deleted successfully.");
      fetchAgents();
    } catch (e) {
      console.error("Failed to delete agent", e);
      alert("Error deleting agent.");
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight">AI Agent Registry</h2>
          <p className="text-slate-400 text-sm mt-1">Configure individual prompt targets, allowed tool profiles, and model bindings.</p>
        </div>
        
        <Link href="/agents/create" className="px-4 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm flex items-center gap-2 transition-all shadow-lg shadow-emerald-500/10">
          <Plus size={16} /> Create New Agent
        </Link>
      </div>

      {message && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium">
          {message}
        </div>
      )}

      {/* Grid of Agents */}
      <div className="grid md:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <div key={agent.id} className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 flex flex-col justify-between hover:border-slate-800 transition-all duration-300">
            <div className="space-y-4">
              {/* Header card */}
              <div className="flex justify-between items-start">
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-emerald-400">
                  <Bot size={24} />
                </div>
                
                <span className={`text-xs px-2 py-0.5 rounded font-semibold ${
                  agent.status === 'active' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                }`}>
                  {agent.status}
                </span>
              </div>

              {/* Title & Description */}
              <div>
                <h3 className="font-bold text-lg leading-tight">{agent.name}</h3>
                <p className="text-xs text-slate-400 font-semibold mt-1 uppercase tracking-wider">{agent.agent_type.replace('_', ' ')}</p>
                <p className="text-sm text-slate-400 mt-3 line-clamp-3">{agent.description || 'No description provided.'}</p>
              </div>

              {/* Tools enabled */}
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Permitted Tools</p>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {agent.tools_enabled.map((t: string) => (
                    <span key={t} className="text-xs px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800/80">
                      {t.replace('_', ' ')}
                    </span>
                  ))}
                  {agent.tools_enabled.length === 0 && (
                    <span className="text-xs text-slate-500 italic">No tools authorized.</span>
                  )}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between border-t border-slate-900/60 pt-4 mt-6">
              <Link href={`/agents/${agent.id}`} className="px-3.5 py-1.5 rounded bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20 text-emerald-400 font-bold text-xs flex items-center gap-1.5 transition-all">
                <Play size={12} fill="currentColor" /> Chat & Run
              </Link>
              
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => handleDelete(agent.id)}
                  className="p-1.5 rounded hover:bg-rose-500/10 text-slate-500 hover:text-rose-400 transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          </div>
        ))}

        {agents.length === 0 && !loading && (
          <div className="col-span-full text-center py-20 border border-dashed border-slate-900 rounded-2xl space-y-4">
            <Bot size={48} className="text-slate-700 mx-auto" />
            <div className="space-y-1">
              <p className="font-bold text-slate-300">No agents found</p>
              <p className="text-sm text-slate-500">Get started by building your first AI agent workspace.</p>
            </div>
            <Link href="/agents/create" className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm inline-flex items-center gap-2 transition-all">
              <Plus size={16} /> Create Agent
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
