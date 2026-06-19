import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Brain,
  Database,
  TrendingUp,
  History,
  Code,
  Search,
  Zap,
  Activity,
  MessageSquare,
  Clock,
  Shield,
  ChevronRight,
  Menu,
  X
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area,
  BarChart, Bar, Cell, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { DEMO_DATA } from './data/demo-data';

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
      active
        ? 'bg-thai-gold/10 text-thai-gold border border-thai-gold/20'
        : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
    }`}
  >
    <Icon size={20} />
    <span className="font-medium">{label}</span>
  </button>
);

const Card = ({ title, children, className = "" }) => (
  <div className={`glass-card p-6 ${className}`}>
    {title && <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 gold-text">{title}</h3>}
    {children}
  </div>
);

const KpiCard = ({ icon: Icon, label, value, delta, color = "gold" }) => (
  <div className="glass-card p-5 relative overflow-hidden group">
    <div className={`absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 opacity-5 rounded-full bg-thai-${color} transition-all group-hover:scale-110`} />
    <div className="flex justify-between items-start">
      <div>
        <p className="text-slate-400 text-sm font-medium mb-1">{label}</p>
        <h4 className="text-2xl font-bold text-white">{value}</h4>
        {delta && (
          <p className="text-emerald-400 text-xs mt-1 flex items-center">
            <TrendingUp size={12} className="mr-1" />
            +{delta} this week
          </p>
        )}
      </div>
      <div className={`p-3 rounded-lg bg-thai-${color}/10 text-thai-${color}`}>
        <Icon size={24} />
      </div>
    </div>
  </div>
);

export default function App() {
  const [activeTab, setActiveTab] = useState('Overview');
  const [data, setData] = useState(DEMO_DATA);
  const [loading, setLoading] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const response = await fetch('/data.json');
        if (response.ok) {
          const liveData = await response.json();
          setData(liveData);
        }
      } catch (e) {
        console.warn("Live data not found, using demo data");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const growthData = data.growth.labels.map((label, i) => ({
    name: label,
    facts: data.growth.facts[i],
    observations: data.growth.observations[i]
  }));

  const renderOverview = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard icon={Database} label="Total Facts" value={data.kpis.total_facts} delta={data.kpis.total_facts_delta} color="gold" />
        <KpiCard icon={Brain} label="Observations" value={data.kpis.total_observations} delta={data.kpis.total_observations_delta} color="bronze" />
        <KpiCard icon={Activity} label="Total Sessions" value={data.kpis.sessions || 0} color="gold" />
        <KpiCard icon={Zap} label="Tokens Used" value={(data.kpis.total_tokens || 0).toLocaleString()} color="bronze" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Knowledge Growth" className="lg:col-span-2">
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={growthData}>
                <defs>
                  <linearGradient id="colorFacts" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#d9b54a" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#d9b54a" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#121216', border: '1px solid #ffffff10', borderRadius: '12px' }}
                  itemStyle={{ color: '#d9b54a' }}
                />
                <Area type="monotone" dataKey="facts" stroke="#d9b54a" fillOpacity={1} fill="url(#colorFacts)" strokeWidth={2} />
                <Area type="monotone" dataKey="observations" stroke="#c9813f" fillOpacity={0} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Top Observations">
          <div className="space-y-4">
            {data.top_observations.map((obs, i) => (
              <div key={i} className="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-thai-gold/20 transition-all">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-bold text-thai-bronze uppercase tracking-wider">Weight {obs.weight}</span>
                </div>
                <p className="text-sm text-slate-200">{obs.summary}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );

  const renderMemory = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Card title="Recent Facts">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-bottom border-white/10">
                <th className="pb-4 font-semibold text-slate-400 text-sm">Kind</th>
                <th className="pb-4 font-semibold text-slate-400 text-sm">Key</th>
                <th className="pb-4 font-semibold text-slate-400 text-sm">Value</th>
                <th className="pb-4 font-semibold text-slate-400 text-sm">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {data.recent_facts.map((fact) => (
                <tr key={fact.id} className="group hover:bg-white/5 transition-colors">
                  <td className="py-4">
                    <span className="px-2 py-1 rounded-md bg-thai-gold/10 text-thai-gold text-xs font-bold uppercase">
                      {fact.kind}
                    </span>
                  </td>
                  <td className="py-4 text-sm font-mono text-slate-300">{fact.key || '—'}</td>
                  <td className="py-4 text-sm text-slate-200">{fact.value}</td>
                  <td className="py-4 text-sm text-slate-400">{fact.created}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );

  const renderChatReasoning = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Card title="Thought Process">
        <div className="space-y-6">
          {data.chat.thought_process.map((group, i) => (
            <div key={i} className="relative pl-6 border-l border-thai-gold/30">
              <div className="absolute -left-[5px] top-0 w-[9px] h-[9px] rounded-full bg-thai-gold shadow-[0_0_8px_rgba(217,181,74,0.6)]" />
              <h4 className="text-sm font-bold text-thai-gold uppercase tracking-widest mb-3">{group.group}</h4>
              <ul className="space-y-2">
                {group.steps.map((step, si) => (
                  <li key={si} className="flex items-center text-sm text-slate-300">
                    <ChevronRight size={14} className="mr-2 text-thai-bronze" />
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Recent Exchange">
        <div className="space-y-4">
          {data.chat.messages.map((msg, i) => (
            <div key={i} className={`p-4 rounded-2xl ${
              msg.role === 'user'
                ? 'bg-white/5 ml-8 rounded-tr-none border border-white/5'
                : 'bg-thai-gold/10 mr-8 rounded-tl-none border border-thai-gold/20'
            }`}>
              <p className="text-xs font-bold mb-1 opacity-50 uppercase tracking-wider">
                {msg.role}
              </p>
              <p className="text-sm text-slate-200">{msg.text}</p>
            </div>
          ))}
          <div className="mt-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between">
            <span className="text-xs font-medium text-emerald-400">Response Confidence</span>
            <span className="text-sm font-bold text-emerald-400">{data.chat.confidence}%</span>
          </div>
        </div>
      </Card>
    </div>
  );

  const renderEvolution = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Card title="Performance Evolution">
        <div className="grid grid-cols-2 gap-4 mb-8">
          <div className="p-4 rounded-xl bg-white/5 border border-white/5">
            <p className="text-slate-400 text-xs mb-1">Performance Gain</p>
            <p className="text-2xl font-bold text-thai-gold">{data.evolution.performance_gain}</p>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/5">
            <p className="text-slate-400 text-xs mb-1">Success Rate</p>
            <p className="text-2xl font-bold text-emerald-400">{data.evolution.success_rate}%</p>
          </div>
        </div>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data.evolution.neural_focus}>
              <PolarGrid stroke="#ffffff10" />
              <PolarAngleAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10 }} />
              <Radar
                name="Performance"
                dataKey="pct"
                stroke="#d9b54a"
                fill="#d9b54a"
                fillOpacity={0.3}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card title="Evolution History">
        <div className="space-y-4">
          {[
            { version: 'v2.1', date: 'Jun 18, 2025', gain: '+24%', status: 'active' },
            { version: 'v2.0', date: 'Jun 01, 2025', gain: '+18%', status: 'stable' },
            { version: 'v1.9', date: 'May 15, 2025', gain: '+12%', status: 'legacy' },
          ].map((v, i) => (
            <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${v.status === 'active' ? 'bg-thai-gold animate-pulse' : 'bg-slate-600'}`} />
                <div>
                  <p className="text-sm font-bold text-white">{v.version}</p>
                  <p className="text-xs text-slate-500">{v.date}</p>
                </div>
              </div>
              <span className="text-sm font-mono text-thai-gold">{v.gain}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );

  const renderSkills = () => (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {data.skills?.map((cat, i) => (
        <div key={i}>
          <div className="flex items-center gap-3 mb-4">
            <h3 className="text-sm font-bold text-thai-gold uppercase tracking-widest">{cat.category}</h3>
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-xs text-slate-500 font-medium">{cat.count} Skills</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cat.skills.map((skill, si) => (
              <div key={si} className="glass-card p-5 border border-white/5 hover:border-thai-gold/30 transition-all group">
                <div className="flex justify-between items-start mb-3">
                  <h4 className="font-bold text-slate-200 group-hover:text-thai-gold transition-colors">{skill.name}</h4>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-slate-400 font-mono">v{skill.version}</span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-2 mb-4 leading-relaxed">
                  {skill.description}
                </p>
                <div className="flex flex-wrap gap-2">
                  {skill.tags.map((tag, ti) => (
                    <span key={ti} className="text-[10px] font-bold text-thai-bronze border border-thai-bronze/30 px-2 py-0.5 rounded-full uppercase tracking-tighter">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );

  const renderActivity = () => (
    <Card title="Agent Activity Logs" className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="space-y-4">
        {data.recent_sessions?.map((session, i) => (
          <div key={i} className="p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all">
            <div className="flex flex-wrap items-center justify-between gap-4 mb-3">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-thai-gold/10 text-thai-gold">
                  <Activity size={16} />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">{session.task}</h4>
                  <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">{session.model} · {session.date}</p>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-xs font-bold text-white">{session.total_tokens.toLocaleString()}</p>
                  <p className="text-[10px] text-slate-500 uppercase tracking-tighter">Tokens</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-bold text-white">{session.iterations}</p>
                  <p className="text-[10px] text-slate-500 uppercase tracking-tighter">Steps</p>
                </div>
                <div className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${
                  session.stop_reason === 'success' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                }`}>
                  {session.stop_reason}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'Overview': return renderOverview();
      case 'Memory': return renderMemory();
      case 'Chat & Reasoning': return renderChatReasoning();
      case 'Evolution': return renderEvolution();
      case 'Skills': return renderSkills();
      case 'Agent Activity': return renderActivity();
      default: return renderOverview();
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 glass-card rounded-none border-y-0 border-l-0 transform transition-transform duration-300 lg:relative lg:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8 px-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-thai-gold to-thai-bronze flex items-center justify-center shadow-[0_0_15px_rgba(217,181,74,0.4)]">
              <Zap className="text-black" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">SakThai<span className="text-thai-gold">-Agent</span></h1>
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Mission Control v2.1</p>
            </div>
          </div>

          <nav className="space-y-2">
            <SidebarItem icon={LayoutDashboard} label="Overview" active={activeTab === 'Overview'} onClick={() => setActiveTab('Overview')} />
            <SidebarItem icon={Database} label="Memory" active={activeTab === 'Memory'} onClick={() => setActiveTab('Memory')} />
            <SidebarItem icon={MessageSquare} label="Chat & Reasoning" active={activeTab === 'Chat & Reasoning'} onClick={() => setActiveTab('Chat & Reasoning')} />
            <SidebarItem icon={TrendingUp} label="Evolution" active={activeTab === 'Evolution'} onClick={() => setActiveTab('Evolution')} />
            <SidebarItem icon={Code} label="Skills" active={activeTab === 'Skills'} onClick={() => setActiveTab('Skills')} />
            <SidebarItem icon={Activity} label="Agent Activity" active={activeTab === 'Agent Activity'} onClick={() => setActiveTab('Agent Activity')} />
          </nav>
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-6">
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-bold text-slate-300">System Online</span>
            </div>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              Serving live snapshots from local SQLite memory store.
            </p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-premium-gradient">
        <header className="sticky top-0 z-40 flex items-center justify-between px-8 py-4 bg-thai-dark/50 backdrop-blur-xl border-b border-white/5">
          <div className="flex items-center gap-4">
            <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="lg:hidden text-slate-400">
              {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            <h2 className="text-lg font-semibold text-white">{activeTab}</h2>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
              <input
                type="text"
                placeholder="Search memory..."
                className="bg-white/5 border border-white/10 rounded-full py-1.5 pl-10 pr-4 text-sm text-slate-300 focus:outline-none focus:border-thai-gold/50 w-64 transition-all"
              />
            </div>
            <button className="p-2 rounded-full bg-white/5 text-slate-400 hover:text-white transition-colors border border-white/10">
              <Shield size={20} />
            </button>
          </div>
        </header>

        <div className="p-8 max-w-7xl mx-auto">
          {loading ? (
            <div className="flex items-center justify-center h-[60vh]">
              <div className="w-12 h-12 border-4 border-thai-gold/20 border-t-thai-gold rounded-full animate-spin" />
            </div>
          ) : renderContent()}
        </div>
      </main>
    </div>
  );
}
