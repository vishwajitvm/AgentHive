'use client';

import React, { useEffect, useState } from 'react';
import { getEnvSettings, saveEnvSetting } from '../../lib/api';
import { Key, ShieldAlert, CheckCircle, Save, HelpCircle } from 'lucide-react';

export default function EnvManagerPage() {
  const [env, setEnv] = useState<any>({});
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true);

  // Individual key entries
  const [keyName, setKeyName] = useState('GEMINI_API_KEY');
  const [keyValue, setKeyValue] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchEnv = async () => {
    try {
      const data = await getEnvSettings();
      setEnv(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyValue) return;
    setSaving(true);
    setSuccess('');
    try {
      await saveEnvSetting(keyName, keyValue);
      setSuccess(`Environment credential for '${keyName}' securely saved.`);
      setKeyValue('');
      fetchEnv();
      setTimeout(() => setSuccess(''), 4000);
    } catch (e) {
      alert("Failed to save credentials key.");
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    fetchEnv();
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Title */}
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight">Secrets & Cryptography</h2>
        <p className="text-slate-400 text-sm mt-1">Symmetrically encrypt third-party model keys in the postgres database.</p>
      </div>

      {success && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-semibold flex items-center gap-2">
          <CheckCircle size={16} /> {success}
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-8">
        {/* Save Form */}
        <div className="md:col-span-2 space-y-6">
          <form onSubmit={handleSave} className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 space-y-5">
            <h3 className="font-bold text-sm flex items-center gap-2 text-slate-300 border-b border-slate-900 pb-2">
              <Key size={16} className="text-emerald-400" /> Save API credentials
            </h3>
            
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Secret Key Name</label>
              <select 
                value={keyName}
                onChange={(e) => setKeyName(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
              >
                <option value="GEMINI_API_KEY">GEMINI_API_KEY</option>
                <option value="OPENAI_API_KEY">OPENAI_API_KEY</option>
                <option value="HUGGINGFACE_API_KEY">HUGGINGFACE_API_KEY</option>
                <option value="GROQ_API_KEY">GROQ_API_KEY</option>
                <option value="CUSTOM_LLM_API_KEY">CUSTOM_LLM_API_KEY</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Secret Key Value</label>
              <input 
                type="password"
                value={keyValue}
                onChange={(e) => setKeyValue(e.target.value)}
                placeholder="Enter secret API key token..."
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>

            <button 
              type="submit"
              disabled={saving || !keyValue}
              className="w-full py-3 rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-900 disabled:text-slate-600 text-slate-950 font-bold text-sm flex items-center justify-center gap-2 transition-all"
            >
              <Save size={16} /> {saving ? 'Saving key...' : 'Encrypt & Save Secret'}
            </button>
          </form>
        </div>

        {/* Info panel */}
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-900 bg-slate-950/20 p-6 space-y-4 text-xs">
            <h3 className="font-bold text-sm text-slate-300 border-b border-slate-900 pb-2">Active Config States</h3>
            <div className="space-y-3">
              {Object.entries(env).map(([key, val]: [string, any]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="text-slate-500 font-mono text-[10px]">{key}</span>
                  <span className={`font-semibold px-2 py-0.5 rounded ${val ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/15' : 'bg-slate-900 text-slate-500'}`}>
                    {val ? 'Configured' : 'Empty'}
                  </span>
                </div>
              ))}
            </div>
            
            <div className="p-4 rounded-lg bg-amber-500/5 border border-amber-500/10 text-amber-300 leading-relaxed mt-6 space-y-2">
              <div className="flex items-center gap-2 font-bold">
                <ShieldAlert size={14} /> Symmetric Encryption
              </div>
              <p>
                Credentials saved here are stored in the database encrypted via a 256-bit Fernet key and are never exposed in log outputs.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
