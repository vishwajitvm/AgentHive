import React from 'react';
import { Brain, Wrench, CheckCircle, Search, TerminalSquare, AlertTriangle, Cpu, ServerCrash } from 'lucide-react';

interface Step {
  id?: number;
  step_number: number;
  action_type: string;
  content: string;
  created_at: string;
}

interface TraceDiagramProps {
  steps: Step[];
}

export default function TraceDiagram({ steps }: TraceDiagramProps) {
  if (!steps || steps.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-lg">
        No execution steps recorded yet.
      </div>
    );
  }

  const getStepVisuals = (actionType: string) => {
    const type = actionType.toLowerCase();
    if (type.includes('thought')) {
      return {
        icon: <Brain size={16} />,
        color: 'text-purple-400',
        bg: 'bg-purple-500/10',
        border: 'border-purple-500/20'
      };
    }
    if (type.includes('tool_call') || type.includes('tool')) {
      return {
        icon: <Wrench size={16} />,
        color: 'text-blue-400',
        bg: 'bg-blue-500/10',
        border: 'border-blue-500/20'
      };
    }
    if (type.includes('observation') || type.includes('search')) {
      return {
        icon: <Search size={16} />,
        color: 'text-amber-400',
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/20'
      };
    }
    if (type.includes('final_answer') || type.includes('final')) {
      return {
        icon: <CheckCircle size={16} />,
        color: 'text-emerald-400',
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/20'
      };
    }
    if (type.includes('error') && !type.includes('llm_error')) {
      return {
        icon: <AlertTriangle size={16} />,
        color: 'text-rose-400',
        bg: 'bg-rose-500/10',
        border: 'border-rose-500/20'
      };
    }
    if (type.includes('llm_call')) {
      return {
        icon: <Cpu size={16} />,
        color: 'text-sky-400',
        bg: 'bg-sky-500/10',
        border: 'border-sky-500/20'
      };
    }
    if (type.includes('llm_error') || type.includes('fallback')) {
      return {
        icon: <ServerCrash size={16} />,
        color: 'text-red-400',
        bg: 'bg-red-500/10',
        border: 'border-red-500/50'
      };
    }
    
    // Default system/unknown step
    return {
      icon: <TerminalSquare size={16} />,
      color: 'text-slate-400',
      bg: 'bg-slate-800/50',
      border: 'border-slate-700'
    };
  };

  return (
    <div className="space-y-0 relative py-2">
      {/* Central continuous vertical line */}
      <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-slate-800 z-0"></div>
      
      {steps.map((step, idx) => {
        const visuals = getStepVisuals(step.action_type);
        
        return (
          <div key={step.id || idx} className="relative z-10 flex gap-4 w-full group">
            {/* Timeline Column */}
            <div className="flex flex-col items-center min-w-[3rem] py-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 border-slate-900 shadow-xl ${visuals.bg} ${visuals.color}`}>
                {visuals.icon}
              </div>
            </div>

            {/* Content Column */}
            <div className="flex-1 pb-8">
              <div className={`p-4 rounded-xl border ${visuals.border} bg-slate-900/80 shadow-md backdrop-blur-sm transition-all group-hover:border-slate-600`}>
                <div className="flex justify-between items-center mb-3 border-b border-slate-800/50 pb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${visuals.bg} ${visuals.color}`}>
                      {step.action_type.replace('_', ' ')}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">Step {step.step_number}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(step.created_at).toLocaleTimeString()}
                  </span>
                </div>
                
                {/* Content formatting */}
                <div className="text-sm text-slate-300 font-mono whitespace-pre-wrap leading-relaxed overflow-x-auto max-h-[400px] overflow-y-auto">
                  {step.content}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
