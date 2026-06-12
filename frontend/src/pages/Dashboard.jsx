import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import Navbar from '../components/Navbar';
import { BarChart3, Users, ShieldAlert } from 'lucide-react';

export default function Dashboard() {
  // These states will eventually hold data from your API
  const [metrics, setMetrics] = useState({ ratio: '10.4%', taxpayers: '3.24M', compliance: '68.2' });
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    // API CALL PLACEHOLDER:
    // fetch('/api/dashboard-data').then(res => res.json()).then(data => setMetrics(data));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Navbar />
        <main className="p-8">
          <h2 className="text-2xl font-bold text-slate-900 mb-8">Assalaamu Alaykum, Auditor.</h2>
          
          {/* Metrics Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <MetricCard title="Tax-to-GDP Ratio" value={metrics.ratio} sub="~ +0.8% from last FY" icon={BarChart3} />
            <MetricCard title="Total Taxpayers" value={metrics.taxpayers} sub="Active Filers (Ver 2.0)" icon={Users} />
            <MetricCard title="National Compliance" value={`${metrics.compliance}/100`} sub="System Optimized" icon={ShieldAlert} />
          </div>

          {/* Visualization Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white p-6 rounded-2xl border shadow-sm">
              <h4 className="font-bold mb-4">Regional Compliance Insights</h4>
              <div className="h-64 bg-slate-50 border-2 border-dashed rounded-xl flex items-center justify-center">Map Visualization</div>
            </div>
            <div className="space-y-6">
              <ActionCard title="Advanced Entity Resolution" link="Explore Logic →" color="bg-slate-900" />
              <ActionCard title="Relational Graph Analysis" link="Launch Graph View →" color="bg-white" border />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

// Sub-components for cleaner code
const MetricCard = ({ title, value, sub, icon: Icon }) => (
  <div className="bg-white p-6 rounded-2xl border shadow-sm flex justify-between">
    <div>
      <p className="text-slate-500 text-xs font-bold uppercase">{title}</p>
      <h3 className="text-3xl font-bold mt-2">{value}</h3>
      <p className="text-emerald-600 text-xs font-bold mt-1">{sub}</p>
    </div>
    <Icon className="text-slate-400" />
  </div>
);

const ActionCard = ({ title, link, color, border }) => (
  <div className={`${color} p-6 rounded-2xl ${border ? 'border' : ''} text-${color === 'bg-slate-900' ? 'white' : 'slate-900'}`}>
    <h4 className="font-bold mb-2">{title}</h4>
    <button className="text-sm font-bold opacity-80 hover:opacity-100">{link}</button>
  </div>
);