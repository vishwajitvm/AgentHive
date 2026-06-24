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
  AlertCircle,
  X,
  BookOpen
} from 'lucide-react';
import Link from 'next/link';

export default function AgentsListPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<any>(null);

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

  const filteredAgents = agents.filter(a => 
    a.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    a.agent_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (a.description && a.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight">AI Agent Registry</h2>
          <p className="text-slate-400 text-sm mt-1">Configure individual prompt targets, allowed tool profiles, and model bindings.</p>
        </div>
        
        <div className="flex gap-4 w-full md:w-auto">
          <input 
            type="text" 
            placeholder="Search agents..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full md:w-64 bg-slate-900 border border-slate-800 text-slate-200 text-sm rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
          />
          <Link href="/agents/create" className="whitespace-nowrap px-4 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm flex items-center gap-2 transition-all shadow-lg shadow-emerald-500/10">
            <Plus size={16} /> Create New Agent
          </Link>
        </div>
      </div>

      {message && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium">
          {message}
        </div>
      )}

      {/* Grid of Agents */}
      <div className="grid md:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => (
          <div key={agent.id} className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 flex flex-col justify-between hover:border-slate-800 transition-all duration-300">
            <div className="space-y-4">
              {/* Header card */}
              <div className="flex justify-between items-start">
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-emerald-400">
                  <Bot size={24} />
                </div>
                
                <div className="flex flex-col items-end gap-1">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                    agent.status === 'active' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}>
                    {agent.status.toUpperCase()}
                  </span>
                  {agent.model_policy_id ? (
                    <span className="text-[9px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-1.5 py-0.5 rounded">Custom Model</span>
                  ) : (
                    <span className="text-[9px] bg-slate-800 text-slate-400 border border-slate-700 px-1.5 py-0.5 rounded">Default Router</span>
                  )}
                </div>
              </div>

              {/* Title & Description */}
              <div>
                <h3 className="font-bold text-lg leading-tight">{agent.name}</h3>
                <p className="text-[10px] text-slate-400 font-bold mt-1 uppercase tracking-widest">{agent.agent_type.replace('_', ' ')}</p>
                <p className="text-xs text-slate-400 mt-3 line-clamp-3 leading-relaxed">{agent.description || 'No description provided.'}</p>
              </div>

              {/* Tools enabled */}
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Permitted Tools ({agent.tools_enabled.length})</p>
                <div className="flex flex-wrap gap-1.5 mt-2 max-h-16 overflow-y-auto pr-1 custom-scrollbar">
                  {agent.tools_enabled.map((t: string) => (
                    <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800/80">
                      {t.replace('_', ' ')}
                    </span>
                  ))}
                  {agent.tools_enabled.length === 0 && (
                    <span className="text-[10px] text-slate-500 italic">No tools authorized.</span>
                  )}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between border-t border-slate-900/60 pt-4 mt-6">
              <div className="flex gap-2">
                <button 
                  onClick={() => setSelectedAgent(agent)}
                  className="px-3 py-1.5 rounded bg-sky-500/10 border border-sky-500/20 hover:bg-sky-500/20 text-sky-400 font-bold text-xs flex items-center gap-1.5 transition-all"
                >
                  <BookOpen size={12} fill="currentColor" /> How to Use
                </button>
                <Link href={`/agents/${agent.id}`} className="px-3.5 py-1.5 rounded bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20 text-emerald-400 font-bold text-xs flex items-center gap-1.5 transition-all">
                  <Play size={12} fill="currentColor" /> Chat & Run
                </Link>
              </div>
              
              <div className="flex items-center gap-2">
                <Link href={`/agents/edit/${agent.id}`} className="p-1.5 rounded hover:bg-slate-800 text-slate-500 hover:text-slate-300 transition-colors">
                  <Settings size={16} />
                </Link>
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

        {filteredAgents.length === 0 && !loading && (
          <div className="col-span-full text-center py-20 border border-dashed border-slate-900 rounded-2xl space-y-4">
            <Bot size={48} className="text-slate-700 mx-auto" />
            <div className="space-y-1">
              <p className="font-bold text-slate-300">No agents found</p>
              <p className="text-sm text-slate-500">Try adjusting your search or create a new agent.</p>
            </div>
          </div>
        )}
      </div>

      {/* How to Use Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-5 border-b border-slate-800 bg-slate-900/50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-800 border border-slate-700 rounded text-sky-400">
                  <Bot size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-slate-200">{selectedAgent.name}</h3>
                  <span className="text-[10px] font-bold tracking-widest text-emerald-400 uppercase bg-emerald-500/10 px-2 py-0.5 rounded">Type: Agent</span>
                </div>
              </div>
              <button onClick={() => setSelectedAgent(null)} className="p-2 text-slate-500 hover:text-slate-300 hover:bg-slate-800 rounded-lg transition-colors">
                <X size={20} />
              </button>
            </div>
            
            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6">
              {/* Description */}
              <div className="space-y-2">
                <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">About This Agent</h4>
                <p className="text-sm text-slate-400 leading-relaxed bg-slate-950/50 p-4 rounded-lg border border-slate-800">
                  {selectedAgent.description || 'No description provided.'}
                </p>
              </div>

              {/* Step by Step */}
              <div className="space-y-3">
                <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">How to Use (Step by Step)</h4>
                <div className="space-y-3">
                  <div className="flex gap-3 items-start bg-slate-950/30 p-3 rounded-lg border border-slate-800/50">
                    <div className="bg-slate-800 text-slate-300 w-6 h-6 rounded flex items-center justify-center font-bold text-xs shrink-0">1</div>
                    <div>
                      <p className="text-sm text-slate-300 font-semibold">Open the Agent Console</p>
                      <p className="text-xs text-slate-500 mt-1">Click the "Chat & Run" button on the agent's card to enter their dedicated workspace console.</p>
                    </div>
                  </div>
                  <div className="flex gap-3 items-start bg-slate-950/30 p-3 rounded-lg border border-slate-800/50">
                    <div className="bg-slate-800 text-slate-300 w-6 h-6 rounded flex items-center justify-center font-bold text-xs shrink-0">2</div>
                    <div>
                      <p className="text-sm text-slate-300 font-semibold">Provide an Instruction</p>
                      <p className="text-xs text-slate-500 mt-1">Type your goal into the input box. The agent is initialized with a specific <span className="text-emerald-400 font-mono">system_prompt</span> so you don't need to over-explain context.</p>
                    </div>
                  </div>
                  <div className="flex gap-3 items-start bg-slate-950/30 p-3 rounded-lg border border-slate-800/50">
                    <div className="bg-slate-800 text-slate-300 w-6 h-6 rounded flex items-center justify-center font-bold text-xs shrink-0">3</div>
                    <div>
                      <p className="text-sm text-slate-300 font-semibold">Monitor the Reasoning Trace</p>
                      <p className="text-xs text-slate-500 mt-1">Watch the right-side panel to see the agent think, call its authorized tools, and arrive at a final answer within its {selectedAgent.max_steps}-step limit.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Example */}
              <div className="space-y-2">
                <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Example Prompt</h4>
                <div className="bg-slate-950 rounded-lg border border-slate-800 p-4">
                  <p className="text-sm text-emerald-400 italic font-medium">
                    "Execute your task using the permitted tools ({selectedAgent.tools_enabled.length > 0 ? selectedAgent.tools_enabled.join(', ') : 'None'}) to gather data and generate a final report."
                  </p>
                </div>
              </div>
            </div>
            
            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex justify-end">
              <button 
                onClick={() => setSelectedAgent(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-bold transition-colors"
              >
                Close Guide
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
