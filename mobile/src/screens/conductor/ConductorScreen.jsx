import React, { useState, useEffect } from 'react';
import { mobileApi } from '../../services/api';
import {
  QrCode, Check, X, AlertTriangle, Users, DollarSign,
  Plus, CheckCircle2, ShieldAlert, Sparkles, Printer
} from 'lucide-react';

export default function ConductorScreen({ lang }) {
  const [activeSubTab, setActiveSubTab] = useState('scan'); // scan, issue, count, reconcile
  const [qrInput, setQrInput] = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Spot ticketing
  const [passengerName, setPassengerName] = useState('Ravi Kumar');
  const [fromStop, setFromStop] = useState('');
  const [toStop, setToStop] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [issuedTicket, setIssuedTicket] = useState(null);
  const [stops, setStops] = useState([]);

  // Counter & Reconciliation
  const [paxCount, setPaxCount] = useState(null);
  const [reconciliation, setReconciliation] = useState(null);

  useEffect(() => {
    fetchInitial();
  }, []);

  const fetchInitial = async () => {
    try {
      const st = await mobileApi.getStops();
      setStops(st);
      if (st.length >= 2) {
        setFromStop(st[0].id);
        setToStop(st[1].id);
      }
      fetchRecon();
    } catch (e) {}
  };

  const fetchRecon = async () => {
    try {
      const rec = await mobileApi.getReconciliation();
      setReconciliation(rec);
    } catch (e) {}
  };

  const handleValidateQr = async (overrideStr = null) => {
    const stringToTest = overrideStr || qrInput;
    if (!stringToTest) {
      alert('Please enter or paste QR code data.');
      return;
    }
    setLoading(true);
    setScanResult(null);
    try {
      const res = await mobileApi.validateQr(stringToTest);
      setScanResult(res);
      fetchRecon();
    } catch (e) {
      setScanResult({ valid: false, error_type: 'ERROR', message: e.message });
    } finally {
      setLoading(false);
    }
  };

  // Preset sample QR tests for effortless testing of acceptance check 3
  const testPreset = (type) => {
    if (type === 'valid') {
      // Pick first valid ticket from history or test payload
      const validSample = JSON.stringify({
        data: { v: 1, type: "TICKET", tid: "demo-valid-t1", ref: "TNK-DEMO", trip: "t1", pax: "Dharshini Siva", seat: 14, fare: 120.0, iat: 1713000000 },
        sig: "c018258e727e4693a9fa186d953a78044ce4a64d0b1784d168560124ad99f0bb"
      });
      setQrInput(validSample);
      handleValidateQr(validSample);
    } else if (type === 'forged') {
      const forgedSample = JSON.stringify({
        data: { v: 1, type: "TICKET", tid: "demo-fake", ref: "TNK-FAKE", trip: "t1", pax: "Malicious Hacker", seat: 1, fare: 0.0, iat: 1713000000 },
        sig: "fake_tampered_signature_invalid_hash_123456"
      });
      setQrInput(forgedSample);
      handleValidateQr(forgedSample);
    }
  };

  const handleIssueSpotTicket = async () => {
    try {
      // Find active trip or mock trip
      const fleet = await mobileApi.getLiveFleet();
      const inTransit = fleet.find((b) => b.is_in_transit) || fleet[0];
      if (!inTransit || !inTransit.current_trip_id) {
        alert('No active trip available to issue on-bus ticket.');
        return;
      }
      const res = await mobileApi.issueSpotTicket({
        trip_id: inTransit.current_trip_id,
        from_stop_id: fromStop,
        to_stop_id: toStop,
        passenger_name: passengerName,
        payment_method: paymentMethod
      });
      setIssuedTicket(res);
      fetchRecon();
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden">
      {/* Sub-nav */}
      <div className="flex items-center justify-around bg-slate-900 border-b border-slate-800 p-2 text-xs font-bold">
        <button
          onClick={() => setActiveSubTab('scan')}
          className={`py-1.5 px-3 rounded-lg ${activeSubTab === 'scan' ? 'bg-emerald-600 text-white' : 'text-slate-400'}`}
        >
          Scan QR Ticket
        </button>
        <button
          onClick={() => setActiveSubTab('issue')}
          className={`py-1.5 px-3 rounded-lg ${activeSubTab === 'issue' ? 'bg-emerald-600 text-white' : 'text-slate-400'}`}
        >
          Spot Ticketing
        </button>
        <button
          onClick={() => setActiveSubTab('reconcile')}
          className={`py-1.5 px-3 rounded-lg ${activeSubTab === 'reconcile' ? 'bg-emerald-600 text-white' : 'text-slate-400'}`}
        >
          Daily Cash Recon
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {/* SUBTAB 1: QR SCANNER & FORGERY CHECK */}
        {activeSubTab === 'scan' && (
          <div className="space-y-3">
            <div className="mobile-card p-4 space-y-3">
              <h3 className="font-bold text-white text-xs flex items-center gap-1.5">
                <QrCode className="h-4 w-4 text-emerald-400" />
                <span>Validate Commuter QR Ticket</span>
              </h3>
              <p className="text-[11px] text-slate-400">
                Cryptographically verifies HMAC signature. Rejects forged, cancelled, or duplicate scans.
              </p>

              {/* QR Payload Textarea */}
              <textarea
                rows={3}
                value={qrInput}
                onChange={(e) => setQrInput(e.target.value)}
                placeholder="Paste scanned QR JSON string or use quick presets below..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-[11px] font-mono text-white focus:outline-none focus:border-emerald-500"
              />

              {/* Test Buttons */}
              <div className="space-y-1.5 pt-1">
                <span className="text-[10px] text-slate-500 uppercase block font-bold">Quick Validation Presets:</span>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => testPreset('valid')}
                    className="py-1.5 px-2 bg-emerald-950 hover:bg-emerald-900 border border-emerald-500/40 text-emerald-300 rounded font-bold text-[11px]"
                  >
                    Test Valid QR Ticket
                  </button>
                  <button
                    onClick={() => testPreset('forged')}
                    className="py-1.5 px-2 bg-rose-950 hover:bg-rose-900 border border-rose-500/40 text-rose-300 rounded font-bold text-[11px]"
                  >
                    Test Forged QR (Fake)
                  </button>
                </div>
              </div>

              <button
                onClick={() => handleValidateQr()}
                disabled={loading}
                className="w-full mt-2 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-xs shadow-md shadow-emerald-600/30"
              >
                {loading ? 'Verifying HMAC Signature...' : 'Validate Scanned QR Code'}
              </button>
            </div>

            {/* Verification Verdict Banner */}
            {scanResult && (
              <div className={`mobile-card p-4 border text-xs space-y-2 ${
                scanResult.valid ? 'bg-emerald-950/70 border-emerald-500 text-emerald-200' : 'bg-rose-950/80 border-rose-500 text-rose-200'
              }`}>
                <div className="flex items-center gap-2">
                  {scanResult.valid ? <CheckCircle2 className="h-5 w-5 text-emerald-400" /> : <ShieldAlert className="h-5 w-5 text-rose-400" />}
                  <span className="font-extrabold text-sm uppercase tracking-wider">
                    {scanResult.valid ? 'TICKET VERIFIED & BOARDED' : 'SCAN REJECTED'}
                  </span>
                </div>

                <p className="font-medium text-[11px]">{scanResult.message}</p>

                {scanResult.ticket && (
                  <div className="p-2.5 bg-slate-950 rounded-lg font-mono text-[11px] space-y-0.5">
                    <div>Passenger: <strong>{scanResult.ticket.passenger_name}</strong></div>
                    <div>Seat: <strong>{scanResult.ticket.seat_number}</strong> | Status: <strong>{scanResult.ticket.status}</strong></div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* SUBTAB 2: SPOT DIGITAL TICKETING */}
        {activeSubTab === 'issue' && (
          <div className="space-y-3">
            <div className="mobile-card p-4 space-y-3">
              <h3 className="font-bold text-white text-xs flex items-center gap-1.5">
                <Printer className="h-4 w-4 text-emerald-400" />
                <span>Issue Spot Digital Ticket (On-Bus)</span>
              </h3>

              <div className="space-y-2 text-xs">
                <div>
                  <label className="text-[10px] text-slate-400 block mb-0.5">Passenger Name:</label>
                  <input
                    type="text"
                    value={passengerName}
                    onChange={(e) => setPassengerName(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-white"
                  />
                </div>

                <div>
                  <label className="text-[10px] text-slate-400 block mb-0.5">Boarding Stop:</label>
                  <select
                    value={fromStop}
                    onChange={(e) => setFromStop(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-white"
                  >
                    {stops.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[10px] text-slate-400 block mb-0.5">Alighting Stop:</label>
                  <select
                    value={toStop}
                    onChange={(e) => setToStop(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-white"
                  >
                    {stops.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[10px] text-slate-400 block mb-0.5">Payment Method:</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => setPaymentMethod('cash')}
                      className={`py-2 rounded-lg font-bold text-xs ${paymentMethod === 'cash' ? 'bg-emerald-600 text-white' : 'bg-slate-900 text-slate-400'}`}
                    >
                      Cash (Physical)
                    </button>
                    <button
                      onClick={() => setPaymentMethod('upi')}
                      className={`py-2 rounded-lg font-bold text-xs ${paymentMethod === 'upi' ? 'bg-emerald-600 text-white' : 'bg-slate-900 text-slate-400'}`}
                    >
                      QR UPI Digital
                    </button>
                  </div>
                </div>

                <button
                  onClick={handleIssueSpotTicket}
                  className="w-full mt-2 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-xs shadow-md shadow-emerald-600/30"
                >
                  Print & Issue Ticket (Auto Stage Fare)
                </button>
              </div>
            </div>

            {issuedTicket && (
              <div className="mobile-card p-4 bg-emerald-950/60 border-emerald-500 text-xs space-y-2">
                <div className="flex items-center gap-2 text-emerald-300 font-bold">
                  <Check className="h-4 w-4" />
                  <span>Ticket Issued & Added to Daily Collection</span>
                </div>
                <div className="p-2.5 bg-slate-950 rounded-lg font-mono space-y-0.5 text-[11px]">
                  <div>Ref: <strong className="text-white">{issuedTicket.booking_reference}</strong></div>
                  <div>Seat: <strong className="text-emerald-400">{issuedTicket.seat_number}</strong> | Fare: ₹{issuedTicket.fare} ({issuedTicket.payment_method.toUpperCase()})</div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* SUBTAB 3: DAILY CASH RECONCILIATION */}
        {activeSubTab === 'reconcile' && (
          <div className="space-y-3">
            <div className="mobile-card p-4 space-y-3">
              <h3 className="font-bold text-white text-xs flex items-center gap-1.5">
                <DollarSign className="h-4 w-4 text-emerald-400" />
                <span>Daily Collection Summary & Reconciliation</span>
              </h3>
              <p className="text-[11px] text-slate-400">
                Audits physical cash collected on-bus vs digital UPI payments for end-of-shift depot remittance.
              </p>

              {reconciliation ? (
                <div className="space-y-2.5 text-xs">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase block font-semibold">Cash Collected</span>
                      <strong className="text-base text-emerald-400 font-mono">₹{reconciliation.cash_collection_inr}</strong>
                      <span className="text-[10px] text-slate-500 block">{reconciliation.cash_tickets_count} tickets</span>
                    </div>

                    <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">Digital (UPI/App)</span>
                      <strong className="text-base text-cyan-400 font-mono">₹{reconciliation.digital_collection_inr}</strong>
                      <span className="text-[10px] text-slate-500 block">{reconciliation.digital_tickets_count} tickets</span>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-900 rounded-xl border border-slate-700 flex justify-between items-center">
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Grand Total Collection:</span>
                      <span className="text-base font-extrabold text-white font-mono">₹{reconciliation.grand_total_collection_inr}</span>
                    </div>
                    <span className="badge-active px-2.5 py-1 rounded text-[10px] font-bold">
                      {reconciliation.status}
                    </span>
                  </div>

                  <div className="p-2.5 bg-amber-950/40 border border-amber-500/30 rounded-lg text-amber-200 text-[11px]">
                    <strong>Depot Cash Remittance:</strong> Hand over ₹{reconciliation.remittance_due_at_depot_cashier} physical cash at end of shift.
                  </div>
                </div>
              ) : (
                <div className="py-6 text-center text-slate-500 text-xs">Loading collection data...</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
