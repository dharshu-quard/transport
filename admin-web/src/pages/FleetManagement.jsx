import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Bus, Plus, Filter, CheckCircle, AlertTriangle, RefreshCw } from 'lucide-react';

export default function FleetManagement({ currentRole, lang }) {
  const [buses, setBuses] = useState([]);
  const [filterDepot, setFilterDepot] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newReg, setNewReg] = useState('');
  const [newType, setNewType] = useState('Express');
  const [newDepot, setNewDepot] = useState('Chennai Central Depot (CMBT)');

  useEffect(() => {
    fetchBuses();
  }, [filterDepot]);

  const fetchBuses = async () => {
    try {
      const data = await api.getBuses(filterDepot);
      setBuses(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpdateStatus = async (busId, newStatus) => {
    try {
      await api.updateBus(busId, { status: newStatus });
      fetchBuses();
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Bus className="h-6 w-6 text-emerald-400" />
            <span>{lang === 'ta' ? 'பேருந்து மேலாண்மை & பராமரிப்பு' : 'Fleet Inventory & Vehicle Health'}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time status management across 4 corporations depots (Chennai, Coimbatore, Madurai, Trichy).
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-md shadow-emerald-600/20"
          >
            <Plus className="h-4 w-4" />
            <span>{lang === 'ta' ? 'புதிய பேருந்து சேர்' : 'Register New Bus'}</span>
          </button>
        </div>
      </div>

      {/* Fleet Table */}
      <div className="glass-panel overflow-hidden border border-slate-800">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800 font-bold">
            <tr>
              <th className="py-3 px-4">Registration</th>
              <th className="py-3 px-4">Depot</th>
              <th className="py-3 px-4">Class</th>
              <th className="py-3 px-4">Fuel Type</th>
              <th className="py-3 px-4">Mileage</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-medium">
            {buses.map((b) => (
              <tr key={b.id} className="hover:bg-slate-900/50 transition-colors">
                <td className="py-3 px-4 font-mono font-bold text-white">{b.registration_number}</td>
                <td className="py-3 px-4 text-slate-300">{b.depot_name}</td>
                <td className="py-3 px-4 text-slate-300">{b.bus_type}</td>
                <td className="py-3 px-4 text-slate-400">{b.fuel_type}</td>
                <td className="py-3 px-4 font-mono text-slate-300">{Math.round(b.mileage_km).toLocaleString()} km</td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    b.status === 'active' ? 'badge-active' : b.status === 'maintenance' ? 'badge-warning' : b.status === 'breakdown' ? 'badge-danger' : 'badge-info'
                  }`}>
                    {b.status.toUpperCase()}
                  </span>
                </td>
                <td className="py-3 px-4 text-right space-x-2">
                  {b.status !== 'active' && (
                    <button
                      onClick={() => handleUpdateStatus(b.id, 'active')}
                      className="px-2 py-1 rounded bg-emerald-950 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-900 text-[10px] font-bold"
                    >
                      Set Active
                    </button>
                  )}
                  {b.status !== 'maintenance' && (
                    <button
                      onClick={() => handleUpdateStatus(b.id, 'maintenance')}
                      className="px-2 py-1 rounded bg-amber-950 border border-amber-500/40 text-amber-300 hover:bg-amber-900 text-[10px] font-bold"
                    >
                      Workshop
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
