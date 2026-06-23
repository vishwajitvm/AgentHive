'use client';

import React, { useState, useEffect } from 'react';
import './globals.css';
import { 
  LayoutDashboard, 
  Bot, 
  Sliders, 
  Workflow, 
  Terminal, 
  Key, 
  Activity,
  Heart,
  ChevronLeft,
  ChevronRight,
  Wrench
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [healthStatus, setHealthStatus] = useState<'healthy' | 'degraded' | 'offline'>('offline');
  const [healthDetails, setHealthDetails] = useState<any>(null);

  // Poll backend health status
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/ready', { cache: 'no-store' });
        if (res.ok) {
          const data = await res.json();
          setHealthStatus(data.status === 'ready' ? 'healthy' : 'degraded');
          setHealthDetails(data);
        } else {
          setHealthStatus('offline');
        }
      } catch (e) {
        setHealthStatus('offline');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Agents', path: '/agents', icon: Bot },
    { name: 'Tools Directory', path: '/tools', icon: Wrench },
    { name: 'Models & Policies', path: '/models', icon: Sliders },
    { name: 'Workflows', path: '/workflows', icon: Workflow },
    { name: 'Activity Logs', path: '/logs', icon: Terminal },
    { name: 'Secrets Manager', path: '/env', icon: Key },
    { name: 'Monitoring', path: '/monitoring', icon: Activity },
  ];

  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 flex min-h-screen">
        {/* Sidebar */}
        <aside className={`border-r border-slate-900 bg-slate-950/70 backdrop-blur-md transition-all duration-300 flex flex-col ${isCollapsed ? 'w-20' : 'w-64'}`}>
          {/* Logo */}
          <div className="p-6 border-b border-slate-900 flex items-center justify-between">
            {!isCollapsed && (
              <span className="text-xl font-bold tracking-wider bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">
                AGENTHIVE
              </span>
            )}
            {isCollapsed && (
              <span className="text-xl font-extrabold text-emerald-400 mx-auto">AH</span>
            )}
            <button 
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="text-slate-500 hover:text-slate-200 transition-colors hidden md:block"
            >
              {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
            </button>
          </div>

          {/* Navigation links */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.path;
              return (
                <Link
                  key={item.name}
                  href={item.path}
                  className={`flex items-center gap-4 px-4 py-3 rounded-lg transition-all duration-200 group ${
                    isActive 
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/50 border border-transparent'
                  }`}
                >
                  <Icon size={20} className={isActive ? 'text-emerald-400' : 'text-slate-400 group-hover:text-slate-200'} />
                  {!isCollapsed && <span className="text-sm font-medium">{item.name}</span>}
                </Link>
              );
            })}
          </nav>

          {/* Footer health indicators */}
          <div className="p-4 border-t border-slate-900 space-y-3">
            <div className="flex items-center gap-3 justify-center md:justify-start">
              <span className={`w-3 h-3 rounded-full animate-pulse ${
                healthStatus === 'healthy' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' :
                healthStatus === 'degraded' ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]' :
                'bg-rose-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]'
              }`} />
              {!isCollapsed && (
                <span className="text-xs font-semibold text-slate-400">
                  {healthStatus === 'healthy' ? 'API Online' :
                   healthStatus === 'degraded' ? 'Degraded State' :
                   'API Offline'}
                </span>
              )}
            </div>
          </div>
        </aside>

        {/* Main Content Pane */}
        <div className="flex-1 flex flex-col min-h-screen">
          {/* Header */}
          <header className="border-b border-slate-900 bg-slate-950/40 backdrop-blur-md px-8 py-4 flex items-center justify-between sticky top-0 z-50">
            <div>
              <h1 className="text-lg font-bold">Workspace dashboard</h1>
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-xs px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-400">
                Single-User Dev Session
              </span>
            </div>
          </header>

          <main className="flex-1 p-8 overflow-y-auto bg-gradient-to-br from-slate-950 to-slate-900">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
