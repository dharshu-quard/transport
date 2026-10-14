import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { ShieldCheck, Check, X, QrCode, FileText, UserCheck, Calendar } from 'lucide-react';

export default function PassReviewWorkflow({ currentRole, lang }) {
  const [applications, setApplications] = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);

  useEffect(() => {
    fetchApplications();
  }, [currentRole]);

  const fetchApplications = async () => {
    try {
      const data = await api.getPassApplications();
      setApplications(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDepotReview = async (appId, status) => {
    try {
      await api.reviewPassDepot(appId, status, 'Documents verified by Depot Superintendant');
      fetchApplications();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleAdminApprove = async (appId, status) => {
    try {
      await api.approvePassAdmin(appId, status, 'Approved by Transport Commissioner Office');
      fetchApplications();
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-emerald-400" />
            <span>{lang === 'ta' ? 'ஊழியர் & குடும்ப பயண அட்டை ஒப்புதல்' : 'Employee & Family Transit Pass Approval Workflow'}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Two-stage scrutiny: Depot Manager Review &rarr; State Admin Cryptographic QR Issuance.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {applications.map((app) => (
          <div key={app.id} className="glass-panel p-5 bg-slate-900/80 border-slate-800 space-y-3.5 text-xs">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] font-mono text-emerald-400 block font-bold">{app.employee_code}</span>
                <h4 className="font-bold text-sm text-white mt-0.5">{app.holder_name}</h4>
                <span className="text-[11px] text-slate-400 capitalize">Relationship: {app.relation_type}</span>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                app.status.includes('approved') ? 'badge-active' : app.status.includes('rejected') ? 'badge-danger' : 'badge-warning'
              }`}>
                {app.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>

            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 space-y-1 text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Validity Period:</span>
                <strong className="text-white">{app.period}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Application Type:</span>
                <strong className="text-emerald-400 capitalize">{app.pass_type} Pass</strong>
              </div>
            </div>

            {/* Action buttons according to status & role */}
            <div className="pt-2 border-t border-slate-800/80">
              {app.status === 'submitted' ? (
                <div className="space-y-1.5">
                  <span className="text-[10px] text-amber-300 block font-semibold">Stage 1: Depot Manager Review</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleDepotReview(app.id, 'depot_approved')}
                      className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold text-xs flex items-center justify-center gap-1 shadow-sm"
                    >
                      <Check className="h-3 w-3" /> Depot Approve
                    </button>
                    <button
                      onClick={() => handleDepotReview(app.id, 'depot_rejected')}
                      className="flex-1 py-1.5 bg-rose-950 border border-rose-500/40 text-rose-300 rounded font-bold text-xs flex items-center justify-center gap-1"
                    >
                      <X className="h-3 w-3" /> Reject
                    </button>
                  </div>
                </div>
              ) : app.status === 'depot_approved' ? (
                <div className="space-y-1.5">
                  <span className="text-[10px] text-cyan-300 block font-semibold">Stage 2: State Admin Final Issuance</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleAdminApprove(app.id, 'admin_approved')}
                      className="flex-1 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-bold text-xs flex items-center justify-center gap-1 shadow-sm"
                    >
                      <Check className="h-3 w-3" /> Issue Signed Pass
                    </button>
                    <button
                      onClick={() => handleAdminApprove(app.id, 'admin_rejected')}
                      className="flex-1 py-1.5 bg-rose-950 border border-rose-500/40 text-rose-300 rounded font-bold text-xs flex items-center justify-center gap-1"
                    >
                      <X className="h-3 w-3" /> Reject
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-2 rounded bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-center text-[11px] font-semibold flex items-center justify-center gap-1.5">
                  <QrCode className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Cryptographic QR Pass Officially Active</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
