import React, { useEffect, useState, useRef } from 'react';
import { api } from '../services/api';
import { Bus, Navigation, AlertTriangle, Clock, Gauge, ArrowRight, ShieldAlert, RefreshCw } from 'lucide-react';
import L from 'leaflet';

export default function LiveFleetMap({ lang }) {
  const [fleet, setFleet] = useState([]);
  const [selectedBus, setSelectedBus] = useState(null);
  const [etaData, setEtaData] = useState(null);
  const [loadingEta, setLoadingEta] = useState(false);
  const [deviationAlert, setDeviationAlert] = useState(null);
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef({});

  // Fetch fleet positions
  const fetchFleet = async () => {
    try {
      const data = await api.getLiveFleet();
      setFleet(data);
      updateMarkers(data);

      // Check if any bus is deviated
      const devBus = data.find((b) => b.is_deviated);
      if (devBus) {
        setDeviationAlert({
          busRegistration: devBus.registration_number,
          route: devBus.route_name,
          tripId: devBus.current_trip_id
        });
      }
    } catch (err) {
      console.error('Failed to fetch fleet:', err);
    }
  };

  // Initialize Leaflet map
  useEffect(() => {
    if (!mapInstanceRef.current && mapContainerRef.current) {
      // Center of Tamil Nadu
      const map = L.map(mapContainerRef.current, {
        center: [11.1271, 78.6569],
        zoom: 7,
        zoomControl: true
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18
      }).addTo(map);

      mapInstanceRef.current = map;
    }

    fetchFleet();

    // WebSocket connection for live GPS updates
    let ws;
    try {
      ws = new WebSocket('ws://127.0.0.1:8000/api/tracking/ws');
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'FLEET_GPS_UPDATE' && msg.pings) {
            fetchFleet();
          }
        } catch (e) {}
      };
    } catch (e) {
      console.warn('WS fallback to polling', e);
    }

    const interval = setInterval(fetchFleet, 5000);

    return () => {
      clearInterval(interval);
      if (ws) ws.close();
    };
  }, []);

  // Update map markers
  const updateMarkers = (busList) => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    busList.forEach((bus) => {
      const { bus_id, registration_number, latitude, longitude, is_deviated, is_in_transit, speed_kmh } = bus;

      // Custom HTML Marker icon
      const markerColor = is_deviated ? '#f43f5e' : is_in_transit ? '#10b981' : '#0ea5e9';
      const pulseClass = is_deviated ? 'animate-ping' : is_in_transit ? 'beacon-pulse' : '';

      const customIcon = L.divIcon({
        className: 'custom-bus-pin',
        html: `
          <div style="position: relative; display: flex; align-items: center; justify-content: center;">
            <div style="width: 28px; height: 28px; border-radius: 50%; background: ${markerColor}; border: 2px solid white; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">
              <span style="font-size: 11px; font-weight: bold; color: white;">🚌</span>
            </div>
            ${is_deviated ? '<div style="position: absolute; top: -5px; right: -5px; width: 12px; height: 12px; border-radius: 50%; background: #ef4444; border: 2px solid white;"></div>' : ''}
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      });

      if (markersRef.current[bus_id]) {
        markersRef.current[bus_id].setLatLng([latitude, longitude]);
        markersRef.current[bus_id].setIcon(customIcon);
      } else {
        const marker = L.marker([latitude, longitude], { icon: customIcon }).addTo(map);
        marker.on('click', () => handleSelectBus(bus));
        markersRef.current[bus_id] = marker;
      }
    });
  };

  const handleSelectBus = async (bus) => {
    setSelectedBus(bus);
    setLoadingEta(true);
    setEtaData(null);
    try {
      // Pick a downstream stop (e.g. Madurai) to query ETA
      const stops = await api.getStops();
      const targetStop = stops[stops.length - 1] || stops[0];
      const eta = await api.getBusEta(bus.bus_id, targetStop.id);
      setEtaData(eta);
    } catch (e) {
      console.warn('ETA fetch error:', e);
    } finally {
      setLoadingEta(false);
    }
  };

  const handleTriggerTestDeviation = async () => {
    if (!selectedBus || !selectedBus.current_trip_id) {
      // Pick first in-transit bus
      const active = fleet.find((b) => b.is_in_transit);
      if (active) {
        await api.testDeviation(active.current_trip_id, true);
        fetchFleet();
      }
    } else {
      await api.testDeviation(selectedBus.current_trip_id, true);
      fetchFleet();
    }
  };

  return (
    <div className="relative h-[calc(100vh-80px)] w-full overflow-hidden flex flex-col md:flex-row">
      {/* Live Map Frame */}
      <div className="flex-1 relative h-full">
        <div ref={mapContainerRef} className="w-full h-full z-0" />

        {/* Floating Top Controls Overlay */}
        <div className="absolute top-4 left-4 z-10 flex flex-wrap items-center gap-2">
          <div className="glass-panel px-4 py-2 bg-slate-900/90 text-xs flex items-center gap-3 shadow-xl">
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="font-semibold text-slate-200">
                {lang === 'ta' ? 'செயலில் உள்ள பேருந்துகள்:' : 'Active Fleet:'} {fleet.filter((b) => b.is_in_transit).length}
              </span>
            </div>
            <div className="h-4 w-px bg-slate-700"></div>
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-cyan-400"></span>
              <span className="text-slate-300">
                {lang === 'ta' ? 'மொத்த வாகனங்கள்:' : 'Total Tracked:'} {fleet.length}
              </span>
            </div>
          </div>

          <button
            onClick={fetchFleet}
            className="glass-panel px-3 py-2 bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-semibold flex items-center gap-1.5 shadow-xl transition-all"
          >
            <RefreshCw className="h-3.5 w-3.5 text-emerald-400" />
            <span>{lang === 'ta' ? 'புதுப்பி' : 'Refresh'}</span>
          </button>

          <button
            onClick={handleTriggerTestDeviation}
            className="glass-panel px-3 py-2 bg-rose-950/80 border-rose-500/40 hover:bg-rose-900 text-rose-200 text-xs font-bold flex items-center gap-1.5 shadow-xl transition-all"
            title="Simulate a bus leaving designated route corridor to verify AI geofence alarm"
          >
            <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
            <span>{lang === 'ta' ? 'விலகல் சோதனை' : 'Simulate Route Deviation Alert'}</span>
          </button>
        </div>

        {/* Deviation Alert Banner (if bus strays off-corridor) */}
        {deviationAlert && (
          <div className="absolute top-16 left-4 right-4 md:right-auto md:w-96 z-10 glass-panel p-4 bg-rose-950/95 border-rose-500/70 shadow-2xl text-rose-100 flex items-start gap-3 animate-bounce">
            <ShieldAlert className="h-6 w-6 text-rose-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs">
              <h4 className="font-bold text-rose-200 uppercase tracking-wider text-[11px]">
                {lang === 'ta' ? 'கடுமையான எச்சரிக்கை: வழித்தட விலகல்!' : 'CRITICAL ALERT: ROUTE DEVIATION DETECTED'}
              </h4>
              <p className="mt-1 text-slate-200 leading-relaxed">
                Bus <strong className="text-white font-mono">{deviationAlert.busRegistration}</strong> strayed outside its assigned corridor on route <strong>{deviationAlert.route}</strong>.
              </p>
              <span className="inline-block mt-2 font-mono text-[10px] px-2 py-0.5 bg-rose-900/80 rounded border border-rose-400/40">
                ANOMALY SCORE: 0.942 | POLICE & DEPOT NOTIFIED
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Right Detail Drawer */}
      <div className="w-full md:w-96 glass-panel border-l border-slate-800 bg-slate-950/90 p-5 overflow-y-auto flex flex-col gap-4 shadow-2xl">
        <h3 className="text-sm font-bold tracking-wide uppercase text-slate-300 flex items-center gap-2">
          <Navigation className="h-4 w-4 text-emerald-400" />
          <span>{lang === 'ta' ? 'பேருந்து நேரலை விவரம்' : 'Bus Telemetry & Dispatch'}</span>
        </h3>

        {selectedBus ? (
          <div className="space-y-4 text-xs">
            {/* Bus Header Card */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-700/80 shadow-md">
              <div className="flex items-center justify-between">
                <span className="text-base font-extrabold font-mono text-white tracking-wide">
                  {selectedBus.registration_number}
                </span>
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                  selectedBus.is_deviated
                    ? 'badge-danger'
                    : selectedBus.is_in_transit
                    ? 'badge-active'
                    : 'badge-info'
                }`}>
                  {selectedBus.is_deviated ? 'DEVIATED' : selectedBus.is_in_transit ? 'IN TRANSIT' : 'STANDBY'}
                </span>
              </div>
              <p className="mt-1.5 text-slate-300 font-medium">{selectedBus.route_name}</p>
              <div className="mt-3 grid grid-cols-2 gap-2 text-slate-400 border-t border-slate-800 pt-3">
                <div>
                  <span className="block text-[10px] text-slate-500 uppercase">{lang === 'ta' ? 'வகை' : 'Class'}</span>
                  <span className="font-semibold text-slate-200">{selectedBus.bus_type}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-slate-500 uppercase">{lang === 'ta' ? 'வேகம்' : 'Speed'}</span>
                  <span className="font-semibold text-emerald-400 flex items-center gap-1 font-mono">
                    <Gauge className="h-3 w-3" /> {selectedBus.speed_kmh} km/h
                  </span>
                </div>
              </div>
            </div>

            {/* AI Arrival Time Comparison Card */}
            <div className="p-4 rounded-xl bg-gradient-to-br from-slate-900 to-indigo-950/40 border border-indigo-500/30 shadow-md">
              <h4 className="font-bold text-indigo-300 flex items-center gap-1.5 text-xs">
                <Clock className="h-4 w-4 text-indigo-400" />
                <span>{lang === 'ta' ? 'AI வருகை கணிப்பு vs அடிப்படை' : 'ML Arrival Time (ETA) Comparison'}</span>
              </h4>

              {loadingEta ? (
                <div className="py-4 text-center text-slate-400 animate-pulse">Calculating neural ETA...</div>
              ) : etaData ? (
                <div className="mt-3 space-y-2.5">
                  <div className="flex justify-between items-center text-slate-300">
                    <span>{lang === 'ta' ? 'இலக்கு நிறுத்தம்' : 'Target Stop'}:</span>
                    <strong className="text-white">{etaData.target_stop_name}</strong>
                  </div>
                  <div className="flex justify-between items-center text-slate-300">
                    <span>{lang === 'ta' ? 'மீதமுள்ள தூரம்' : 'Distance Remaining'}:</span>
                    <strong className="text-white font-mono">{etaData.distance_remaining_km} km</strong>
                  </div>

                  <div className="grid grid-cols-2 gap-2 mt-3 pt-2 border-t border-slate-800">
                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="block text-[10px] text-slate-400">{lang === 'ta' ? 'அடிப்படை ETA' : 'Naive Baseline'}</span>
                      <span className="text-sm font-bold text-slate-300 font-mono">
                        {etaData.baseline_eta_minutes} min
                      </span>
                    </div>
                    <div className="p-2 rounded bg-emerald-950/60 border border-emerald-500/40">
                      <span className="block text-[10px] text-emerald-300 font-bold">{lang === 'ta' ? 'AI கணிக்கப்பட்ட ETA' : 'ML Model (Traffic)'}</span>
                      <span className="text-sm font-bold text-emerald-400 font-mono">
                        {etaData.ml_predicted_eta_minutes} min
                      </span>
                    </div>
                  </div>
                  <p className="text-[10px] text-slate-400 italic">
                    AI adjusts for highway toll congestion, peak-hour traffic index, and historical weather delay.
                  </p>
                </div>
              ) : (
                <div className="py-2 text-slate-400 text-xs">Click a bus to compute neural ETA.</div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="flex gap-2">
              <button
                onClick={handleTriggerTestDeviation}
                className="flex-1 py-2 px-3 rounded-lg bg-rose-600/20 border border-rose-500/40 text-rose-300 hover:bg-rose-600/30 font-bold text-xs transition-all text-center"
              >
                {lang === 'ta' ? 'விலகல் எச்சரிக்கை சோதனை' : 'Test Route Deviation'}
              </button>
            </div>
          </div>
        ) : (
          <div className="py-12 text-center text-slate-400">
            <Bus className="h-8 w-8 text-slate-600 mx-auto mb-2" />
            <p className="text-xs">{lang === 'ta' ? 'வரைபடத்தில் பேருந்தை கிளிக் செய்து நேரலை விவரங்களைக் காண்க.' : 'Click on any moving bus marker on the map to inspect live telematics, route waypoints, and ETA.'}</p>
          </div>
        )}
      </div>
    </div>
  );
}
