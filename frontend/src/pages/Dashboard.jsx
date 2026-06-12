import React, { useEffect, useState } from 'react';
import axios from 'axios';
import UploadDataset from '../components/UploadDataset';
import RiskDashboard from '../components/RiskDashboard';

const Dashboard = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    // Pull the system state whenever the dashboard loads
    axios.get('http://localhost:8000/data/summary-stats')
      .then(res => setStats(res.data.stats));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Investigator Portal</h1>
      
      {/* Visual Stats Row */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-blue-100 p-4 rounded">Tax Records: {stats.tax_records}</div>
          <div className="bg-green-100 p-4 rounded">Vehicles Registered: {stats.vehicles}</div>
          <div className="bg-purple-100 p-4 rounded">Connections: {stats.connected_relationships}</div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <UploadDataset />
        <RiskDashboard />
      </div>
    </div>
  );
};

export default Dashboard;