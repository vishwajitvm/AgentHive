'use client';

import React, { useEffect, useState } from 'react';
import { 
  listProviders, 
  configureProvider, 
  listPolicies, 
  createPolicy, 
  activatePolicy 
} from '../../lib/api';
import { 
  Sliders, 
  Layers, 
  Save, 
  CheckCircle, 
  Key, 
  Settings,
  HelpCircle,
  Activity
} from 'lucide-react';

export default function ModelProvidersPage() {
  const [providers, setProviders] = useState<any[]>([]);
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [successMsg, setSuccessMsg] = useState('');

  // Selected policy variables
  const [policyForm, setPolicyForm] = useState({
    name: 'Custom Fallback Policy',
    primary_provider: 'gemini',
    secondary_provider: 'ollama',
    fallback_order: 'gemini,ollama,huggingface,groq,openai',
    max_input_tokens: 12000,
    max_output_tokens: 2048,
    timeout_seconds: 60,
    retry_count: 2
  });

  const fetchModelData = async () => {
    try {
      const provList = await listProviders();
      setProviders(provList);
      
      const polList = await listPolicies();
      setPolicies(polList);

      // Populate policy form with active policy details
      const active = polList.find((p: any) => p.is_active);
      if (active) {
        setPolicyForm({
          name: active.name,
          primary_provider: active.primary_provider,
          secondary_provider: active.secondary_provider,
          fallback_order: active.fallback_order,
          max_input_tokens: active.max_input_tokens,
          max_output_tokens: active.max_output_tokens,
          timeout_seconds: active.timeout_seconds,
          retry_count: active.retry_count
        });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleProviderSave = async (provType: string, formValues: any) => {
    try {
      await configureProvider({
        provider_name: formValues.provider_name,
        provider_type: provType,
        base_url: formValues.base_url,
        default_model: formValues.default_model,
        api_key: formValues.api_key,
        enabled: formValues.enabled
      });
      setSuccessMsg(`Provider '${formValues.provider_name}' successfully updated.`);
      fetchModelData();
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (e) {
      alert("Failed to save provider config.");
    }
  };

  const handlePolicySave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const pol = await createPolicy(policyForm);
      if (pol.id) {
        await activatePolicy(pol.id);
        setSuccessMsg("LLM Fallback policy successfully activated.");
        fetchModelData();
        setTimeout(() => setSuccessMsg(''), 4000);
      }
    } catch (e) {
      alert("Failed to save and activate model policy.");
    }
  };

  useEffect(() => {
    fetchModelData();
  }, []);

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight">Models & Fallback Policies</h2>
        <p className="text-slate-400 text-sm mt-1">Configure credentials for cloud models and dictate automatic failover policies.</p>
      </div>

      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-semibold flex items-center gap-2">
          <CheckCircle size={16} /> {successMsg}
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Left Column: Configure Providers */}
        <div className="lg:col-span-2 space-y-6">
          <h3 className="font-bold text-lg flex items-center gap-2 border-b border-slate-900 pb-3">
            <Sliders size={18} className="text-emerald-400" /> API Providers Configurations
          </h3>

          <div className="space-y-6">
            {providers.map((prov) => (
              <ProviderFormCard 
                key={prov.provider_type} 
                provider={prov} 
                onSave={(vals) => handleProviderSave(prov.provider_type, vals)} 
              />
            ))}
            {providers.length === 0 && !loading && (
              <p className="text-center text-slate-500 py-10 font-medium">Loading providers lists...</p>
            )}
          </div>
        </div>

        {/* Right Column: Policies Form */}
        <div className="space-y-6">
          <h3 className="font-bold text-lg flex items-center gap-2 border-b border-slate-900 pb-3">
            <Layers size={18} className="text-emerald-400" /> Active Fallback Policy
          </h3>

          <form onSubmit={handlePolicySave} className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 space-y-5">
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Policy Name</label>
              <input 
                type="text" 
                value={policyForm.name} 
                onChange={(e) => setPolicyForm({...policyForm, name: e.target.value})}
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Primary Provider</label>
                <select 
                  value={policyForm.primary_provider}
                  onChange={(e) => setPolicyForm({...policyForm, primary_provider: e.target.value})}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
                >
                  <option value="gemini">Gemini</option>
                  <option value="ollama">Ollama</option>
                  <option value="openai">OpenAI (GPT)</option>
                  <option value="huggingface">Hugging Face</option>
                  <option value="groq">Groq</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Secondary Provider</label>
                <select 
                  value={policyForm.secondary_provider}
                  onChange={(e) => setPolicyForm({...policyForm, secondary_provider: e.target.value})}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
                >
                  <option value="gemini">Gemini</option>
                  <option value="ollama">Ollama</option>
                  <option value="openai">OpenAI (GPT)</option>
                  <option value="huggingface">Hugging Face</option>
                  <option value="groq">Groq</option>
                </select>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Fallback routing order</label>
              <input 
                type="text" 
                value={policyForm.fallback_order} 
                onChange={(e) => setPolicyForm({...policyForm, fallback_order: e.target.value})}
                placeholder="gemini,ollama,huggingface,groq,openai"
                className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-emerald-500"
              />
              <p className="text-[10px] text-slate-500 leading-normal">Comma-separated list prioritising failover order if endpoints fail.</p>
            </div>

            <div className="grid grid-cols-2 gap-4 border-t border-slate-900 pt-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Max Input Tokens</label>
                <input 
                  type="number" 
                  value={policyForm.max_input_tokens} 
                  onChange={(e) => setPolicyForm({...policyForm, max_input_tokens: parseInt(e.target.value) || 4000})}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Max Output Tokens</label>
                <input 
                  type="number" 
                  value={policyForm.max_output_tokens} 
                  onChange={(e) => setPolicyForm({...policyForm, max_output_tokens: parseInt(e.target.value) || 2048})}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Timeout (seconds)</label>
                <input 
                  type="number" 
                  value={policyForm.timeout_seconds} 
                  onChange={(e) => setPolicyForm({...policyForm, timeout_seconds: parseInt(e.target.value) || 60})}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Retry count</label>
                <input 
                  type="number" 
                  value={policyForm.retry_count} 
                  onChange={(e) => setPolicyForm({...policyForm, retry_count: parseInt(e.target.value) || 1})}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <button 
              type="submit" 
              className="w-full py-3 mt-4 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm flex items-center justify-center gap-2 transition-all shadow-lg shadow-emerald-500/10"
            >
              <Save size={16} /> Save & Activate Policy
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// Inner helper component for Provider Forms
function ProviderFormCard({ provider, onSave }: { provider: any; onSave: (vals: any) => void }) {
  const [form, setForm] = useState({
    provider_name: provider.provider_name,
    base_url: provider.base_url || '',
    default_model: provider.default_model,
    api_key: '',
    enabled: provider.enabled
  });

  return (
    <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-6 space-y-4 hover:border-slate-800 transition-colors">
      <div className="flex justify-between items-center border-b border-slate-900/60 pb-3">
        <div className="flex items-center gap-2.5">
          <span className="text-base font-bold">{provider.provider_name}</span>
          <span className="text-[10px] bg-slate-900 border border-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono uppercase">
            {provider.provider_type}
          </span>
        </div>
        
        <label className="flex items-center gap-2 cursor-pointer">
          <input 
            type="checkbox" 
            checked={form.enabled}
            onChange={(e) => setForm({...form, enabled: e.target.checked})}
            className="rounded text-emerald-500 focus:ring-emerald-500"
          />
          <span className="text-xs text-slate-400 font-semibold">Enabled</span>
        </label>
      </div>

      <div className="grid md:grid-cols-3 gap-4 text-xs">
        <div className="space-y-1">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Default Model</label>
          <input 
            type="text"
            value={form.default_model}
            onChange={(e) => setForm({...form, default_model: e.target.value})}
            className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="space-y-1">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Base URL (optional)</label>
          <input 
            type="text"
            value={form.base_url}
            onChange={(e) => setForm({...form, base_url: e.target.value})}
            className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="space-y-1">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
            <Key size={10} /> API Key / Credential
          </label>
          <input 
            type="password"
            value={form.api_key}
            onChange={(e) => setForm({...form, api_key: e.target.value})}
            placeholder={provider.has_key ? '••••••••' : 'Not configured'}
            className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 focus:outline-none focus:border-emerald-500"
          />
        </div>
      </div>

      <div className="flex justify-end pt-2">
        <button 
          onClick={() => onSave(form)}
          className="px-4 py-2 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800/80 hover:text-slate-100 text-slate-300 font-bold text-xs flex items-center gap-1.5 transition-colors"
        >
          <Save size={12} /> Save Settings
        </button>
      </div>
    </div>
  );
}
