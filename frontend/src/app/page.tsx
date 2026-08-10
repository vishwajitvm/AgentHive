'use client';

import React, { useEffect, useState } from 'react';
import { getSystemStats, getReadyStatus, getAgentRuns, getLlmCalls, getSystemResources } from '../lib/api';
import { 
  Cpu, 
  Activity, 
  Layers, 
  CheckCircle, 
  AlertTriangle,
  Play,
  Clock,
  Compass,
  Filter,
  DollarSign,
  TrendingUp,
  Server,
  Database
} from 'lucide-react';
import Link from 'next/link';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid } from 'recharts';

export default function DashboardHome() {
  const [stats, setStats] = useState<any>({
    total_runs: 0,
    total_llm_calls: 0,
    total_tokens: 0,
    prompt_tokens: 0,
    completion_tokens: 0,
    fallback_events: 0,
    success_rate: 100.0,
    tokens_by_provider: {},
    estimated_cost: 0,
    top_agents: [],
    latency_history: []
  });
  
  const [resources, setResources] = useState({ cpu_percent: 0, memory_percent: 0 });
  
  const [readyCheck, setReadyCheck] = useState<any>({
    database: 'loading',
    redis: 'loading',
    ollama: 'loading',
    minio: 'loading'
  });
  const [recentRuns, setRecentRuns] = useState<any[]>([]);
  const [recentCalls, setRecentCalls] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters State
  const [timeRange, setTimeRange] = useState('all');
  const [providerFilter, setProviderFilter] = useState('all');
  
  // Currency State
  const [currency, setCurrency] = useState('USD');
  const [exchangeRate, setExchangeRate] = useState(83.0); // Default fallback

  useEffect(() => {
    const fetchExchangeRate = async () => {
      try {
        const res = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
        const data = await res.json();
        if (data && data.rates && data.rates.INR) {
          setExchangeRate(data.rates.INR);
        }
      } catch (e) {
        console.error("Failed to fetch exchange rate", e);
      }
    };
    fetchExchangeRate();
  }, []);

  const fetchStats = async () => {
    try {
      const systemStats = await getSystemStats(timeRange, providerFilter);
      setStats(systemStats);
      
      const ready = await getReadyStatus();
      setReadyCheck(ready);

      const runs = await getAgentRuns(undefined, undefined, 5, 0);
      setRecentRuns(runs.items || runs);

      const calls = await getLlmCalls(undefined, 10, 0);
      setRecentCalls(calls.items || calls);
    } catch (e) {
      console.error("Failed to load dashboard metrics", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 60000); // Increased from 6s to 60s
    return () => clearInterval(interval);
  }, [timeRange, providerFilter]);
  
  useEffect(() => {
    const fetchRes = async () => {
      const res = await getSystemResources();
      setResources(res);
    };
    fetchRes();
    const interval = setInterval(fetchRes, 15000); // Increased from 3s to 15s
    return () => clearInterval(interval);
  }, []);

  const displayCost = currency === 'INR' 
    ? `₹${((stats.estimated_cost || 0) * exchangeRate).toFixed(2)}`
    : `$${(stats.estimated_cost || 0).toFixed(2)}`;

  const statCards = [
    { name: 'Estimated Cost', val: displayCost, desc: 'Approximated API spend', icon: DollarSign, color: 'from-emerald-500 to-teal-600' },
    { name: 'Total Executions', val: stats.total_runs, desc: 'Workflow runs in window', icon: Cpu, color: 'from-blue-500 to-indigo-600' },
    { name: 'LLM Call Requests', val: stats.total_llm_calls, desc: 'API queries routed', icon: Layers, color: 'from-purple-500 to-pink-600' },
    { name: 'Policy Success Rate', val: `${stats.success_rate}%`, desc: 'Runs without errors', icon: CheckCircle, color: 'from-amber-500 to-orange-600' },
  ];

  const COLORS = ['#10b981', '#3b82f6', '#a855f7', '#f59e0b', '#ec4899', '#06b6d4', '#8b5cf6', '#ef4444'];
  const chartData = Object.entries(stats.tokens_by_provider || {}).map(([key, val]: any) => ({
    name: key.toUpperCase(),
    value: val.prompt + val.completion
  }));

  return (
    <div className="space-y-6 pb-12">
      {/* Welcome Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-emerald-950/20 border border-slate-900 p-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="space-y-2">
          <p className="text-emerald-400 font-bold text-sm tracking-wider uppercase">Live Orchestration Hub</p>
          <h2 className="text-3xl font-extrabold tracking-tight">AgentHive Command Center</h2>
          <p className="text-slate-400 text-sm max-w-2xl">
            Monitor model fallback routing paths, view system metrics, and control multiple AI agents executing local and cloud computations.
          </p>
        </div>
        <Link href="/agents" className="px-5 py-3 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm flex items-center gap-2 shadow-lg shadow-emerald-500/20 transition-all duration-200">
          <Play size={16} fill="currentColor" /> Run Agent Task
        </Link>
      </div>

      {/* Analytics Filter Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-center bg-slate-900/80 border border-slate-800 rounded-xl p-5 gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <Filter size={18} className="text-emerald-500" />
          <h3 className="font-bold text-slate-200">Analytics Filters</h3>
        </div>
        <div className="flex gap-4 w-full sm:w-auto">
          <div className="flex flex-col space-y-1.5 w-full sm:w-48">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Time Range</label>
            <select 
              value={timeRange}
              onChange={e => setTimeRange(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all outline-none"
            >
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
              <option value="week">Last 7 Days</option>
              <option value="month">Last 30 Days</option>
              <option value="year">This Year</option>
              <option value="all">All Time</option>
            </select>
          </div>
          <div className="flex flex-col space-y-1.5 w-full sm:w-48">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">API Provider</label>
            <select 
              value={providerFilter}
              onChange={e => setProviderFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all outline-none"
            >
              <option value="all">All Providers (Grouped)</option>
              <option value="openai">OpenAI</option>
              <option value="gemini">Gemini</option>
              <option value="huggingface">Hugging Face</option>
              <option value="groq">Groq</option>
              <option value="ollama">Ollama</option>
            </select>
          </div>
          <div className="flex flex-col space-y-1.5 w-full sm:w-28">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Currency</label>
            <select 
              value={currency}
              onChange={e => setCurrency(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all outline-none"
            >
              <option value="USD">USD ($)</option>
              <option value="INR">INR (₹)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Cards Statistics Grid */}
      <div className="grid md:grid-cols-4 gap-6">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.name} className="relative overflow-hidden rounded-xl border border-slate-900 bg-slate-950/40 p-6 flex flex-col justify-between hover:border-slate-800 transition-all duration-300 group">
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{card.name}</p>
                  <p className="text-3xl font-extrabold mt-2 tracking-tight group-hover:text-emerald-400 transition-colors">{card.val}</p>
                </div>
                <div className={`p-3 rounded-lg bg-gradient-to-br ${card.color} text-white shadow-lg`}>
                  <Icon size={20} />
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-4 font-medium">{card.desc}</p>
            </div>
          );
        })}
      </div>
      
      {/* Visual Analytics Row 1 */}
      <div className="grid lg:grid-cols-3 gap-8">
        
        {/* Token Distribution (Recharts) */}
        <div className="rounded-xl border border-slate-900 bg-slate-950/30 p-6 flex flex-col lg:col-span-1">
          <div>
            <h3 className="font-bold text-lg">Token Distribution</h3>
            <p className="text-xs text-slate-500 mt-1">
              {providerFilter === 'all' ? 'Accumulated tokens grouped by provider' : `Tokens broken down by ${providerFilter.toUpperCase()} model`}
            </p>
          </div>

          <div className="h-[250px] w-full mt-6">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={95}
                    paddingAngle={3}
                    dataKey="value"
                    stroke="none"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip 
                    formatter={(value: any) => [`${value.toLocaleString()} tokens`, 'Usage']}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#f8fafc' }}
                    itemStyle={{ color: '#e2e8f0', fontWeight: 'bold' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="w-32 h-32 rounded-full border-4 border-dashed border-slate-800 flex items-center justify-center text-slate-600 font-bold text-sm">
                  No Data
                </div>
              </div>
            )}
          </div>

          <div className="space-y-3 mt-8 flex-1 overflow-y-auto pr-2 custom-scrollbar">
            {chartData.map((entry, idx) => (
              <div key={entry.name} className="flex justify-between items-center text-xs p-2 rounded-lg hover:bg-slate-900/50 transition-colors">
                <div className="flex items-center gap-3">
                  <span className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                  <span className="font-semibold text-slate-200">{entry.name}</span>
                </div>
                <span className="text-slate-400 font-bold">{entry.value.toLocaleString()} tokens</span>
              </div>
            ))}
            {chartData.length === 0 && (
              <p className="text-xs text-slate-500 text-center py-4">No token consumption in this period.</p>
            )}
          </div>
        </div>
        
        {/* Average Latency Area Chart */}
        <div className="rounded-xl border border-slate-900 bg-slate-950/30 p-6 flex flex-col lg:col-span-2">
            <div>
              <h3 className="font-bold text-lg">Average LLM Latency</h3>
              <p className="text-xs text-slate-500 mt-1">API response times over selected period</p>
            </div>
            <div className="h-[300px] w-full mt-8">
              {stats.latency_history && stats.latency_history.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={stats.latency_history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(val) => new Date(val).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                      stroke="#475569" 
                      tick={{ fill: '#64748b', fontSize: 10 }}
                    />
                    <YAxis stroke="#475569" tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={(val) => `${val}ms`} />
                    <RechartsTooltip 
                      labelFormatter={(val) => new Date(val).toLocaleString()}
                      formatter={(val) => [`${val} ms`, 'Latency']}
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                    />
                    <Area type="monotone" dataKey="latency" stroke="#10b981" fillOpacity={1} fill="url(#colorLatency)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-600 font-bold text-sm border border-dashed border-slate-800 rounded-xl">No latency data</div>
              )}
            </div>
        </div>
      </div>
      
      {/* Data Row 2 */}
      <div className="grid lg:grid-cols-3 gap-8">
          {/* Top Active Agents */}
          <div className="rounded-xl border border-slate-900 bg-slate-950/30 p-6 flex flex-col">
             <div className="flex justify-between items-center mb-6">
                <div>
                  <h3 className="font-bold text-lg">Top Active Agents</h3>
                  <p className="text-xs text-slate-500 mt-1">Most frequently executed workflows</p>
                </div>
                <TrendingUp className="text-blue-500" size={20} />
             </div>
             
             <div className="space-y-6 mt-2">
               {stats.top_agents?.map((agent: any, idx: number) => (
                 <div key={idx} className="space-y-2.5">
                   <div className="flex justify-between text-sm">
                     <span className="font-bold text-slate-200">{agent.name}</span>
                     <span className="text-blue-400 font-mono text-xs">{agent.runs} runs</span>
                   </div>
                   <div className="w-full bg-slate-900 rounded-full h-2">
                     <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${Math.min(100, (agent.runs / (stats.top_agents[0].runs || 1)) * 100)}%` }}></div>
                   </div>
                 </div>
               ))}
               {!stats.top_agents?.length && (
                 <div className="text-center py-6 border border-dashed border-slate-800 rounded-xl text-slate-500 text-sm font-medium">No agents executed recently.</div>
               )}
             </div>
          </div>
          
          {/* System Hardware */}
          <div className="rounded-xl border border-slate-900 bg-slate-950/30 p-6 flex flex-col">
             <div className="flex justify-between items-center mb-6">
                <div>
                  <h3 className="font-bold text-lg">System Hardware</h3>
                  <p className="text-xs text-slate-500 mt-1">Live Docker Backend Metrics</p>
                </div>
                <Server className="text-purple-500" size={20} />
             </div>
             
             <div className="space-y-8 mt-4">
               <div className="space-y-3">
                 <div className="flex justify-between text-sm">
                   <span className="font-bold text-slate-200 flex items-center gap-2"><Cpu size={14} className="text-purple-400"/> CPU Usage</span>
                   <span className="text-purple-400 font-mono font-bold text-xs">{resources.cpu_percent.toFixed(1)}%</span>
                 </div>
                 <div className="w-full bg-slate-900 rounded-full h-3">
                   <div className="bg-purple-500 h-3 rounded-full transition-all duration-500 shadow-[0_0_10px_rgba(168,85,247,0.4)]" style={{ width: `${resources.cpu_percent}%` }}></div>
                 </div>
               </div>
               
               <div className="space-y-3">
                 <div className="flex justify-between text-sm">
                   <span className="font-bold text-slate-200 flex items-center gap-2"><Database size={14} className="text-amber-400"/> Memory Allocation</span>
                   <span className="text-amber-400 font-mono font-bold text-xs">{resources.memory_percent.toFixed(1)}%</span>
                 </div>
                 <div className="w-full bg-slate-900 rounded-full h-3">
                   <div className="bg-amber-500 h-3 rounded-full transition-all duration-500 shadow-[0_0_10px_rgba(245,158,11,0.4)]" style={{ width: `${resources.memory_percent}%` }}></div>
                 </div>
               </div>
             </div>
          </div>

          <div className="rounded-xl border border-slate-900 bg-slate-950/30 p-6 flex flex-col">
             <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="font-bold text-lg">Recent Agents</h3>
                <p className="text-xs text-slate-500 mt-1">Live feed of orchestration</p>
              </div>
              <Link href="/logs" className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold underline decoration-emerald-500/30 underline-offset-4">All Logs</Link>
            </div>
            
            <div className="space-y-3">
              {recentRuns.map((run) => (
                <div key={run.id} className="flex items-center justify-between p-3 rounded-lg border border-slate-800/50 bg-slate-900/50 hover:border-slate-700 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-full ${run.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : run.status === 'running' ? 'bg-blue-500/10 text-blue-400' : 'bg-rose-500/10 text-rose-400'}`}>
                      {run.status === 'completed' ? <CheckCircle size={16} /> : run.status === 'running' ? <Activity size={16} className="animate-pulse" /> : <AlertTriangle size={16} />}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-slate-200">{run.task_prompt ? run.task_prompt.substring(0, 30) + (run.task_prompt.length > 30 ? '...' : '') : 'Unnamed Task'}</p>
                      <p className="text-[10px] text-slate-500 font-mono mt-0.5">Run ID: {run.id}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-semibold capitalize" style={{ color: run.status === 'completed' ? '#34d399' : run.status === 'running' ? '#60a5fa' : '#f87171' }}>{run.status}</p>
                    <p className="text-[10px] text-slate-500 font-mono mt-0.5">{new Date(run.created_at).toLocaleTimeString()}</p>
                  </div>
                </div>
              ))}
              {recentRuns.length === 0 && (
                <p className="text-center text-sm text-slate-500 py-4 border border-dashed border-slate-800 rounded-xl">No recent executions.</p>
              )}
            </div>
          </div>
      </div>
    </div>
  );
}
