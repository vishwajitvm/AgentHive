'use client';

import React, { useEffect, useState } from 'react';
import { getSystemStats, getReadyStatus, getAgentRuns, getLlmCalls } from '../lib/api';
import { 
  Cpu, 
  Activity, 
  Layers, 
  RotateCcw, 
  CheckCircle, 
  AlertTriangle,
  Play,
  Clock,
  Compass
} from 'lucide-react';
import Link from 'next/link';

export default function DashboardHome() {
  const [stats, setStats] = useState<any>({
    total_runs: 0,
    total_llm_calls: 0,
    total_tokens: 0,
    prompt_tokens: 0,
    completion_tokens: 0,
    fallback_events: 0,
    success_rate: 100.0,
    tokens_by_provider: {}
  });
  const [readyCheck, setReadyCheck] = useState<any>({
    database: 'loading',
    redis: 'loading',
    ollama: 'loading',
    minio: 'loading'
  });
  const [recentRuns, setRecentRuns] = useState<any[]>([]);
  const [recentCalls, setRecentCalls] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const systemStats = await getSystemStats();
      setStats(systemStats);
      
      const ready = await getReadyStatus();
      setReadyCheck(ready);

      const runs = await getAgentRuns();
      setRecentRuns(runs.slice(0, 5));

      const calls = await getLlmCalls();
      setRecentCalls(calls.slice(0, 5));
    } catch (e) {
      console.error("Failed to load dashboard metrics", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 6000);
    return () => clearInterval(interval);
  }, []);

  const statCards = [
    { name: 'Total Agent Executions', val: stats.total_runs, desc: 'Successful workflow runs', icon: Cpu, color: 'from-blue-500 to-indigo-600' },
    { name: 'LLM Call Requests', val: stats.total_llm_calls, desc: 'API queries routed', icon: Layers, color: 'from-emerald-500 to-teal-600' },
    { name: 'Total Token Consumption', val: stats.total_tokens.toLocaleString(), desc: `${stats.prompt_tokens.toLocaleString()} in / ${stats.completion_tokens.toLocaleString()} out`, icon: Compass, color: 'from-purple-500 to-pink-600' },
    { name: 'Policy Success Rate', val: `${stats.success_rate}%`, desc: 'Runs completing without errors', icon: CheckCircle, color: 'from-amber-500 to-orange-600' },
  ];

  return (
    <div className="space-y-8">
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

      {/* Health Checks matrix */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(readyCheck).map(([service, status]: [string, any]) => {
          if (service === 'status') return null;
          const isOk = status === 'healthy';
          return (
            <div key={service} className="rounded-xl border border-slate-900 bg-slate-950/40 p-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">{service}</p>
                <p className="text-sm font-semibold capitalize mt-1">{status}</p>
              </div>
              <span className={`w-3.5 h-3.5 rounded-full ${isOk ? 'bg-emerald-500' : 'bg-rose-500'} animate-pulse`} />
            </div>
          );
        })}
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

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Token Distribution (SVG Chart) */}
        <div className="rounded-xl border border-slate-900 bg-slate-950/30 p-6 space-y-6 lg:col-span-1">
          <div>
            <h3 className="font-bold text-lg">Token Distribution</h3>
            <p className="text-xs text-slate-500 mt-1">Accumulated tokens grouped by provider</p>
          </div>

          <div className="flex justify-center py-4">
            {/* Custom SVG pie/bar display */}
            <svg width="180" height="180" viewBox="0 0 200 200" className="transform -rotate-90">
              <circle cx="100" cy="100" r="80" fill="transparent" stroke="#1e293b" strokeWidth="20" />
              {/* If no stats, render placeholder */}
              {stats.total_tokens === 0 ? (
                <circle cx="100" cy="100" r="80" fill="transparent" stroke="#3b82f6" strokeWidth="20" strokeDasharray="502" strokeDashoffset="250" />
              ) : (
                Object.entries(stats.tokens_by_provider).map(([prov, usage]: [string, any], idx) => {
                  const total = usage.prompt + usage.completion;
                  const percent = total / stats.total_tokens;
                  const strokeLen = percent * 502; // Circumference = 2 * pi * r = 2 * 3.14 * 80 = 502
                  // Calculate cumulative dash offsets
                  let offset = 0;
                  return (
                    <circle 
                      key={prov}
                      cx="100" 
                      cy="100" 
                      r="80" 
                      fill="transparent" 
                      stroke={idx === 0 ? '#10b981' : idx === 1 ? '#3b82f6' : '#a855f7'} 
                      strokeWidth="20" 
                      strokeDasharray="502" 
                      strokeDashoffset={502 - strokeLen}
                      className="transition-all duration-500"
                    />
                  );
                })
              )}
            </svg>
          </div>

          <div className="space-y-3">
            {Object.entries(stats.tokens_by_provider).map(([prov, usage]: [string, any], idx) => {
              const total = usage.prompt + usage.completion;
              return (
                <div key={prov} className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${idx === 0 ? 'bg-emerald-500' : idx === 1 ? 'bg-blue-500' : 'bg-purple-500'}`} />
                    <span className="font-semibold uppercase">{prov}</span>
                  </div>
                  <span className="text-slate-400 font-bold">{total.toLocaleString()} tokens</span>
                </div>
              );
            })}
            {Object.keys(stats.tokens_by_provider).length === 0 && (
              <p className="text-xs text-slate-500 text-center py-4">No token consumption logged yet.</p>
            )}
          </div>
        </div>

        {/* Live Fallbacks Timeline / LLM Calls */}
        <div className="rounded-xl border border-slate-900 bg-slate-950/30 p-6 space-y-6 lg:col-span-2">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-bold text-lg">Model Fallback Incidents</h3>
              <p className="text-xs text-slate-500 mt-1">Automatic failovers logged by routing policy</p>
            </div>
            <span className="text-xs bg-rose-500/10 text-rose-400 px-2 py-0.5 rounded border border-rose-500/20 font-bold">
              {stats.fallback_events} Fallbacks
            </span>
          </div>

          <div className="space-y-4">
            {recentCalls.filter(c => c.fallback_reason || c.status === 'error').map((call) => (
              <div key={call.id} className="p-4 rounded-lg bg-rose-500/5 border border-rose-500/10 flex items-start gap-4 hover:bg-rose-500/10 transition-colors">
                <AlertTriangle className="text-rose-400 flex-shrink-0 mt-1" size={18} />
                <div className="space-y-1 flex-1">
                  <div className="flex justify-between items-center">
                    <p className="text-sm font-bold uppercase text-rose-300">Fallback Event: {call.provider}</p>
                    <span className="text-xs text-slate-500 flex items-center gap-1">
                      <Clock size={12} /> {new Date(call.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">Model Requested: <code className="text-rose-200">{call.model}</code></p>
                  <p className="text-xs text-rose-200 font-medium italic mt-2">{call.fallback_reason || call.failure_reason}</p>
                </div>
              </div>
            ))}
            {recentCalls.filter(c => c.fallback_reason || c.status === 'error').length === 0 && (
              <div className="text-center py-12 border border-dashed border-slate-900 rounded-lg space-y-3">
                <Activity size={32} className="text-slate-600 mx-auto" />
                <p className="text-sm text-slate-400">All routed calls resolved on primary endpoints. No fallback triggers recorded.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
