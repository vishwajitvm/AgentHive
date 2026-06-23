'use client';

import React from 'react';
import { 
  FileText, 
  Terminal, 
  Search, 
  Cloud, 
  Code2, 
  ChevronRight,
  ShieldCheck
} from 'lucide-react';

export default function ToolsDirectoryPage() {
  const tools = [
    {
      slug: 'file_tool',
      name: 'File System Tool',
      icon: FileText,
      desc: 'Enables the agent to read, write, or list text files in its dedicated local directory workspace.',
      args: [
        { name: 'action', type: 'string', desc: "'read', 'write', or 'list' (required)" },
        { name: 'filename', type: 'string', desc: "Target file name in the workspace (required for read/write)" },
        { name: 'content', type: 'string', desc: "Text contents to write to the file (required for write)" }
      ]
    },
    {
      slug: 'pdf_tool',
      name: 'PDF Text Extractor',
      icon: Terminal,
      desc: 'Extracts plain text chunks from PDF documents loaded in the workspace.',
      args: [
        { name: 'filename', type: 'string', desc: "Target PDF file name (required)" }
      ]
    },
    {
      slug: 'search_tool',
      name: 'Web Search Engine',
      icon: Search,
      desc: 'Retrieves summaries, snippets, and page contents for web queries. Falls back to a mock local registry for common terminology testing.',
      args: [
        { name: 'query', type: 'string', desc: "Search terms or question (required)" }
      ]
    },
    {
      slug: 'storage_tool',
      name: 'MinIO Cloud Storage',
      icon: Cloud,
      desc: 'Allows the agent to upload generated markdown reports or download assets from an S3-compatible MinIO bucket.',
      args: [
        { name: 'action', type: 'string', desc: "'upload' or 'download' (required)" },
        { name: 'object_name', type: 'string', desc: "S3 key under which the asset is catalogued (required)" },
        { name: 'content', type: 'string', desc: "Plaintext file contents to upload (required for upload)" }
      ]
    },
    {
      slug: 'code_tool',
      name: 'Code Interpreter',
      icon: Code2,
      desc: 'Evaluates simple Python calculations and prints outputs under a restricted execution sandbox namespace.',
      args: [
        { name: 'expression', type: 'string', desc: "Mathematical formula or Python statement (required)" }
      ]
    }
  ];

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight">Authorized Tools Catalog</h2>
        <p className="text-slate-400 text-sm mt-1">Review operational scopes and JSON arguments schemas for all agent-accessible tool classes.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {tools.map((tool) => {
          const Icon = tool.icon;
          return (
            <div key={tool.slug} className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 space-y-4 hover:border-slate-800 transition-colors">
              <div className="flex items-center justify-between border-b border-slate-900 pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-900 border border-slate-800 rounded text-emerald-400">
                    <Icon size={20} />
                  </div>
                  <div>
                    <h3 className="font-bold text-base">{tool.name}</h3>
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">{tool.slug}</span>
                  </div>
                </div>
                
                <span className="text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded flex items-center gap-1 font-bold">
                  <ShieldCheck size={10} /> Authorized
                </span>
              </div>

              <p className="text-sm text-slate-400 leading-relaxed">{tool.desc}</p>

              {/* Arguments schema */}
              <div className="space-y-2 border-t border-slate-900/60 pt-3">
                <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Arguments Schema</p>
                <div className="space-y-1.5 mt-2">
                  {tool.args.map(arg => (
                    <div key={arg.name} className="text-xs flex gap-2">
                      <span className="font-mono text-slate-300 font-bold">{arg.name}:</span>
                      <span className="text-slate-500 font-semibold">({arg.type})</span>
                      <span className="text-slate-400 flex-1">{arg.desc}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
