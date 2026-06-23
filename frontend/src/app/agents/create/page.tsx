'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createAgent } from '../../../lib/api';
import { Bot, Save, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function CreateAgentPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    name: '',
    slug: '',
    description: '',
    agent_type: 'personal_assistant',
    prompt_content: '',
    tools_enabled: [] as string[],
    memory_enabled: true,
    max_steps: 10,
    timeout_seconds: 120
  });

  const toolOptions = [
    { slug: 'file_tool', name: 'File System Tool', desc: 'Allows writing, reading and listing files locally.' },
    { slug: 'pdf_tool', name: 'PDF Text Extractor', desc: 'Extracts plain text contents from PDF files.' },
    { slug: 'search_tool', name: 'Web Search Engine', desc: 'Searches the web for articles and snippets.' },
    { slug: 'storage_tool', name: 'MinIO Cloud Storage', desc: 'Uploads or downloads objects from S3 bucket.' },
    { slug: 'code_tool', name: 'Code Interpreter', desc: 'Safe evaluation of simple Python arithmetic and blocks.' },
  ];

  const handleToolToggle = (slug: string) => {
    setForm(prev => {
      const exists = prev.tools_enabled.includes(slug);
      return {
        ...prev,
        tools_enabled: exists 
          ? prev.tools_enabled.filter(t => t !== slug)
          : [...prev.tools_enabled, slug]
      };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.slug || !form.prompt_content) {
      setError('Please fill in Name, Slug, and System Prompt fields.');
      return;
    }
    
    setLoading(true);
    setError('');

    try {
      await createAgent(form);
      router.push('/agents');
    } catch (err: any) {
      setError(err.message || 'Failed to create agent.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back Link */}
      <Link href="/agents" className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-slate-200 transition-colors uppercase tracking-wider">
        <ArrowLeft size={14} /> Back to registry
      </Link>

      {/* Header */}
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight">Create AI Agent Profile</h2>
        <p className="text-slate-400 text-sm mt-1">Configure reasoning prompts and security execution parameters.</p>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm font-semibold">
          {error}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="grid md:grid-cols-3 gap-8">
        {/* Left column settings */}
        <div className="md:col-span-2 space-y-6">
          {/* Metadata */}
          <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 space-y-4">
            <h3 className="font-bold text-base border-b border-slate-900 pb-3">Agent Metadata</h3>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Name</label>
                <input 
                  type="text" 
                  value={form.name} 
                  onChange={(e) => setForm({...form, name: e.target.value})}
                  placeholder="e.g. Code Helper Agent"
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Unique Slug</label>
                <input 
                  type="text" 
                  value={form.slug} 
                  onChange={(e) => setForm({...form, slug: e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, '')})}
                  placeholder="e.g. code_helper"
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Description</label>
              <textarea 
                value={form.description} 
                onChange={(e) => setForm({...form, description: e.target.value})}
                placeholder="Brief summary explaining what this agent will do..."
                rows={2}
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>
            
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Agent Type</label>
              <select 
                value={form.agent_type}
                onChange={(e) => setForm({...form, agent_type: e.target.value})}
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
              >
                <option value="personal_assistant">Personal Assistant</option>
                <option value="task_agent">Task Agent</option>
                <option value="pdf_agent">PDF Document Agent</option>
                <option value="research_agent">Research Analyst Agent</option>
                <option value="developer_agent">Developer Agent</option>
              </select>
            </div>
          </div>

          {/* System Prompt */}
          <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 space-y-4">
            <h3 className="font-bold text-base border-b border-slate-900 pb-3">System Prompt Instructions</h3>
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">System Prompt (TOON format optimized)</label>
              <textarea 
                value={form.prompt_content} 
                onChange={(e) => setForm({...form, prompt_content: e.target.value})}
                placeholder="Instruct the agent on its role, constraints, and target outputs..."
                rows={6}
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>
        </div>

        {/* Right column settings */}
        <div className="space-y-6">
          {/* Tools permissions */}
          <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 space-y-4">
            <h3 className="font-bold text-base border-b border-slate-900 pb-3">Allowed Tools</h3>
            <div className="space-y-4">
              {toolOptions.map((tool) => {
                const checked = form.tools_enabled.includes(tool.slug);
                return (
                  <label key={tool.slug} className="flex items-start gap-3 cursor-pointer group">
                    <input 
                      type="checkbox" 
                      checked={checked}
                      onChange={() => handleToolToggle(tool.slug)}
                      className="mt-1 rounded text-emerald-500 focus:ring-emerald-500"
                    />
                    <div className="space-y-0.5">
                      <span className="text-xs font-semibold group-hover:text-slate-100 transition-colors">{tool.name}</span>
                      <p className="text-[11px] text-slate-500 leading-tight">{tool.desc}</p>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Parameters */}
          <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 space-y-4">
            <h3 className="font-bold text-base border-b border-slate-900 pb-3">Loop Thresholds</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Max Reasoning Steps</label>
                <input 
                  type="number" 
                  value={form.max_steps} 
                  onChange={(e) => setForm({...form, max_steps: parseInt(e.target.value) || 5})}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Timeout (seconds)</label>
                <input 
                  type="number" 
                  value={form.timeout_seconds} 
                  onChange={(e) => setForm({...form, timeout_seconds: parseInt(e.target.value) || 60})}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>
            
            <label className="flex items-center gap-3 cursor-pointer mt-4">
              <input 
                type="checkbox"
                checked={form.memory_enabled}
                onChange={(e) => setForm({...form, memory_enabled: e.target.checked})}
                className="rounded text-emerald-500 focus:ring-emerald-500"
              />
              <span className="text-xs font-semibold">Enable pgvector Memory</span>
            </label>
          </div>

          {/* Submit */}
          <button 
            type="submit" 
            disabled={loading}
            className="w-full py-3 rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 disabled:text-slate-600 text-slate-950 font-bold text-sm flex items-center justify-center gap-2 transition-all shadow-lg shadow-emerald-500/10"
          >
            <Save size={16} /> {loading ? 'Saving Agent...' : 'Save Agent'}
          </button>
        </div>
      </form>
    </div>
  );
}
