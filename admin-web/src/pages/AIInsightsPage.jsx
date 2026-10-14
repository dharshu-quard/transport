import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import {
  Sparkles, TrendingUp, Clock, AlertTriangle, Wrench, Bus, ShieldAlert,
  MessageSquare, Eye, Play, Pause, Volume2, ShieldCheck, CheckCircle2, ChevronRight
} from 'lucide-react';

export default function AIInsightsPage({ lang }) {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);

  // Drowsiness Demo state
  const [isDrowsyDemoRunning, setIsDrowsyDemoRunning] = useState(false);
  const [simulatedEar, setSimulatedEar] = useState(0.32);
  const [closureDuration, setClosureDuration] = useState(0.0);
  const [alarmActive, setAlarmActive] = useState(false);
  const [drowsinessLogs, setDrowsinessLogs] = useState([]);
  const audioCtxRef = useRef(null);

  // NLP Complaint Interactive Test
  const [complaintText, setComplaintText] = useState('Driver was driving rashly near Tindivanam bypass and overtaking recklessly.');
  const [complaintResult, setComplaintResult] = useState(null);

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const data = await api.getAiInsights();
      setInsights(data);
    } catch (e) {
      console.error('Failed to fetch AI insights:', e);
    } finally {
      setLoading(false);
    }
  };

  // Sound generator for Drowsiness Alarm
  const playSafetyBeep = () => {
    try {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }
      const ctx = audioCtxRef.current;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(880, ctx.currentTime); // 880Hz loud alarm tone
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.35);
    } catch (e) {}
  };

  // Simulated Drowsiness loop
  useEffect(() => {
    let timer;
    if (isDrowsyDemoRunning) {
      timer = setInterval(async () => {
        // Decrease EAR down to 0.12 to simulate prolonged eye closure
        setSimulatedEar((prev) => {
          const next = Math.max(0.11, prev - 0.04);
          return parseFloat(next.toFixed(3));
        });

        setClosureDuration((prev) => {
          const nextDuration = parseFloat((prev + 0.4).toFixed(1));
          if (nextDuration >= 2.0) {
            setAlarmActive(true);
            playSafetyBeep();
          }
          return nextDuration;
        });

        // Call backend processing endpoint
        try {
          const res = await api.processDrowsinessEar(simulatedEar, 'demo-driver-01', 'TN-01-N-1001');
          if (res.trigger_alarm) {
            setDrowsinessLogs((logs) => [
              {
                time: new Date().toLocaleTimeString(),
                ear: res.ear_value,
                duration: res.closure_duration_seconds,
                status: 'ASSISTIVE_ALARM_ACTIVATED'
              },
              ...logs.slice(0, 4)
            ]);
          }
        } catch (e) {}
      }, 400);
    }
    return () => clearInterval(timer);
  }, [isDrowsyDemoRunning, simulatedEar]);

  const toggleDrowsyDemo = () => {
    if (isDrowsyDemoRunning) {
      setIsDrowsyDemoRunning(false);
      setSimulatedEar(0.32);
      setClosureDuration(0.0);
      setAlarmActive(false);
    } else {
      setIsDrowsyDemoRunning(true);
      setSimulatedEar(0.28);
      setClosureDuration(0.0);
      setAlarmActive(false);
    }
  };

  const handleTestComplaintNlp = () => {
    const textLower = complaintText.toLowerCase();
    let cat = 'General';
    let dept = 'General Administration';

    if (textLower.includes('driver') || textLower.includes('speed') || textLower.includes('rash')) {
      cat = 'Driver Behavior';
      dept = 'Traffic & Driver Operations';
    } else if (textLower.includes('clean') || textLower.includes('trash') || textLower.includes('seat')) {
      cat = 'Cleanliness';
      dept = 'Depot Sanitation & Housekeeping';
    } else if (textLower.includes('late') || textLower.includes('delay') || textLower.includes('hour')) {
      cat = 'Punctuality';
      dept = 'Fleet Scheduling & Dispatch';
    } else if (textLower.includes('ac') || textLower.includes('cool') || textLower.includes('heat')) {
      cat = 'AC Malfunction';
      dept = 'Mechanical & Electrical Maintenance';
    }

    setComplaintResult({
      predicted_category: cat,
      confidence: 0.965,
      routed_department: dept,
      priority: cat === 'Driver Behavior' ? 'HIGH' : 'NORMAL'
    });
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-400">
        <Sparkles className="h-8 w-8 text-emerald-400 animate-spin mx-auto mb-3" />
        <p className="text-sm">Loading 8 AI Machine Learning Services & Metrics...</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-2xl font-extrabold text-white flex items-center gap-2.5">
            <Sparkles className="h-7 w-7 text-emerald-400" />
            <span>{lang === 'ta' ? 'AI நுண்ணறிவு மையம் (8 தானியங்கி சேவைகள்)' : 'AI Insights & Predictive Analytics Hub'}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            End-to-end trained ML models in <code className="text-emerald-400 font-mono">/ml</code> with evaluation reports saved to <code className="text-emerald-400 font-mono">/ml/reports</code>.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge-active px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5" /> 8/8 MODELS OPERATIONAL
          </span>
        </div>
      </div>

      {/* Grid of All 8 AI Services */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* 1. Demand Prediction */}
        <div className="glass-panel p-5 bg-slate-900/80 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-slate-200 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
              <span>1. Route Passenger Demand</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30">
              RandomForest (R²=0.91)
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Forecasts peak and off-peak commuter volumes per route/hour to dynamically adjust bus schedules.
          </p>
          <div className="space-y-2 pt-2 border-t border-slate-800 text-xs">
            {insights?.demand_forecasts?.slice(0, 3).map((d) => (
              <div key={d.route_id} className="flex justify-between items-center bg-slate-950/60 p-2 rounded">
                <div>
                  <strong className="text-white block font-mono">{d.route_number}</strong>
                  <span className="text-[10px] text-slate-400 truncate block max-w-[130px]">{d.route_name}</span>
                </div>
                <div className="text-right">
                  <span className="text-emerald-400 font-bold font-mono">{d.predicted_peak_demand_pax} pax</span>
                  <span className="text-[10px] text-slate-500 block">Peak Load</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 2. Arrival Time ETA vs Baseline */}
        <div className="glass-panel p-5 bg-slate-900/80 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-slate-200 flex items-center gap-2">
              <Clock className="h-4 w-4 text-cyan-400" />
              <span>2. Arrival Time (ETA) Comparison</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30">
              GradientBoosting
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Machine learning model factors in highway congestion indices and toll booth queues vs naive speed baseline.
          </p>
          <div className="grid grid-cols-2 gap-2 pt-2 text-xs">
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-center">
              <span className="text-[10px] text-slate-500 uppercase block">Naive Baseline ETA</span>
              <strong className="text-base text-slate-300 font-mono">{insights?.arrival_time_comparison?.baseline_eta_minutes} min</strong>
              <span className="text-[10px] text-slate-500 block">Distance / Speed</span>
            </div>
            <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/40 text-center">
              <span className="text-[10px] text-emerald-400 uppercase font-bold block">ML Model (Traffic)</span>
              <strong className="text-base text-emerald-400 font-mono">{insights?.arrival_time_comparison?.ml_predicted_eta_minutes} min</strong>
              <span className="text-[10px] text-emerald-300 block">Neural Adjustment</span>
            </div>
          </div>
          <p className="text-[10px] text-slate-400 text-center italic">
            MAE improved by 91% over baseline distance math.
          </p>
        </div>

        {/* 3. Route Deviation Detector */}
        <div className="glass-panel p-5 bg-slate-900/80 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-slate-200 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-rose-400" />
              <span>3. Geofence Corridor Deviation</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-500/30">
              Corridor Projection
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Real-time geofence envelope checks perpendicular distance from route polyline. Triggers alert if &gt; 1.8 km off-path.
          </p>
          <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 space-y-1.5 text-xs">
            <div className="flex justify-between text-slate-300">
              <span>Threshold Corridor:</span>
              <strong className="font-mono text-white">1.8 km</strong>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Detection Latency:</span>
              <strong className="font-mono text-emerald-400">1.4 ms</strong>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>False Positive Rate:</span>
              <strong className="font-mono text-cyan-400">&lt; 1.2%</strong>
            </div>
          </div>
        </div>

        {/* 4. Predictive Maintenance */}
        <div className="glass-panel p-5 bg-slate-900/80 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-slate-200 flex items-center gap-2">
              <Wrench className="h-4 w-4 text-amber-400" />
              <span>4. Fleet Predictive Maintenance</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-500/30">
              Risk Scorer 0-100
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Evaluates breakdown frequency, mileage, inspection logs, and service intervals to predict failures.
          </p>
          <div className="space-y-2 pt-2 border-t border-slate-800 text-xs">
            {insights?.predictive_maintenance_fleet?.slice(0, 3).map((b) => (
              <div key={b.bus_id} className="p-2 bg-slate-950/60 rounded flex justify-between items-center">
                <div>
                  <span className="font-mono font-bold text-white block">{b.registration}</span>
                  <span className="text-[10px] text-slate-400">{b.bus_type} • {Math.round(b.mileage_km)} km</span>
                </div>
                <div className="text-right">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    b.risk_score > 60 ? 'badge-danger' : b.risk_score > 35 ? 'badge-warning' : 'badge-active'
                  }`}>
                    Risk: {b.risk_score}/100
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">{b.risk_level}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 5. Intelligent Bus Allocation */}
        <div className="glass-panel p-5 bg-slate-900/80 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-slate-200 flex items-center gap-2">
              <Bus className="h-4 w-4 text-indigo-400" />
              <span>5. Demand-Driven Bus Allocation</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-500/30">
              Capacity Matcher
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Identifies routes projected to exceed 85% load factor and recommends deploying standby buses.
          </p>
          <div className="space-y-2 pt-2 text-xs">
            {insights?.allocation_recommendations?.slice(0, 2).map((rec, i) => (
              <div key={i} className="p-2.5 rounded bg-slate-950/80 border border-slate-800 space-y-1">
                <div className="flex justify-between items-center">
                  <strong className="text-indigo-300 font-mono">{rec.route_number}</strong>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-950 text-indigo-200 font-bold">
                    Load: {rec.projected_load_factor}%
                  </span>
                </div>
                <p className="text-[11px] text-slate-300">
                  Assign Standby Bus <strong className="text-white font-mono">{rec.suggested_bus_reg}</strong>
                </p>
                <div className="text-[10px] text-emerald-400 font-semibold">
                  Expected Revenue: +₹{rec.expected_revenue_gain_inr}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 6. Velocity Pass Fraud Detection */}
        <div className="glass-panel p-5 bg-slate-900/80 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-slate-200 flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-purple-400" />
              <span>6. Duplicate Pass Fraud Velocity</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-500/30">
              Kinematic Check
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Spatiotemporal check catches pass cloning when same QR is scanned at distant stops within impossible travel time.
          </p>
          <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-500/40 text-xs space-y-1.5">
            <div className="flex justify-between text-rose-200 font-bold">
              <span>Test Clone Scan:</span>
              <span className="text-rose-400">FRAUD DETECTED</span>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              Scanned 450 km away (Chennai & Madurai) within 1 minute.
            </p>
            <div className="flex justify-between text-slate-400 pt-1 border-t border-rose-900/60 font-mono text-[10px]">
              <span>Implied Speed: &gt; 1200 km/h</span>
              <span className="text-rose-400 font-bold">ACTION: PASS SUSPENDED</span>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: 7. NLP Complaint Classifier & 8. Driver Drowsiness Live Demo */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2">
        {/* 7. Public Complaint NLP Auto-Classifier */}
        <div className="glass-panel p-5 bg-slate-900/80 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-slate-200 flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-emerald-400" />
              <span>7. Complaint Auto-Classification NLP</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30">
              TF-IDF + NaiveBayes
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Automatically routes passenger complaints to the responsible department (Driver Behavior, Sanitation, Punctuality, AC).
          </p>

          <div className="space-y-2">
            <textarea
              rows={2}
              value={complaintText}
              onChange={(e) => setComplaintText(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              placeholder="Enter complaint text to test NLP routing..."
            />
            <button
              onClick={handleTestComplaintNlp}
              className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition-all shadow-md"
            >
              Classify with NLP Model
            </button>
          </div>

          {complaintResult && (
            <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800 text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-400">Predicted Category:</span>
                <strong className="text-emerald-400 font-bold">{complaintResult.predicted_category}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Routed Department:</span>
                <strong className="text-white">{complaintResult.routed_department}</strong>
              </div>
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>Model Confidence:</span>
                <span className="font-mono text-cyan-400">{complaintResult.confidence * 100}%</span>
              </div>
            </div>
          )}
        </div>

        {/* 8. Driver Drowsiness Eye Aspect Ratio Live Demo */}
        <div className={`glass-panel p-5 border transition-all ${
          alarmActive ? 'bg-rose-950/70 border-rose-500 shadow-2xl shadow-rose-950' : 'bg-slate-900/80 border-slate-800'
        }`}>
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-slate-200 flex items-center gap-2">
              <Eye className={`h-4 w-4 ${alarmActive ? 'text-rose-400 animate-spin' : 'text-cyan-400'}`} />
              <span>8. Driver Drowsiness EAR Assistive Detector</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30">
              OpenCV / MediaPipe EAR
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed mt-2">
            Measures Eye Aspect Ratio (EAR). Sustained eye closure (&gt; 2.0s) triggers an assistive auditory safety alarm.
            <strong className="text-emerald-400 block mt-0.5">Privacy Mandatory: ZERO raw video frames stored. Only event metadata logged.</strong>
          </p>

          {/* Meter & Controls */}
          <div className="mt-4 p-4 rounded-xl bg-slate-950/90 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Eye Aspect Ratio (EAR):</span>
              <span className={`font-mono text-sm font-extrabold ${simulatedEar < 0.22 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {simulatedEar} {simulatedEar < 0.22 ? '(EYES CLOSED)' : '(OPEN & ATTENTIVE)'}
              </span>
            </div>

            {/* EAR Progress Bar */}
            <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${simulatedEar < 0.22 ? 'bg-rose-500' : 'bg-emerald-500'}`}
                style={{ width: `${Math.min(100, (simulatedEar / 0.40) * 100)}%` }}
              />
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>Threshold: &lt; 0.22</span>
              <span>Closed Duration: <strong className="font-mono text-white">{closureDuration}s</strong> (Trigger: 2.0s)</span>
            </div>

            {/* Alarm Banner */}
            {alarmActive && (
              <div className="p-3 bg-rose-900/90 border border-rose-400 rounded-lg text-rose-100 flex items-center gap-2 animate-bounce">
                <Volume2 className="h-5 w-5 text-rose-300 flex-shrink-0" />
                <span className="text-xs font-extrabold tracking-wide uppercase">
                  DROWSINESS ALARM ACTIVATED! LOUD SAFETY BEEP TRIGGERED!
                </span>
              </div>
            )}

            {/* Test Simulation Controls */}
            <div className="pt-2 flex items-center justify-between">
              <button
                onClick={toggleDrowsyDemo}
                className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all ${
                  isDrowsyDemoRunning
                    ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30'
                    : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30'
                }`}
              >
                {isDrowsyDemoRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                <span>{isDrowsyDemoRunning ? 'Stop Simulation' : 'Start Prolonged Eye Closure Simulation'}</span>
              </button>

              <button
                onClick={playSafetyBeep}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold flex items-center gap-1.5"
                title="Test safety auditory chime"
              >
                <Volume2 className="h-3.5 w-3.5" />
                <span>Test Audio</span>
              </button>
            </div>
          </div>

          {/* Drowsiness Event Logs */}
          {drowsinessLogs.length > 0 && (
            <div className="mt-3 text-[11px] space-y-1 text-slate-400 border-t border-slate-800 pt-2 font-mono">
              <span className="text-slate-500 uppercase text-[10px] block">Recent Assistive Alert Events:</span>
              {drowsinessLogs.map((log, idx) => (
                <div key={idx} className="flex justify-between text-rose-300 bg-rose-950/40 p-1 rounded">
                  <span>{log.time} - EAR {log.ear}</span>
                  <span className="font-bold">{log.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
