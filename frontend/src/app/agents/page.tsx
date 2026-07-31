'use client';

import React, { useEffect, useState } from 'react';
import { listAgents, deleteAgent, reorderAgents } from '../../lib/api';
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
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, rectSortingStrategy } from '@dnd-kit/sortable';
import { SortableAgentCard } from './SortableAgentCard';

export default function AgentsListPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<any>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

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

  const handleDragEnd = async (event: any) => {
    const { active, over } = event;

    if (active.id !== over?.id) {
      setAgents((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);
        
        const newItems = arrayMove(items, oldIndex, newIndex);
        
        // Update order_index
        const reordered = newItems.map((item, idx) => ({
          ...item,
          order_index: idx
        }));
        
        // Save to backend asynchronously
        reorderAgents(reordered.map(r => ({ id: r.id, order_index: r.order_index })))
          .catch(err => console.error("Failed to reorder", err));

        return reordered;
      });
    }
  };

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
      <DndContext 
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <div className="grid md:grid-cols-3 gap-6">
          <SortableContext 
            items={filteredAgents.map(a => a.id)}
            strategy={rectSortingStrategy}
          >
            {filteredAgents.map((agent) => (
              <SortableAgentCard 
                key={agent.id} 
                agent={agent} 
                setSelectedAgent={setSelectedAgent}
                handleDelete={handleDelete}
              />
            ))}
          </SortableContext>

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
      </DndContext>

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
                <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">How to Use (Instructions)</h4>
                <div className="space-y-3">
                  {selectedAgent.how_to_use ? (
                    <p className="text-sm text-slate-400 leading-relaxed bg-slate-950/30 p-4 rounded-lg border border-slate-800 whitespace-pre-wrap">
                      {selectedAgent.how_to_use}
                    </p>
                  ) : (
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
                  )}
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
