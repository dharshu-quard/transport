import React from 'react';
import { Bus, ShieldCheck, MapPin, Sparkles, FileText, Users, Activity, Globe, CheckCircle } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, currentRole, setCurrentRole, lang, setLang }) {
  const navItems = [
    { id: 'fleet-map', labelEn: 'Live Fleet Map', labelTa: 'நேரலை பேருந்து வரைபடம்', icon: MapPin },
    { id: 'ai-insights', labelEn: 'AI Insights (8 Models)', labelTa: 'AI நுண்ணறிவு மையம்', icon: Sparkles, badge: 'Active' },
    { id: 'fleet-crud', labelEn: 'Fleet Management', labelTa: 'பேருந்து மேலாண்மை', icon: Bus },
    { id: 'operations', labelEn: 'Duty & Attendance', labelTa: 'பணி & வருகைப்பதிவு', icon: Users },
    { id: 'passes', labelEn: 'Pass Approvals', labelTa: 'பயண அட்டை ஒப்புதல்', icon: ShieldCheck },
    { id: 'reports', labelEn: 'Revenue & Reports', labelTa: 'வருவாய் அறிக்கைகள்', icon: FileText },
    { id: 'audits', labelEn: 'Audit Logs', labelTa: 'தணிக்கைப் பதிவுகள்', icon: Activity }
  ];

  const roles = [
    { id: 'admin', label: 'State Director (All Depots)' },
    { id: 'depot_manager_chn', label: 'Chennai Depot Manager' },
    { id: 'depot_manager_mdu', label: 'Madurai Depot Manager' },
    { id: 'depot_manager_cbe', label: 'Coimbatore Depot Manager' },
    { id: 'depot_manager_try', label: 'Trichy Depot Manager' }
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 bg-slate-950/85 backdrop-blur-xl px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
      {/* Brand Logo */}
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
          <Bus className="h-6 w-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
              TamilNadu Transit 360 <span className="text-emerald-400 font-extrabold text-xs px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-500/30">AI HUB</span>
            </h1>
          </div>
          <p className="text-xs text-slate-400 font-medium">TNSTC & MTC Intelligent State Transport Operations</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex items-center gap-1 overflow-x-auto py-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                isActive
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-500/10'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Icon className={`h-4 w-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
              <span>{lang === 'ta' ? item.labelTa : item.labelEn}</span>
              {item.badge && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-500/30 text-emerald-200 font-bold border border-emerald-400/30">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Controls: Role Switcher & Language Toggle */}
      <div className="flex items-center gap-3">
        {/* Language Toggle */}
        <button
          onClick={() => setLang(lang === 'en' ? 'ta' : 'en')}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-900 border border-slate-700 text-slate-200 hover:border-slate-500 transition-all shadow-sm"
          title="Toggle Language"
        >
          <Globe className="h-3.5 w-3.5 text-cyan-400" />
          <span>{lang === 'en' ? 'தமிழ்' : 'English'}</span>
        </button>

        {/* Role Scoping Dropdown */}
        <div className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-700 rounded-lg px-2.5 py-1 text-xs">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
          <select
            value={currentRole}
            onChange={(e) => setCurrentRole(e.target.value)}
            className="bg-transparent text-slate-200 font-semibold focus:outline-none cursor-pointer text-xs"
          >
            {roles.map((r) => (
              <option key={r.id} value={r.id} className="bg-slate-900 text-white">
                {r.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </header>
  );
}
