import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Users, Calendar, Check, X, CheckCircle, Clock, ShieldCheck } from 'lucide-react';

export default function OperationsRoster({ currentRole, lang }) {
  const [attendance, setAttendance] = useState([]);
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [activeTab, setActiveTab] = useState('attendance'); // attendance or leaves

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const att = await api.getAttendance();
      setAttendance(att);
      const lvs = await api.getLeaveRequests();
      setLeaveRequests(lvs);
    } catch (e) {
      console.error(e);
    }
  };

  const handleReviewLeave = async (reqId, status) => {
    try {
      await api.reviewLeaveRequest(reqId, status, `Reviewed by Depot Supervisor on ${new Date().toLocaleDateString()}`);
      fetchData();
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Users className="h-6 w-6 text-emerald-400" />
            <span>{lang === 'ta' ? 'பணி ஒதுக்கீடு & விடுப்பு ஒப்புதல்' : 'Duty Rostering, Attendance & Leave Approvals'}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Depot-scoped personnel management for Drivers, Conductors, and Maintenance staff.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('attendance')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'attendance' ? 'bg-emerald-600 text-white' : 'bg-slate-900 text-slate-300'
            }`}
          >
            {lang === 'ta' ? 'வருகைப்பதிவு' : 'Daily Attendance'}
          </button>
          <button
            onClick={() => setActiveTab('leaves')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'leaves' ? 'bg-emerald-600 text-white' : 'bg-slate-900 text-slate-300'
            }`}
          >
            {lang === 'ta' ? 'விடுப்பு கோரிக்கைகள்' : 'Pending Leaves'} ({leaveRequests.length})
          </button>
        </div>
      </div>

      {activeTab === 'attendance' ? (
        <div className="glass-panel overflow-hidden border border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800 font-bold">
              <tr>
                <th className="py-3 px-4">Staff Name</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Check-in</th>
                <th className="py-3 px-4">Check-out</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {attendance.map((a) => (
                <tr key={a.attendance_id} className="hover:bg-slate-900/50">
                  <td className="py-3 px-4 text-white font-semibold">{a.name}</td>
                  <td className="py-3 px-4 uppercase text-[10px] text-slate-400">{a.role}</td>
                  <td className="py-3 px-4 font-mono text-slate-400">{a.date}</td>
                  <td className="py-3 px-4 font-mono text-emerald-400">
                    {a.check_in ? new Date(a.check_in).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-400">
                    {a.check_out ? new Date(a.check_out).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'On Duty'}
                  </td>
                  <td className="py-3 px-4">
                    <span className="badge-active px-2 py-0.5 rounded text-[10px] font-bold">
                      {a.status.toUpperCase()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {leaveRequests.length === 0 ? (
            <div className="col-span-full py-12 text-center text-slate-500 text-xs">
              No pending leave applications for this depot.
            </div>
          ) : (
            leaveRequests.map((lr) => (
              <div key={lr.request_id} className="glass-panel p-4 bg-slate-900/80 border-slate-800 space-y-3 text-xs">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-bold text-white text-sm">{lr.employee_name}</h4>
                    <span className="text-[10px] text-emerald-400 uppercase font-semibold">{lr.leave_type} Leave</span>
                  </div>
                  <span className="badge-warning px-2 py-0.5 rounded text-[10px] font-bold">PENDING</span>
                </div>
                <div className="p-2.5 rounded bg-slate-950/80 border border-slate-800 text-[11px] text-slate-300">
                  <strong>Duration:</strong> {lr.start_date} to {lr.end_date}
                  <p className="mt-1 text-slate-400 italic">"{lr.reason}"</p>
                </div>
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => handleReviewLeave(lr.request_id, 'approved')}
                    className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold text-xs flex items-center justify-center gap-1 shadow-md"
                  >
                    <Check className="h-3.5 w-3.5" /> Approve
                  </button>
                  <button
                    onClick={() => handleReviewLeave(lr.request_id, 'rejected')}
                    className="flex-1 py-1.5 bg-rose-950 hover:bg-rose-900 text-rose-300 border border-rose-500/40 rounded font-bold text-xs flex items-center justify-center gap-1"
                  >
                    <X className="h-3.5 w-3.5" /> Reject
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
