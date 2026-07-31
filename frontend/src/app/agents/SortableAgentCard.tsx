import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Bot, Trash2, Settings, Play, BookOpen, GripVertical } from 'lucide-react';
import Link from 'next/link';

export function SortableAgentCard({ agent, setSelectedAgent, handleDelete }: any) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: agent.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 10 : 1,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div 
      ref={setNodeRef} 
      style={style} 
      className={`rounded-xl border ${isDragging ? 'border-emerald-500 shadow-xl shadow-emerald-500/20' : 'border-slate-900'} bg-slate-950/40 flex flex-col justify-between hover:border-slate-800 transition-colors duration-300 relative group`}
    >
      <div 
        {...attributes} 
        {...listeners}
        className="absolute top-2 left-2 p-1.5 cursor-grab active:cursor-grabbing text-slate-600 hover:text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity z-10"
      >
        <GripVertical size={16} />
      </div>

      <div className="p-6 space-y-4 h-full flex flex-col">
        {/* Header card */}
        <div className="flex justify-between items-start pl-6">
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
        <div className="flex-grow">
          <h3 className="font-bold text-lg leading-tight">{agent.name}</h3>
          <p className="text-[10px] text-slate-400 font-bold mt-1 uppercase tracking-widest">{agent.agent_type.replace('_', ' ')}</p>
          <p className="text-xs text-slate-400 mt-3 line-clamp-3 leading-relaxed">{agent.description || 'No description provided.'}</p>
        </div>

        {/* Tools enabled */}
        <div className="space-y-1 mt-4">
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Permitted Tools ({agent.tools_enabled?.length || 0})</p>
          <div className="flex flex-wrap gap-1.5 mt-2 max-h-16 overflow-y-auto pr-1 custom-scrollbar">
            {agent.tools_enabled?.map((t: string) => (
              <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800/80">
                {t.replace('_', ' ')}
              </span>
            ))}
            {(!agent.tools_enabled || agent.tools_enabled.length === 0) && (
              <span className="text-[10px] text-slate-500 italic">No tools authorized.</span>
            )}
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
    </div>
  );
}
