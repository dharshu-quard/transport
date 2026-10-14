import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LiveFleetMap from './pages/LiveFleetMap';
import AIInsightsPage from './pages/AIInsightsPage';
import FleetManagement from './pages/FleetManagement';
import OperationsRoster from './pages/OperationsRoster';
import PassReviewWorkflow from './pages/PassReviewWorkflow';
import ReportsAnalytics from './pages/ReportsAnalytics';
import AuditLogViewer from './pages/AuditLogViewer';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('fleet-map');
  const [currentRole, setCurrentRole] = useState('admin');
  const [lang, setLang] = useState('en');

  // Auto-login as State Director on load for seamless zero-friction prototype exploration
  useEffect(() => {
    const initAuth = async () => {
      try {
        const res = await api.loginOtp('9840000001', '123456');
        api.setToken(res.access_token);
      } catch (e) {
        console.warn('Auto-auth initial notice:', e);
      }
    };
    initAuth();
  }, [currentRole]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentRole={currentRole}
        setCurrentRole={setCurrentRole}
        lang={lang}
        setLang={setLang}
      />

      <main className="flex-1 w-full overflow-y-auto">
        {activeTab === 'fleet-map' && <LiveFleetMap lang={lang} />}
        {activeTab === 'ai-insights' && <AIInsightsPage lang={lang} />}
        {activeTab === 'fleet-crud' && <FleetManagement currentRole={currentRole} lang={lang} />}
        {activeTab === 'operations' && <OperationsRoster currentRole={currentRole} lang={lang} />}
        {activeTab === 'passes' && <PassReviewWorkflow currentRole={currentRole} lang={lang} />}
        {activeTab === 'reports' && <ReportsAnalytics lang={lang} />}
        {activeTab === 'audits' && <AuditLogViewer currentRole={currentRole} lang={lang} />}
      </main>
    </div>
  );
}
