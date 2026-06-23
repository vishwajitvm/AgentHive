'use client';

import React, { useEffect, useState } from 'react';
import { 
  Wrench,
  Search, 
  Terminal,
  ShieldCheck,
  ShieldAlert,
  Loader2,
  Box,
  X,
  BookOpen
} from 'lucide-react';

interface Tool {
  id: number;
  name: string;
  slug: string;
  description: string;
  category: string;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  is_enabled: boolean;
  requires_auth: boolean;
  required_env_keys: string[];
  safe_mock_mode: boolean;
}

import { listTools, runTool } from '../../lib/api';

export default function ToolsDirectoryPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  
  // Testing State
  const [testTool, setTestTool] = useState<Tool | null>(null);
  const [testPayload, setTestPayload] = useState<string>('');
  const [testResult, setTestResult] = useState<any>(null);
  const [testLoading, setTestLoading] = useState(false);
  const [testError, setTestError] = useState<string | null>(null);

  const handleTestTool = async () => {
    if (!testTool) return;
    try {
      setTestLoading(true);
      setTestError(null);
      setTestResult(null);
      
      let payload = {};
      if (testPayload.trim()) {
        payload = JSON.parse(testPayload);
      }
      
      const result = await runTool(testTool.slug, payload);
      setTestResult(result);
    } catch (err: any) {
      setTestError(err.message || 'Invalid JSON or execution error');
    } finally {
      setTestLoading(false);
    }
  };

  const openTestModal = (tool: Tool) => {
    setTestTool(tool);
    setTestPayload(JSON.stringify(tool.input_schema, null, 2));
    setTestResult(null);
    setTestError(null);
  };

  useEffect(() => {
    async function fetchTools() {
      try {
        const data = await listTools();
        setTools(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchTools();
  }, []);

  const filteredTools = tools.filter(t => 
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    t.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight">Tools Directory</h2>
          <p className="text-slate-400 text-sm mt-1">Review capabilities and JSON schemas for all registered agent tools.</p>
        </div>
        
        <div className="relative w-full md:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
          <input 
            type="text" 
            placeholder="Search tools..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 text-slate-200 text-sm rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-500 gap-3">
          <Loader2 className="animate-spin" size={24} />
          <span>Loading tools from registry...</span>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl flex items-center gap-3">
          <ShieldAlert size={20} />
          <p>Error loading tools: {error}</p>
        </div>
      ) : filteredTools.length === 0 ? (
        <div className="p-12 text-center text-slate-500 bg-slate-900/30 border border-slate-800/50 rounded-xl">
          <Box size={48} className="mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-bold text-slate-400 mb-1">No tools found</h3>
          <p className="text-sm">No tools matched your search query.</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredTools.map((tool) => (
            <div key={tool.slug} className="rounded-xl border border-slate-900 bg-slate-950/40 p-5 space-y-4 hover:border-slate-800 transition-colors flex flex-col">
              <div className="flex items-start justify-between border-b border-slate-900 pb-3 gap-4">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="p-2 bg-slate-900 border border-slate-800 rounded text-emerald-400 shrink-0">
                    <Wrench size={18} />
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-bold text-sm truncate">{tool.name}</h3>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">{tool.slug}</span>
                      <span className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded capitalize">{tool.category}</span>
                    </div>
                  </div>
                </div>
                
                {tool.is_enabled ? (
                  <span className="text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded flex items-center gap-1 font-bold shrink-0">
                    <ShieldCheck size={10} /> Active
                  </span>
                ) : (
                  <span className="text-[10px] text-red-400 bg-red-500/10 border border-red-500/20 px-1.5 py-0.5 rounded flex items-center gap-1 font-bold shrink-0">
                    <ShieldAlert size={10} /> Disabled
                  </span>
                )}
              </div>

              <p className="text-xs text-slate-400 leading-relaxed flex-1">{tool.description}</p>

              <div className="space-y-3 pt-2">
                <div className="flex flex-wrap gap-2 text-[10px] font-semibold">
                  {tool.safe_mock_mode && (
                    <span className="bg-blue-500/10 border border-blue-500/20 text-blue-400 px-2 py-1 rounded">Mock Mode</span>
                  )}
                  {tool.requires_auth && (
                    <span className="bg-amber-500/10 border border-amber-500/20 text-amber-400 px-2 py-1 rounded">Requires Auth</span>
                  )}
                </div>

                {tool.required_env_keys?.length > 0 && (
                  <div className="text-[10px]">
                    <span className="text-slate-500 font-bold block mb-1">Required ENV Keys:</span>
                    <div className="flex flex-wrap gap-1">
                      {tool.required_env_keys.map(key => (
                        <span key={key} className="bg-slate-900 border border-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-mono">{key}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-slate-900/60 flex justify-between items-center mt-auto">
                <div className="group relative cursor-help">
                  <span className="text-xs font-mono text-slate-500 border border-slate-800 bg-slate-900 px-2 py-1 rounded hover:text-slate-300">View Schema</span>
                  <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block w-64 bg-slate-900 border border-slate-800 p-3 rounded-lg shadow-xl z-10 text-[10px] font-mono text-emerald-400 whitespace-pre overflow-x-auto">
                    {JSON.stringify(tool.input_schema, null, 2)}
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button 
                    onClick={() => setSelectedTool(tool)}
                    className="text-xs flex items-center gap-1.5 bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/20 px-3 py-1.5 rounded transition-colors font-bold"
                  >
                    <BookOpen size={12} /> How to Use
                  </button>
                  <button 
                    onClick={() => openTestModal(tool)}
                    className="text-xs flex items-center gap-1.5 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/20 px-3 py-1.5 rounded transition-colors font-bold"
                  >
                    <Terminal size={12} /> Test Tool
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* How to Use Modal */}
      {selectedTool && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-5 border-b border-slate-800 bg-slate-900/50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-800 border border-slate-700 rounded text-sky-400">
                  <Wrench size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-slate-200">{selectedTool.name}</h3>
                  <span className="text-[10px] font-bold tracking-widest text-sky-400 uppercase bg-sky-500/10 px-2 py-0.5 rounded">Type: Tool</span>
                </div>
              </div>
              <button onClick={() => setSelectedTool(null)} className="p-2 text-slate-500 hover:text-slate-300 hover:bg-slate-800 rounded-lg transition-colors">
                <X size={20} />
              </button>
            </div>
            
            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6">
              {/* Description */}
              <div className="space-y-2">
                <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">About This Tool</h4>
                <p className="text-sm text-slate-400 leading-relaxed bg-slate-950/50 p-4 rounded-lg border border-slate-800">
                  {selectedTool.description}
                </p>
              </div>

              {/* Step by Step */}
              <div className="space-y-3">
                <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">How to Use (Step by Step)</h4>
                <div className="space-y-3">
                  <div className="flex gap-3 items-start bg-slate-950/30 p-3 rounded-lg border border-slate-800/50">
                    <div className="bg-slate-800 text-slate-300 w-6 h-6 rounded flex items-center justify-center font-bold text-xs shrink-0">1</div>
                    <div>
                      <p className="text-sm text-slate-300 font-semibold">Enable the Tool</p>
                      <p className="text-xs text-slate-500 mt-1">Assign this tool to an agent in the Agent Registry. The agent will then have access to call this tool during its reasoning loop.</p>
                    </div>
                  </div>
                  <div className="flex gap-3 items-start bg-slate-950/30 p-3 rounded-lg border border-slate-800/50">
                    <div className="bg-slate-800 text-slate-300 w-6 h-6 rounded flex items-center justify-center font-bold text-xs shrink-0">2</div>
                    <div>
                      <p className="text-sm text-slate-300 font-semibold">Format the Request</p>
                      <p className="text-xs text-slate-500 mt-1">The agent automatically structures a JSON payload matching the tool's required <span className="font-mono text-emerald-400">input_schema</span>.</p>
                    </div>
                  </div>
                  <div className="flex gap-3 items-start bg-slate-950/30 p-3 rounded-lg border border-slate-800/50">
                    <div className="bg-slate-800 text-slate-300 w-6 h-6 rounded flex items-center justify-center font-bold text-xs shrink-0">3</div>
                    <div>
                      <p className="text-sm text-slate-300 font-semibold">Process the Output</p>
                      <p className="text-xs text-slate-500 mt-1">The tool returns the result formatted according to the <span className="font-mono text-emerald-400">output_schema</span>, and the agent uses this context to continue its task.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Example */}
              <div className="space-y-2">
                <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Example Payload</h4>
                <div className="bg-slate-950 rounded-lg border border-slate-800 p-4">
                  <pre className="text-xs text-emerald-400 font-mono whitespace-pre-wrap">
                    {JSON.stringify(selectedTool.input_schema, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
            
            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex justify-end">
              <button 
                onClick={() => setSelectedTool(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-bold transition-colors"
              >
                Close Guide
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Test Tool Modal */}
      {testTool && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
            <div className="flex justify-between items-center p-5 border-b border-slate-800 bg-slate-900/50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded text-indigo-400">
                  <Terminal size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-slate-200">Test {testTool.name}</h3>
                  <span className="text-[10px] text-slate-500 uppercase tracking-widest">{testTool.slug}</span>
                </div>
              </div>
              <button onClick={() => setTestTool(null)} className="p-2 text-slate-500 hover:text-slate-300 hover:bg-slate-800 rounded-lg transition-colors">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto space-y-6 flex-1">
              <div className="space-y-2">
                <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider flex justify-between">
                  <span>Input JSON Payload</span>
                </h4>
                <textarea 
                  value={testPayload}
                  onChange={(e) => setTestPayload(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-4 text-xs font-mono text-emerald-400 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 min-h-[150px]"
                  placeholder="Enter JSON payload..."
                />
              </div>

              <div className="flex justify-end">
                <button 
                  onClick={handleTestTool}
                  disabled={testLoading}
                  className="px-6 py-2.5 bg-indigo-500 hover:bg-indigo-400 disabled:bg-slate-800 text-white disabled:text-slate-500 rounded-lg text-sm font-bold transition-colors flex items-center gap-2"
                >
                  {testLoading ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} fill="currentColor" />}
                  {testLoading ? 'Executing...' : 'Run Tool'}
                </button>
              </div>

              {testError && (
                <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-sm font-bold">
                  Error: {testError}
                </div>
              )}

              {testResult && (
                <div className="space-y-2">
                  <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Execution Result</h4>
                  <div className={`p-4 rounded-lg border font-mono text-xs overflow-auto max-h-[300px] whitespace-pre-wrap ${
                    testResult.status === 'success' ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-300' : 'bg-rose-500/5 border-rose-500/20 text-rose-300'
                  }`}>
                    {typeof testResult.output === 'object' ? JSON.stringify(testResult.output, null, 2) : testResult.output}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
