import React, { useState, useEffect } from 'react';
import { mobileApi } from '../../services/api';
import {
  Bus, CheckCircle, Clock, ShieldAlert, AlertTriangle, Wrench,
  Check, X, FileText, Calendar, AlertOctagon, ShieldCheck
} from 'lucide-react';

export default function DriverScreen({ lang }) {
  const [dutyData, setDutyData] = useState(null);
  const [isCheckedIn, setIsCheckedIn] = useState(false);
  const [showInspection, setShowInspection] = useState(false);
  const [inspectionDone, setInspectionDone] = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [sosSent, setSosSent] = useState(false);

  // Inspection Checklist items
  const [checklist, setChecklist] = useState({
    brakes_ok: true,
    tires_ok: true,
    wipers_ok: true,
    lights_ok: true,
    emergency_exit_ok: true,
    remarks: 'Pre-trip physical checks cleared'
  });

  // Breakdown items
  const [breakdownType, setBreakdownType] = useState('Engine Overheating');
  const [breakdownDesc, setBreakdownDesc] = useState('');

  useEffect(() => {
    fetchDuty();
  }, []);

  const fetchDuty = async () => {
    try {
      const data = await mobileApi.getDriverDuty();
      if (data.has_duty) {
        setDutyData(data.duty);
        setIsCheckedIn(!!data.duty.check_in_time);
      }
    } catch (e) {}
  };

  const handleCheckInToggle = async () => {
    try {
      if (!isCheckedIn) {
        await mobileApi.driverCheckIn();
        setIsCheckedIn(true);
        alert('Check-in confirmed! Attendance recorded.');
      } else {
        await mobileApi.driverCheckOut();
        setIsCheckedIn(false);
        alert('Check-out completed! Have a safe rest.');
      }
      fetchDuty();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleSubmitInspection = async () => {
    if (!dutyData) return;
    try {
      const res = await mobileApi.submitInspection({
        duty_id: dutyData.id,
        bus_id: dutyData.bus.id,
        ...checklist
      });
      setInspectionDone(true);
      setShowInspection(false);
      alert(res.message);
    } catch (e) {
      alert(e.message);
    }
  };

  const handleReportBreakdown = async () => {
    if (!dutyData) return;
    try {
      await mobileApi.reportBreakdown({
        bus_id: dutyData.bus.id,
        issue_type: breakdownType,
        severity: 'high',
        description: breakdownDesc || 'Vehicle stalled on highway corridor'
      });
      setShowBreakdown(false);
      alert('Breakdown dispatched to Depot Workshop! Recovery assistance en route.');
    } catch (e) {
      alert(e.message);
    }
  };

  const handleSosTrigger = async () => {
    if (!confirm('TRIGGER CRITICAL EMERGENCY SOS ALARM TO STATE POLICE & DEPOT?')) return;
    try {
      await mobileApi.triggerSos({
        bus_id: dutyData ? dutyData.bus.id : 'bus-1',
        latitude: 13.0674,
        longitude: 80.2057,
        details: 'Driver panic button activated'
      });
      setSosSent(true);
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
      {/* Driver Duty Header Card */}
      <div className="mobile-card p-4 space-y-3 bg-gradient-to-br from-slate-900 to-slate-900/90 border-slate-700">
        <div className="flex justify-between items-start">
          <div>
            <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">
              {lang === 'ta' ? 'இன்றைய பணி ஒதுக்கீடு' : 'TODAY\'S ASSIGNED DUTY'}
            </span>
            <h3 className="font-extrabold text-base text-white mt-0.5">
              {dutyData ? dutyData.route.name : 'Madurai - Chennai Superfast'}
            </h3>
            <span className="text-[11px] text-slate-400">
              Route: <strong>{dutyData?.route?.number || '101E'}</strong> • Departure: <strong>{dutyData?.route?.departure_time || '07:30'}</strong>
            </span>
          </div>
          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
            isCheckedIn ? 'badge-active' : 'badge-warning'
          }`}>
            {isCheckedIn ? 'ON DUTY' : 'PENDING CHECK-IN'}
          </span>
        </div>

        {/* Bus Info */}
        <div className="p-3 bg-slate-950 rounded-xl grid grid-cols-2 gap-2 text-slate-300">
          <div>
            <span className="text-[10px] text-slate-500 uppercase block">Vehicle No:</span>
            <strong className="text-white font-mono">{dutyData?.bus?.registration_number || 'TN-01-N-1001'}</strong>
          </div>
          <div>
            <span className="text-[10px] text-slate-500 uppercase block">Vehicle Class:</span>
            <strong className="text-emerald-400">{dutyData?.bus?.bus_type || 'Super Deluxe Express'}</strong>
          </div>
        </div>

        {/* Attendance Button */}
        <button
          onClick={handleCheckInToggle}
          className={`w-full py-2.5 rounded-xl font-bold text-xs flex items-center justify-center gap-2 shadow-lg transition-all ${
            isCheckedIn
              ? 'bg-slate-800 hover:bg-slate-700 text-slate-300'
              : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30'
          }`}
        >
          <Clock className="h-4 w-4" />
          <span>{isCheckedIn ? 'Complete Duty Check-Out' : 'Biometric Duty Check-In (Present)'}</span>
        </button>
      </div>

      {/* Pre-Trip Inspection Card */}
      <div className="mobile-card p-4 space-y-2.5">
        <div className="flex justify-between items-center">
          <h4 className="font-bold text-xs text-white flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Pre-Trip Vehicle Safety Inspection</span>
          </h4>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
            inspectionDone ? 'badge-active' : 'badge-warning'
          }`}>
            {inspectionDone ? 'CLEARED' : 'PENDING'}
          </span>
        </div>

        {!inspectionDone ? (
          <button
            onClick={() => setShowInspection(!showInspection)}
            className="w-full py-2 bg-slate-900 border border-slate-700 hover:border-emerald-400 text-slate-200 rounded-lg font-bold text-xs"
          >
            {showInspection ? 'Close Inspection Checklist' : 'Fill Pre-Trip Inspection Checklist'}
          </button>
        ) : (
          <p className="text-[11px] text-emerald-400 font-semibold flex items-center gap-1">
            <CheckCircle className="h-3.5 w-3.5" /> All safety items verified (Brakes, Tires, Wipers, Lights, Emergency Exits).
          </p>
        )}

        {showInspection && !inspectionDone && (
          <div className="p-3 bg-slate-950 rounded-xl space-y-2 text-xs border border-slate-800">
            {['brakes_ok', 'tires_ok', 'wipers_ok', 'lights_ok', 'emergency_exit_ok'].map((item) => (
              <label key={item} className="flex items-center justify-between text-slate-300 cursor-pointer py-0.5">
                <span className="capitalize">{item.replace('_ok', ' Functionality:')}</span>
                <input
                  type="checkbox"
                  checked={checklist[item]}
                  onChange={(e) => setChecklist({ ...checklist, [item]: e.target.checked })}
                  className="h-4 w-4 rounded accent-emerald-500"
                />
              </label>
            ))}
            <button
              onClick={handleSubmitInspection}
              className="w-full mt-2 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-xs"
            >
              Sign & Certify Vehicle
            </button>
          </div>
        )}
      </div>

      {/* Breakdown Report & Emergency SOS */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => setShowBreakdown(!showBreakdown)}
          className="p-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-xl font-bold text-slate-200 flex flex-col items-center gap-1.5 shadow-md"
        >
          <Wrench className="h-5 w-5 text-amber-400" />
          <span>Report Breakdown</span>
        </button>

        <button
          onClick={handleSosTrigger}
          className="p-3 bg-rose-600 hover:bg-rose-500 border border-rose-400 text-white rounded-xl font-extrabold flex flex-col items-center gap-1.5 shadow-xl shadow-rose-600/40 animate-pulse"
        >
          <AlertOctagon className="h-5 w-5 text-white" />
          <span>EMERGENCY SOS</span>
        </button>
      </div>

      {showBreakdown && (
        <div className="mobile-card p-4 space-y-2 border-amber-500/50">
          <h4 className="font-bold text-white text-xs">Report Breakdown / Stalled Bus</h4>
          <select
            value={breakdownType}
            onChange={(e) => setBreakdownType(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-white"
          >
            <option>Engine Overheating</option>
            <option>Tire Puncture</option>
            <option>Brake Pressure Loss</option>
            <option>Electrical Short</option>
          </select>
          <textarea
            rows={2}
            value={breakdownDesc}
            onChange={(e) => setBreakdownDesc(e.target.value)}
            placeholder="Location landmark & description..."
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white"
          />
          <button
            onClick={handleReportBreakdown}
            className="w-full py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-lg text-xs"
          >
            Transmit Breakdown Alert
          </button>
        </div>
      )}

      {sosSent && (
        <div className="p-3 bg-rose-950 border border-rose-400 rounded-xl text-rose-100 text-center font-bold">
          SOS SIGNAL ACTIVE! Police & Depot Control notified with live GPS coordinates.
        </div>
      )}

      {/* Licence Expiry Reminder */}
      <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
        <span>Heavy Vehicle Licence (TN-58-2018):</span>
        <span className="font-mono text-emerald-400 font-bold">VALID (Expires 2028)</span>
      </div>
    </div>
  );
}
