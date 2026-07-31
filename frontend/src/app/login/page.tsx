'use client';

import { useEffect } from 'react';
import { Shield } from 'lucide-react';

export default function LoginPage() {
  useEffect(() => {
    // Automatically redirect to Keycloak SSO
    const keycloakUrl = 'http://localhost:8080/realms/agenthive/protocol/openid-connect/auth';
    const clientId = 'agenthive-frontend';
    const redirectUri = encodeURIComponent('http://localhost:3000/api/auth/callback');
    const scope = encodeURIComponent('openid email profile');
    
    window.location.href = `${keycloakUrl}?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=${scope}`;
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
      <div className="flex flex-col items-center gap-4 animate-pulse">
        <div className="bg-emerald-500/10 w-16 h-16 rounded-2xl flex items-center justify-center border border-emerald-500/20">
          <Shield className="text-emerald-400" size={32} />
        </div>
        <h2 className="text-xl font-semibold text-slate-300">Redirecting to Secure Login...</h2>
      </div>
    </div>
  );
}
