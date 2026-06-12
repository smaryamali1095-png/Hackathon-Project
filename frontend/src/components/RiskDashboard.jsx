import React, { useState } from 'react';
import { analyzeRisk } from '../services/api';

const RiskDashboard = () => {
  const [cnic, setCnic] = useState('');
  const [result, setResult] = useState(null);

  const handleSearch = async () => {
    try {
      const { data } = await analyzeRisk(cnic);
      setResult(data);
    } catch (err) {
      alert("Error fetching investigation data.");
    }
  };

  return (
    <div className="max-w-4xl mx-auto mt-10">
      <div className="flex gap-2">
        <input 
          className="border p-2 w-full rounded" 
          value={cnic} 
          onChange={(e) => setCnic(e.target.value)}
          placeholder="Enter CNIC for Risk Investigation..." 
        />
        <button onClick={handleSearch} className="bg-blue-700 text-white px-6 py-2 rounded">
          Run Analysis
        </button>
      </div>

      {result && (
        <div className="mt-8 space-y-4">
          <div className="bg-white p-6 border-l-4 border-red-500 shadow">
            <h2 className="text-xl font-bold">Risk Level: {result.analysis.risk_level}</h2>
            <p className="text-gray-600 mt-2">{result.analysis.explanation}</p>
          </div>
          
          <div className="bg-gray-800 text-white p-6 rounded">
            <h3 className="font-semibold mb-2 text-blue-400">AI Investigation Audit Trail</h3>
            <p className="text-sm font-mono whitespace-pre-line">{result.audit_trail}</p>
          </div>
        </div>
      )}
    </div>
  );
};
export default RiskDashboard;