'use client';

import React from 'react';
import { 
  Activity, 
  ExternalLink, 
  BarChart3, 
  ListCollapse, 
  Terminal,
  Server
} from 'lucide-react';

export default function MonitoringConsolePage() {
  const monitoringTools = [
    {
      name: 'Grafana Dashboards',
      desc: 'Visualize application metrics, latency percentiles, and system CPU/Memory loads.',
      url: 'http://localhost:3001',
      port: '3001',
      details: 'Visual metrics charts'
    },
    {
      name: 'Prometheus Server',
      desc: 'Query scraped time-series database metrics for AgentHive backend endpoints.',
      url: 'http://localhost:9090',
      port: '9090',
      details: 'Time-series queries'
    },
    {
      name: 'Grafana Loki Engine',
      desc: 'Log aggregation platform shipping stdout streams from all Docker containers.',
      url: 'http://localhost:3100',
      port: '3100',
      details: 'Aggregated raw logs query'
    }
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Title */}
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight">System Monitoring & Metrics</h2>
        <p className="text-slate-400 text-sm mt-1">Audit container resources, track request timings, and search Loki aggregators.</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {monitoringTools.map((tool) => (
          <div key={tool.name} className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 flex flex-col justify-between hover:border-slate-800 transition-colors">
            <div className="space-y-4">
              <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-emerald-400 w-fit">
                <Activity size={20} />
              </div>
              
              <div>
                <h3 className="font-bold text-base">{tool.name}</h3>
                <p className="text-[10px] text-slate-500 font-mono mt-0.5">LOCAL PORT: {tool.port}</p>
                <p className="text-sm text-slate-400 mt-3 leading-relaxed">{tool.desc}</p>
              </div>
            </div>

            <a 
              href={tool.url}
              target="_blank" 
              rel="noopener noreferrer"
              className="w-full py-2.5 mt-6 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-slate-100 text-slate-300 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
            >
              Open Console <ExternalLink size={12} />
            </a>
          </div>
        ))}
      </div>

      {/* Observability Guide */}
      <div className="rounded-xl border border-slate-900 bg-slate-950/20 p-8 mt-8 space-y-4">
        <h3 className="font-bold text-base flex items-center gap-2 text-slate-300">
          <Server size={18} className="text-emerald-400" /> Shipped Observability Namespaces
        </h3>
        
        <div className="grid md:grid-cols-2 gap-6 text-xs text-slate-400 leading-relaxed">
          <div className="space-y-2 border-l border-slate-900 pl-4">
            <h4 className="font-bold text-slate-200 text-sm flex items-center gap-1.5">
              <Terminal size={14} /> Loki container streams
            </h4>
            <p>
              All application container logs (FastAPI backend, Celery workers, postgres) are collected by Promtail and forwarded to Loki. Search logs inside Grafana under the Explore tab using label `{'container="agenthive-backend"'}`.
            </p>
          </div>

          <div className="space-y-2 border-l border-slate-900 pl-4">
            <h4 className="font-bold text-slate-200 text-sm flex items-center gap-1.5">
              <BarChart3 size={14} /> Prometheus Scrape targets
            </h4>
            <p>
              The FastAPI backend exposes performance and call metrics under `/metrics`. Prometheus queries this data every 15s to monitor latency percentiles, endpoint success rates, and token aggregates.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
