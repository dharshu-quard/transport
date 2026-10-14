import React, { useState, useEffect, useRef } from 'react';
import { mobileApi } from '../../services/api';
import {
  Search, Bus, QrCode, MapPin, Bell, AlertTriangle, ArrowRight, Check,
  Sparkles, ShieldCheck, Clock, RefreshCw, X, Play, RotateCcw, Volume2
} from 'lucide-react';

export default function PassengerScreen({ lang }) {
  const [subTab, setSubTab] = useState('book'); // book, tickets, tracking, autopilot
  const [stops, setStops] = useState([]);
  const [fromStop, setFromStop] = useState('');
  const [toStop, setToStop] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [seatMap, setSeatMap] = useState(null);
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [paxName, setPaxName] = useState('Dharshini Siva');
  const [bookingSuccess, setBookingSuccess] = useState(null);
  const [myTickets, setMyTickets] = useState([]);
  const [viewingQrTicket, setViewingQrTicket] = useState(null);

  // Safety & Alerts
  const [destinationAlertActive, setDestinationAlertActive] = useState(false);
  const [missedStopAlarmActive, setMissedStopAlarmActive] = useState(false);
  const [wrongBusModal, setWrongBusModal] = useState(null);
  const [boardedBusInput, setBoardedBusInput] = useState('TN-45-N-9999');

  // Autopilot
  const [autopilotPlan, setAutopilotPlan] = useState(null);
  const [consentModal, setConsentModal] = useState(false);
  const [autoRoute, setAutoRoute] = useState('');

  const audioCtxRef = useRef(null);

  useEffect(() => {
    fetchStops();
    fetchHistory();
    fetchAutopilot();
  }, []);

  const fetchStops = async () => {
    try {
      const data = await mobileApi.getStops();
      setStops(data);
      if (data.length >= 2) {
        setFromStop(data[0].id);
        setToStop(data[data.length - 1].id);
      }
    } catch (e) {}
  };

  const fetchHistory = async () => {
    try {
      const data = await mobileApi.getBookingHistory();
      setMyTickets(data);
    } catch (e) {}
  };

  const fetchAutopilot = async () => {
    try {
      const data = await mobileApi.getAutopilotPlan();
      setAutopilotPlan(data.plan);
    } catch (e) {}
  };

  const handleSearch = async () => {
    if (!fromStop || !toStop) return;
    try {
      const results = await mobileApi.searchRoutes(fromStop, toStop);
      setSearchResults(results);
    } catch (e) {
      alert(e.message);
    }
  };

  const handleSelectTrip = async (trip, routeInfo) => {
    setSelectedTrip({ ...trip, routeInfo });
    setSelectedSeat(null);
    try {
      const map = await mobileApi.getSeatMap(trip.trip_id);
      setSeatMap(map);
    } catch (e) {}
  };

  const handleConfirmBooking = async () => {
    if (!selectedTrip || !selectedSeat) {
      alert('Please select a seat');
      return;
    }
    try {
      const res = await mobileApi.bookTicket(
        selectedTrip.trip_id,
        fromStop,
        toStop,
        paxName,
        selectedSeat,
        'upi'
      );
      setBookingSuccess(res);
      setSelectedTrip(null);
      setSeatMap(null);
      fetchHistory();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleCancelBooking = async (bId) => {
    if (!confirm('Are you sure you want to cancel? Refund will be calculated based on transit rules.')) return;
    try {
      const res = await mobileApi.cancelBooking(bId, 'Passenger cancelled via mobile app');
      alert(`Cancelled! Refund of ₹${res.refund_amount} (${res.refund_percentage}%) processed.`);
      fetchHistory();
    } catch (e) {
      alert(e.message);
    }
  };

  // Sound generator
  const playAlertSound = (freq = 440, duration = 0.4) => {
    try {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }
      const ctx = audioCtxRef.current;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch (e) {}
  };

  // Destination Alert simulation
  const simulateDestinationApproaching = () => {
    setDestinationAlertActive(true);
    setMissedStopAlarmActive(false);
    playAlertSound(587, 0.5); // Pleasant chime

    // Voice alert simulation via SpeechSynthesis
    if ('speechSynthesis' in window) {
      const text = lang === 'ta'
        ? 'கவனம்! உங்கள் இலக்கு பேருந்து நிறுத்தம் 500 மீட்டருக்குள் வரவுள்ளது.'
        : 'Attention! Your destination stop is approaching within 500 meters.';
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = lang === 'ta' ? 'ta-IN' : 'en-US';
      window.speechSynthesis.speak(utter);
    }
  };

  const simulateMissedStopAlarm = () => {
    setMissedStopAlarmActive(true);
    setDestinationAlertActive(false);
    playAlertSound(880, 0.8); // Loud urgent chime

    if ('speechSynthesis' in window) {
      const text = lang === 'ta'
        ? 'எச்சரிக்கை! நீங்கள் உங்கள் இறங்கும் நிறுத்தத்தைத் தாண்டிவிட்டீர்கள்!'
        : 'ALERT! You have passed your destination stop!';
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = lang === 'ta' ? 'ta-IN' : 'en-US';
      window.speechSynthesis.speak(utter);
    }
  };

  const handleWrongBusCheck = async () => {
    if (!myTickets.length) {
      alert('Please book a ticket first to test wrong bus validation.');
      return;
    }
    const ticketId = myTickets[0].ticket_id;
    try {
      const res = await mobileApi.validateBoardedBus(ticketId, boardedBusInput);
      setWrongBusModal(res);
    } catch (e) {
      alert(e.message);
    }
  };

  const handleAutopilotConsentSubmit = async () => {
    try {
      const res = await mobileApi.createAutopilotPlan({
        route_id: autoRoute || (stops[0] ? stops[0].id : 'r-1'),
        preferred_time_start: '07:30',
        preferred_time_end: '09:00',
        days_of_week: [1, 2, 3, 4, 5],
        max_fare_limit: 150.0,
        max_monthly_bookings: 22,
        consent_given: true
      });
      setConsentModal(false);
      fetchAutopilot();
      alert('Autopilot Activated with explicit consent!');
    } catch (e) {
      alert(e.message);
    }
  };

  const handleTriggerAutopilotNow = async () => {
    try {
      const res = await mobileApi.triggerAutopilotCron();
      alert(`Autopilot executed! Booked: ${res.booked}, Skipped: ${res.skipped}`);
      fetchHistory();
      fetchAutopilot();
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden">
      {/* Sub-nav header */}
      <div className="flex items-center justify-around bg-slate-900 border-b border-slate-800 p-2 text-xs font-bold">
        <button
          onClick={() => setSubTab('book')}
          className={`py-1.5 px-3 rounded-lg ${subTab === 'book' ? 'bg-emerald-600 text-white' : 'text-slate-400'}`}
        >
          {lang === 'ta' ? 'முன்பதிவு' : 'Book Ticket'}
        </button>
        <button
          onClick={() => setSubTab('tickets')}
          className={`py-1.5 px-3 rounded-lg ${subTab === 'tickets' ? 'bg-emerald-600 text-white' : 'text-slate-400'}`}
        >
          {lang === 'ta' ? 'பயணச்சீட்டுகள்' : 'My Tickets'} ({myTickets.length})
        </button>
        <button
          onClick={() => setSubTab('safety')}
          className={`py-1.5 px-3 rounded-lg ${subTab === 'safety' ? 'bg-emerald-600 text-white' : 'text-slate-400'}`}
        >
          {lang === 'ta' ? 'பயண பாதுகாப்பு' : 'Safety Alarms'}
        </button>
        <button
          onClick={() => setSubTab('autopilot')}
          className={`py-1.5 px-3 rounded-lg flex items-center gap-1 ${subTab === 'autopilot' ? 'bg-emerald-600 text-white' : 'text-slate-400'}`}
        >
          <Sparkles className="h-3 w-3 text-emerald-400" />
          <span>{lang === 'ta' ? 'தானியங்கி' : 'Autopilot'}</span>
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* TAB 1: BOOKING FLOW */}
        {subTab === 'book' && (
          <>
            {/* Search Box */}
            <div className="mobile-card p-4 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                <Search className="h-3.5 w-3.5" />
                <span>{lang === 'ta' ? 'வழித்தடம் தேடல்' : 'Search Tamil Nadu Buses'}</span>
              </h3>

              <div className="space-y-2 text-xs">
                <div>
                  <label className="text-[10px] text-slate-400 block mb-0.5">{lang === 'ta' ? 'புறப்படும் இடம்' : 'Origin Stop'}</label>
                  <select
                    value={fromStop}
                    onChange={(e) => setFromStop(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-white"
                  >
                    {stops.map((s) => (
                      <option key={s.id} value={s.id}>
                        {lang === 'ta' ? s.name_ta : s.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[10px] text-slate-400 block mb-0.5">{lang === 'ta' ? 'சேருமிடம்' : 'Destination Stop'}</label>
                  <select
                    value={toStop}
                    onChange={(e) => setToStop(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-white"
                  >
                    {stops.map((s) => (
                      <option key={s.id} value={s.id}>
                        {lang === 'ta' ? s.name_ta : s.name}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={handleSearch}
                  className="w-full mt-2 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-xs flex items-center justify-center gap-1.5 shadow-md shadow-emerald-600/30"
                >
                  <Search className="h-3.5 w-3.5" />
                  <span>{lang === 'ta' ? 'பேருந்துகளைக் காண்க' : 'Find Available Buses'}</span>
                </button>
              </div>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-300">
                  {lang === 'ta' ? 'கிடைக்கும் வழித்தடங்கள்' : 'Available Services'} ({searchResults.length})
                </h4>

                {searchResults.map((r) => (
                  <div key={r.route_id} className="mobile-card p-3 space-y-2 text-xs">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="font-mono text-emerald-400 font-bold">{r.route_number}</span>
                        <h5 className="font-bold text-white text-xs mt-0.5">{r.route_name}</h5>
                        <span className="text-[10px] text-slate-400">{r.distance_km} km • ~{r.estimated_mins} mins</span>
                      </div>
                      <span className="text-base font-extrabold font-mono text-emerald-400">₹{r.fare_inr}</span>
                    </div>

                    {/* Trips List */}
                    <div className="space-y-1.5 pt-1 border-t border-slate-800">
                      {r.trips.map((t) => (
                        <div key={t.trip_id} className="flex justify-between items-center bg-slate-900/90 p-2 rounded-lg">
                          <div>
                            <span className="font-mono text-white font-bold">{t.departure_time}</span>
                            <span className="text-[10px] text-slate-400 ml-2">{t.bus_type}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold text-cyan-400 font-mono">
                              {t.available_seats} seats left
                            </span>
                            <button
                              onClick={() => handleSelectTrip(t, r)}
                              className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold text-[11px]"
                            >
                              Select Seat
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Seat Map Modal / Section */}
            {seatMap && (
              <div className="mobile-card p-4 space-y-3 border-emerald-500/50">
                <div className="flex justify-between items-center">
                  <h4 className="font-bold text-xs text-white">
                    Select Seat ({seatMap.bus_registration} • {seatMap.bus_type})
                  </h4>
                  <button onClick={() => setSeatMap(null)} className="text-slate-400 hover:text-white">
                    <X className="h-4 w-4" />
                  </button>
                </div>

                {/* Seat Map Grid (40 seats layout: 2x2 with aisle) */}
                <div className="p-3 bg-slate-950 rounded-xl max-h-56 overflow-y-auto">
                  <div className="grid grid-cols-4 gap-2 text-center text-xs">
                    {seatMap.seats.slice(0, 32).map((s) => {
                      const isSelected = selectedSeat === s.seat_number;
                      return (
                        <button
                          key={s.seat_number}
                          disabled={!s.is_available}
                          onClick={() => setSelectedSeat(s.seat_number)}
                          className={`py-2 rounded-lg font-mono font-bold text-xs transition-all ${
                            !s.is_available
                              ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
                              : isSelected
                              ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/40'
                              : 'bg-slate-900 border border-slate-700 text-slate-200 hover:border-emerald-400'
                          }`}
                        >
                          {s.seat_number}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                  <span>Selected Seat: <strong className="text-emerald-400 font-mono">{selectedSeat || 'None'}</strong></span>
                  <span>Fare: <strong className="text-white font-mono">₹{selectedTrip.routeInfo.fare_inr}</strong></span>
                </div>

                <button
                  disabled={!selectedSeat}
                  onClick={handleConfirmBooking}
                  className={`w-full py-2.5 rounded-lg text-xs font-bold shadow-lg ${
                    selectedSeat ? 'bg-emerald-600 hover:bg-emerald-500 text-white' : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  }`}
                >
                  Pay ₹{selectedTrip.routeInfo.fare_inr} via Mock UPI & Confirm Ticket
                </button>
              </div>
            )}

            {/* Booking Confirmed Popup */}
            {bookingSuccess && (
              <div className="mobile-card p-4 bg-emerald-950/60 border-emerald-500/80 text-xs space-y-2">
                <div className="flex items-center gap-2 text-emerald-300 font-bold">
                  <Check className="h-4 w-4" />
                  <span>Ticket Booked Successfully!</span>
                </div>
                <div className="p-2.5 bg-slate-950 rounded-lg font-mono space-y-1">
                  <div>Ref: <strong className="text-white">{bookingSuccess.booking_reference}</strong></div>
                  <div>Seat: <strong className="text-emerald-400">{bookingSuccess.seat_number}</strong> | Fare: ₹{bookingSuccess.total_fare}</div>
                </div>
                <button
                  onClick={() => {
                    setViewingQrTicket(bookingSuccess);
                    setBookingSuccess(null);
                    setSubTab('tickets');
                  }}
                  className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold text-xs"
                >
                  View Offline HMAC QR Ticket
                </button>
              </div>
            )}
          </>
        )}

        {/* TAB 2: MY TICKETS & OFFLINE HMAC QR */}
        {subTab === 'tickets' && (
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-slate-300">
              {lang === 'ta' ? 'எனது முன்பதிவுகள்' : 'My Journey Tickets'}
            </h3>

            {myTickets.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-xs">
                No tickets found. Book your first trip above!
              </div>
            ) : (
              myTickets.map((t) => (
                <div key={t.booking_id} className="mobile-card p-3 text-xs space-y-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="font-mono text-emerald-400 font-bold">{t.booking_reference}</span>
                      <h5 className="font-bold text-white text-xs">{t.route_name}</h5>
                      <span className="text-[10px] text-slate-400">Seat {t.seat_number} • ₹{t.total_fare}</span>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      t.status === 'confirmed' ? 'badge-active' : 'badge-danger'
                    }`}>
                      {t.status.toUpperCase()}
                    </span>
                  </div>

                  <div className="flex gap-2 pt-1 border-t border-slate-800">
                    <button
                      onClick={() => setViewingQrTicket(t)}
                      className="flex-1 py-1.5 bg-slate-900 border border-slate-700 hover:border-emerald-400 text-slate-200 rounded font-bold text-[11px] flex items-center justify-center gap-1"
                    >
                      <QrCode className="h-3 w-3 text-emerald-400" /> View QR
                    </button>
                    {t.status === 'confirmed' && (
                      <button
                        onClick={() => handleCancelBooking(t.booking_id)}
                        className="py-1.5 px-3 bg-rose-950 border border-rose-500/40 text-rose-300 rounded font-bold text-[11px]"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}

            {/* Offline QR Viewer Modal */}
            {viewingQrTicket && (
              <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
                <div className="mobile-card p-5 bg-slate-900 max-w-xs w-full space-y-3 text-center border-emerald-500">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold text-emerald-400">Offline Tamper-Proof Ticket</span>
                    <button onClick={() => setViewingQrTicket(null)} className="text-slate-400 hover:text-white">
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  {/* QR Payload Box */}
                  <div className="p-4 bg-white rounded-xl text-slate-900 inline-block mx-auto shadow-2xl">
                    <div className="h-36 w-36 border-4 border-slate-900 flex flex-col items-center justify-center p-2 text-center">
                      <QrCode className="h-20 w-20 text-slate-900 mx-auto" />
                      <span className="text-[8px] font-mono font-bold uppercase mt-1">HMAC-SHA256 SIGNED</span>
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-300 font-mono space-y-0.5">
                    <div>Seat: <strong>{viewingQrTicket.seat_number}</strong> | Ref: <strong>{viewingQrTicket.booking_reference}</strong></div>
                    <div className="text-[10px] text-emerald-400 font-bold">Cryptographically Verified Offline</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: SAFETY, DESTINATION ALERTS & WRONG-BUS CHECK */}
        {subTab === 'safety' && (
          <div className="space-y-4 text-xs">
            {/* Destination Alert Simulation Box */}
            <div className="mobile-card p-4 space-y-3">
              <h4 className="font-bold text-xs text-white flex items-center gap-1.5">
                <Bell className="h-4 w-4 text-cyan-400" />
                <span>Destination Stop Alarm System</span>
              </h4>
              <p className="text-[11px] text-slate-400">
                Auditory chime + synthetic speech alert within 500m of destination. Louder alarm if stop is passed.
              </p>

              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={simulateDestinationApproaching}
                  className="p-2.5 bg-cyan-950/80 border border-cyan-500/40 rounded-lg text-cyan-200 font-bold text-center hover:bg-cyan-900 transition-all flex flex-col items-center gap-1"
                >
                  <Volume2 className="h-4 w-4 text-cyan-400" />
                  <span>Approaching (500m)</span>
                </button>
                <button
                  onClick={simulateMissedStopAlarm}
                  className="p-2.5 bg-rose-950/80 border border-rose-500/40 rounded-lg text-rose-200 font-bold text-center hover:bg-rose-900 transition-all flex flex-col items-center gap-1"
                >
                  <AlertTriangle className="h-4 w-4 text-rose-400" />
                  <span>Missed Stop Alarm!</span>
                </button>
              </div>

              {destinationAlertActive && (
                <div className="p-3 bg-cyan-950 border border-cyan-400 rounded-lg text-cyan-100 flex items-center gap-2 animate-bounce">
                  <Volume2 className="h-4 w-4 text-cyan-300" />
                  <span>Approaching destination stop within 500m! Please prepare to disembark.</span>
                </div>
              )}

              {missedStopAlarmActive && (
                <div className="p-3 bg-rose-950 border border-rose-400 rounded-lg text-rose-100 flex items-center gap-2 animate-pulse">
                  <AlertTriangle className="h-4 w-4 text-rose-300" />
                  <span>URGENT: Destination stop missed! Please request immediate halt.</span>
                </div>
              )}
            </div>

            {/* Wrong Bus Warning Check */}
            <div className="mobile-card p-4 space-y-3">
              <h4 className="font-bold text-xs text-white flex items-center gap-1.5">
                <AlertTriangle className="h-4 w-4 text-amber-400" />
                <span>Wrong-Bus Safety Verification</span>
              </h4>
              <p className="text-[11px] text-slate-400">
                Checks if you boarded the correct vehicle corresponding to your booked ticket.
              </p>

              <div className="space-y-2">
                <div>
                  <label className="text-[10px] text-slate-400 block mb-0.5">Boarded Bus Registration Number:</label>
                  <input
                    type="text"
                    value={boardedBusInput}
                    onChange={(e) => setBoardedBusInput(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs font-mono text-white"
                  />
                </div>
                <button
                  onClick={handleWrongBusCheck}
                  className="w-full py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-lg text-xs"
                >
                  Verify Boarded Bus Match
                </button>
              </div>

              {wrongBusModal && (
                <div className={`p-3 rounded-lg border text-xs space-y-1 ${
                  wrongBusModal.warning ? 'bg-rose-950/80 border-rose-500 text-rose-200' : 'bg-emerald-950/80 border-emerald-500 text-emerald-200'
                }`}>
                  <strong className="block text-sm font-bold">
                    {wrongBusModal.warning ? wrongBusModal.warning_title : 'MATCH CONFIRMED'}
                  </strong>
                  <p>{wrongBusModal.warning ? wrongBusModal.warning_message_en : wrongBusModal.message}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: JOURNEY AUTOPILOT */}
        {subTab === 'autopilot' && (
          <div className="space-y-4 text-xs">
            <div className="mobile-card p-4 space-y-3 bg-gradient-to-br from-slate-900 to-emerald-950/40 border-emerald-500/40">
              <div className="flex justify-between items-center">
                <h3 className="font-bold text-sm text-emerald-300 flex items-center gap-1.5">
                  <Sparkles className="h-4 w-4 text-emerald-400" />
                  <span>Journey Autopilot</span>
                </h3>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  autopilotPlan?.is_active ? 'badge-active' : 'badge-warning'
                }`}>
                  {autopilotPlan?.is_active ? 'ACTIVE' : 'PAUSED'}
                </span>
              </div>

              <p className="text-[11px] text-slate-300 leading-relaxed">
                Automated scheduler automatically books your daily commute ticket within budget safeguards with zero manual hassle.
              </p>

              {autopilotPlan ? (
                <div className="space-y-2 pt-2 border-t border-slate-800">
                  <div className="p-2.5 bg-slate-950 rounded-lg space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Route:</span>
                      <strong className="text-white">{autopilotPlan.route_name}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Preferred Window:</span>
                      <strong className="text-white font-mono">{autopilotPlan.preferred_window}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Monthly Limit:</span>
                      <strong className="text-emerald-400 font-mono">{autopilotPlan.current_month_bookings}/{autopilotPlan.max_monthly_bookings} bookings</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Max Fare Cap:</span>
                      <strong className="text-cyan-400 font-mono">₹{autopilotPlan.max_fare_limit}</strong>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={async () => {
                        await mobileApi.toggleAutopilot();
                        fetchAutopilot();
                      }}
                      className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded-lg text-xs"
                    >
                      {autopilotPlan.is_active ? 'Pause Plan' : 'Resume Plan'}
                    </button>
                    <button
                      onClick={handleTriggerAutopilotNow}
                      className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-xs shadow-md"
                    >
                      Test Auto-Book Now
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setConsentModal(true)}
                  className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-xs shadow-md"
                >
                  Set Up Daily Commute Autopilot
                </button>
              )}
            </div>

            {/* Explicit Consent Modal */}
            {consentModal && (
              <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
                <div className="mobile-card p-5 bg-slate-900 max-w-xs w-full space-y-3 border-emerald-500 text-xs">
                  <h4 className="font-bold text-white text-sm">Journey Autopilot Consent</h4>
                  <p className="text-[11px] text-slate-300 leading-relaxed">
                    By enabling Autopilot, you authorize TamilNadu Transit 360 AI to automatically reserve tickets on your designated commute days between 07:30 - 09:00, subject to your ₹150 budget limit and monthly cap.
                  </p>
                  <p className="text-[10px] text-emerald-400 font-semibold">
                    You can pause or cancel anytime. Notifications sent before and after every booking.
                  </p>
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={handleAutopilotConsentSubmit}
                      className="flex-1 py-2 bg-emerald-600 text-white font-bold rounded-lg"
                    >
                      I Agree & Enable
                    </button>
                    <button
                      onClick={() => setConsentModal(false)}
                      className="flex-1 py-2 bg-slate-800 text-slate-300 rounded-lg"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
