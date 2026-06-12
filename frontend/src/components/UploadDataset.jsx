import React, { useState } from 'react';
import axios from 'axios';

const UploadDataset = () => {
  const [file, setFile] = useState(null);
  const [datasetType, setDatasetType] = useState('tax_records');
  const [fiscalYear, setFiscalYear] = useState('2026');
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return alert("Please select a file first.");
    
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('fiscal_year', fiscalYear);

    try {
      // Pointing to your FastAPI backend
      const response = await axios.post(`http://localhost:8000/data/upload/${datasetType}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert(response.data.message);
    } catch (error) {
      console.error("Upload error:", error);
      alert("Failed to process dataset. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-8 rounded-lg shadow-md max-w-lg mx-auto mt-10">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Dataset Integration</h2>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Dataset Category</label>
          <select 
            className="w-full mt-1 p-2 border rounded"
            onChange={(e) => setDatasetType(e.target.value)}
          >
            <option value="tax_records">FBR Tax Records</option>
            <option value="vehicles">Vehicle Registration</option>
            <option value="properties">Property Registry</option>
            <option value="utilities">Utility Consumption</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Fiscal Year</label>
          <input 
            type="text" 
            className="w-full mt-1 p-2 border rounded"
            value={fiscalYear}
            onChange={(e) => setFiscalYear(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Select CSV File</label>
          <input 
            type="file" 
            accept=".csv"
            className="w-full mt-1"
            onChange={(e) => setFile(e.target.files[0])} 
          />
        </div>

        <button 
          onClick={handleUpload}
          disabled={loading}
          className={`w-full py-2 px-4 rounded text-white font-bold ${
            loading ? 'bg-gray-400' : 'bg-green-600 hover:bg-green-700'
          }`}
        >
          {loading ? 'Processing & Integrating...' : 'Upload & Integrate'}
        </button>
      </div>
    </div>
  );
};

export default UploadDataset;