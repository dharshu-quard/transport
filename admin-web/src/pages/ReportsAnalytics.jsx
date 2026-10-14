import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { FileText, Download, DollarSign, TrendingUp, Users, ArrowUpRight, CheckCircle2 } from 'lucide-react';

export default function ReportsAnalytics({ lang }) {
  const [revenue, setRevenue] = useState(null);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const data = await api.getRevenueReports();
      setRevenue(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDownloadCsv = () => {
    const token = api.token;
    const url = `http://127.0.0.1:8000/api/admin/reports/export-csv${token ? `?token=${token}` : ''}`;
    window.open(url, '_blank');
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="h-6 w-6 text-emerald-400" />
            <span>{lang === 'ta' ? 'வருவாய் & பயண பகுப்பாய்வு' : 'Statewide Revenue & Booking Analytics'}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Operational cash flow, load factors, and one-click regulatory CSV audits.
          </p>
        </div>
        <button
          onClick={handleDownloadCsv}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold flex items-center gap-2 shadow-lg shadow-emerald-600/20"
        >
          <Download className="h-4 w-4" />
          <span>{lang === 'ta' ? 'CSV அறிக்கை பதிவிறக்கு' : 'Export Bookings CSV'}</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4 bg-slate-900/80 border-slate-800 space-y-1">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">Total Gross Collection</span>
          <div className="text-2xl font-extrabold font-mono text-white">
            ₹{revenue?.total_revenue_inr?.toLocaleString() || '48,250'}
          </div>
          <span className="text-[10px] text-emerald-400 font-semibold flex items-center gap-1">
            <ArrowUpRight className="h-3 w-3" /> +14.8% vs last month
          </span>
        </div>

        <div className="glass-panel p-4 bg-slate-900/80 border-slate-800 space-y-1">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">Confirmed Bookings</span>
          <div className="text-2xl font-extrabold font-mono text-white">
            {revenue?.total_confirmed_bookings?.toLocaleString() || '120'}
          </div>
          <span className="text-[10px] text-cyan-400 font-semibold">Online & Mobile App</span>
        </div>

        <div className="glass-panel p-4 bg-slate-900/80 border-slate-800 space-y-1">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">Fleet Utilization</span>
          <div className="text-2xl font-extrabold font-mono text-emerald-400">
            {revenue?.fleet_utilization_rate || '84.2%'}
          </div>
          <span className="text-[10px] text-slate-400">60 Buses operating</span>
        </div>

        <div className="glass-panel p-4 bg-slate-900/80 border-slate-800 space-y-1">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">Daily Commuters</span>
          <div className="text-2xl font-extrabold font-mono text-cyan-400">
            {revenue?.daily_passengers_served?.toLocaleString() || '18,450'}
          </div>
          <span className="text-[10px] text-slate-400">Across 20 intercity routes</span>
        </div>
      </div>
    </div>
  );
}
