import React, { useState, useEffect } from 'react';
import PassengerScreen from './screens/passenger/PassengerScreen';
import DriverScreen from './screens/driver/DriverScreen';
import ConductorScreen from './screens/conductor/ConductorScreen';
import EmployeeScreen from './screens/employee/EmployeeScreen';
import { mobileApi } from './services/api';
import {
  Bus, User, Navigation, ShieldCheck, QrCode, Globe, Battery, Wifi, Signal
} from 'lucide-react';

export default function App() {
  const [activeRole, setActiveRole] = useState('passenger'); // passenger, driver, conductor, employee
  const [lang, setLang] = useState('en');

  // Auto-login according to role
  useEffect(() => {
    const rolePhones = {
      passenger: '9876543210',
      driver: '9700001001',
      conductor: '9700002001',
      employee: '9700003001'
    };
    const phone = rolePhones[activeRole] || '9876543210';
    mobileApi.loginOtp(phone, '123456').then((res) => {
      mobileApi.setToken(res.access_token);
    }).catch((e) => console.warn('Auth switch:', e));
  }, [activeRole]);

  return (
    <div className="w-full min-h-screen bg-slate-950 flex flex-col items-center justify-center p-2 md:p-6 font-sans">
      {/* Smartphone Device Mockup Frame */}
      <div className="mobile-device-frame">
        {/* Phone Top Notch & Status Bar */}
        <div className="bg-slate-950 px-6 pt-2 pb-1 flex justify-between items-center text-[11px] text-slate-400 select-none">
          <span className="font-mono font-bold text-white">09:41</span>
          <div className="mobile-notch">
            <div className="mobile-camera"></div>
          </div>
          <div className="flex items-center gap-1.5 text-white">
            <Signal className="h-3 w-3" />
            <Wifi className="h-3 w-3" />
            <Battery className="h-3 w-3" />
          </div>
        </div>

        {/* Role Switcher & Language Bar */}
        <div className="bg-slate-900 border-b border-slate-800 px-3 py-2 flex items-center justify-between gap-2">
          <div className="flex items-center gap-1 overflow-x-auto py-0.5">
            {[
              { id: 'passenger', label: 'Passenger' },
              { id: 'driver', label: 'Driver' },
              { id: 'conductor', label: 'Conductor' },
              { id: 'employee', label: 'Passes' }
            ].map((r) => (
              <button
                key={r.id}
                onClick={() => setActiveRole(r.id)}
                className={`px-2.5 py-1 rounded-full text-[10px] font-bold transition-all whitespace-nowrap ${
                  activeRole === r.id
                    ? 'bg-emerald-500 text-white shadow-sm shadow-emerald-500/30'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>

          <button
            onClick={() => setLang(lang === 'en' ? 'ta' : 'en')}
            className="flex-shrink-0 px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-[10px] font-bold text-cyan-300 flex items-center gap-1"
          >
            <Globe className="h-2.5 w-2.5" />
            <span>{lang === 'en' ? 'தமிழ்' : 'EN'}</span>
          </button>
        </div>

        {/* Role Screens */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {activeRole === 'passenger' && <PassengerScreen lang={lang} />}
          {activeRole === 'driver' && <DriverScreen lang={lang} />}
          {activeRole === 'conductor' && <ConductorScreen lang={lang} />}
          {activeRole === 'employee' && <EmployeeScreen lang={lang} />}
        </div>

        {/* Bottom Home Indicator Bar */}
        <div className="bg-slate-950 py-1.5 flex justify-center">
          <div className="w-32 h-1 bg-slate-700 rounded-full"></div>
        </div>
      </div>
    </div>
  );
}
