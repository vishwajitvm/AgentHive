export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-950 text-white p-8">
      <section className="max-w-6xl mx-auto">
        <p className="text-sm text-emerald-400 font-semibold">AgentHive</p>
        <h1 className="text-4xl font-bold mt-3">Multi-Agent Control Dashboard</h1>
        <p className="text-slate-300 mt-4 max-w-3xl">
          Manage agents, models, workflows, tools, logs, and provider fallback policies from one dashboard.
        </p>
        <div className="grid md:grid-cols-3 gap-4 mt-8">
          {['Agents', 'Models', 'Logs'].map((item) => (
            <div key={item} className="rounded-xl border border-slate-800 bg-slate-900 p-5">
              <h2 className="font-semibold text-xl">{item}</h2>
              <p className="text-slate-400 mt-2">Starter dashboard card for {item.toLowerCase()} module.</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
