import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Activity, ShieldCheck, Filter, Clock, User, Terminal } from 'lucide-react';

export default function AuditLogViewer({ currentRole, lang }) {
  const [logs, setLogs] = useState([]);
  const [filterAction, setFilterAction] = useState('');

  useEffect(() => {
    fetchLogs();
  }, [filterAction]);

  const fetchLogs = async () => {
    try {
      const data = await api.getAuditLogs(filterAction);
      setLogs(data);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Activity className="h-6 w-6 text-emerald-400" />
            <span>{lang === 'ta' ? 'அமைப்பு தணிக்கைப் பதிவுகள்' : 'Administrative Mutation Audit Trails'}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Cryptographically tracked audit logs for all administrative actions (who, what, when, old/new diff).
          </p>
        </div>
      </div>

      <div className="glass-panel overflow-hidden border border-slate-800">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800 font-bold">
            <tr>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">Action</th>
              <th className="py-3 px-4">Entity</th>
              <th className="py-3 px-4">Operator</th>
              <th className="py-3 px-4">Role</th>
              <th className="py-3 px-4">Audit Payload (Diff)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-medium">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-slate-900/50">
                <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                  {new Date(log.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'medium' })}
                </td>
                <td className="py-3 px-4">
                  <span className="font-mono text-emerald-300 font-bold text-[11px] px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/30">
                    {log.action}
                  </span>
                </td>
                <td className="py-3 px-4 text-slate-300">{log.entity_name}</td>
                <td className="py-3 px-4 text-white font-semibold">{log.performed_by}</td>
                <td className="py-3 px-4 uppercase text-[10px] text-slate-400">{log.role || 'system'}</td>
                <td className="py-3 px-4 max-w-xs font-mono text-[10px] text-slate-400 truncate">
                  {log.new_values ? JSON.stringify(log.new_values) : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
