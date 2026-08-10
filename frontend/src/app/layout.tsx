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
  Wrench,
  LogOut,
  UserCircle
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
    const interval = setInterval(checkHealth, 30000); // Increased from 8s to 30s
    return () => clearInterval(interval);
  }, []);

  const [isAdmin, setIsAdmin] = useState(false);
  const [userProfile, setUserProfile] = useState<{name: string, email: string} | null>(null);
  
  // Check admin status from JWT
  useEffect(() => {
    const token = document.cookie
      .split('; ')
      .find(row => row.startsWith('agenthive_token='))
      ?.split('=')[1];
      
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const roles = payload.resource_access?.['agenthive-frontend']?.roles || [];
        if (roles.includes('super_admin') || roles.includes('admin')) {
          setIsAdmin(true);
        }
        setUserProfile({
          name: payload.name || payload.preferred_username || payload.email?.split('@')[0] || 'User',
          email: payload.email || ''
        });
      } catch (e) {
        console.error('Failed to parse token');
      }
    }
  }, [pathname]);

  const handleLogout = () => {
    // Read the id_token for seamless Keycloak logout
    const idToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('agenthive_id_token='))
      ?.split('=')[1];

    document.cookie = "agenthive_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "agenthive_id_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    
    let logoutUrl = "http://localhost:8080/realms/agenthive/protocol/openid-connect/logout?client_id=agenthive-frontend&post_logout_redirect_uri=" + encodeURIComponent("http://localhost:3000/login");
    if (idToken) {
      logoutUrl += "&id_token_hint=" + idToken;
    }
    
    window.location.href = logoutUrl;
  };

  const allNavItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard, adminOnly: false },
    { name: 'Agents', path: '/agents', icon: Bot, adminOnly: false },
    { name: 'Tools Directory', path: '/tools', icon: Wrench, adminOnly: false },
    { name: 'Models & Policies', path: '/models', icon: Sliders, adminOnly: false },
    { name: 'Workflows', path: '/workflows', icon: Workflow, adminOnly: false },
    { name: 'Activity Logs', path: '/logs', icon: Terminal, adminOnly: true },
    { name: 'Secrets Manager', path: '/env', icon: Key, adminOnly: true },
    { name: 'Monitoring', path: '/monitoring', icon: Activity, adminOnly: true },
  ];

  const navItems = allNavItems.filter(item => !item.adminOnly || isAdmin);

  const isAuthPage = pathname === '/login' || pathname === '/signup' || pathname === '/verify';

  if (isAuthPage) {
    return (
      <html lang="en">
        <body className="bg-slate-950 text-slate-100 flex min-h-screen">
          <main className="flex-1 overflow-y-auto bg-gradient-to-br from-slate-950 to-slate-900">
            {children}
          </main>
        </body>
      </html>
    );
  }

  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 flex h-screen overflow-hidden">
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
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto custom-scrollbar">
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
          <div className="p-4 border-t border-slate-900 space-y-3 shrink-0">
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
        <div className="flex-1 flex flex-col h-screen overflow-hidden">
          {/* Header */}
          <header className="border-b border-slate-900 bg-slate-950/40 backdrop-blur-md px-8 py-4 flex items-center justify-between shrink-0">
            <div>
              <h1 className="text-lg font-bold">Workspace dashboard</h1>
            </div>
            
            <div className="flex items-center gap-4">
              {userProfile && (
                <div className="flex items-center gap-3 mr-4 pl-4 border-l border-slate-800">
                  <div className="bg-slate-800 p-1.5 rounded-full border border-slate-700">
                    <UserCircle size={22} className="text-emerald-400" />
                  </div>
                  <div className="flex flex-col hidden sm:flex">
                    <span className="text-sm font-bold text-slate-200 leading-tight">{userProfile.name}</span>
                    <span className="text-[10px] text-slate-500">{userProfile.email}</span>
                  </div>
                  <button 
                    onClick={handleLogout}
                    className="ml-2 p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-900 rounded-lg transition-colors"
                    title="Logout"
                  >
                    <LogOut size={18} />
                  </button>
                </div>
              )}
              <span className="text-xs px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-400 hidden md:inline-block">
                Single-User Dev Session
              </span>
            </div>
          </header>

          {/* Scrollable Main Content */}
          <main className="flex-1 p-8 overflow-y-auto bg-gradient-to-br from-slate-950 to-slate-900 custom-scrollbar">
            {children}
          </main>
          
          {/* Main Footer (Global) */}
          <footer className="border-t border-slate-900 bg-slate-950 px-8 py-3 shrink-0 flex items-center justify-between text-xs text-slate-500">
            <div>&copy; {new Date().getFullYear()} AgentHive Platform</div>
            <div className="flex items-center gap-4">
              <span className="hover:text-slate-300 cursor-pointer transition-colors">Documentation</span>
              <span className="hover:text-slate-300 cursor-pointer transition-colors">Support</span>
              <span className="hover:text-slate-300 cursor-pointer transition-colors">v1.0.0-beta</span>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
