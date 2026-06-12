import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { uploadDataset } from "../api/api";

export default function DataSources() {
  const [datasetType, setDatasetType] = useState("vehicles");
  const [fiscalYear, setFiscalYear] = useState("2026");
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");

  const upload = async () => {
    if (!file) {
      setMessage("Please select a CSV file.");
      return;
    }

    try {
      const res = await uploadDataset(datasetType, fiscalYear, file);
      setMessage(res.data.message);
    } catch (err) {
      setMessage(err.response?.data?.detail || "Upload failed.");
    }
  };

  return (
    <div className="flex min-h-screen bg-[#F4F6FB]">
      <Sidebar />
      <main className="flex-1">
        <Navbar />

        <div className="p-8 space-y-6">
          <h1 className="text-4xl font-black">Data Sources</h1>
          <p className="text-slate-600">
            Upload synthetic Pakistani civic datasets for graph construction.
          </p>

          <div className="bg-white border rounded-xl p-6 space-y-5 max-w-xl">
            <select
              value={datasetType}
              onChange={(e) => setDatasetType(e.target.value)}
              className="w-full border p-3 rounded"
            >
              <option value="vehicles">Vehicles</option>
              <option value="properties">Properties</option>
              <option value="tax_records">Tax Records</option>
              <option value="utilities">Utilities</option>
              <option value="travel_records">Luxury Travel Records</option>
            </select>

            <input
              value={fiscalYear}
              onChange={(e) => setFiscalYear(e.target.value)}
              className="w-full border p-3 rounded"
              placeholder="Fiscal Year"
            />

            <input
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files[0])}
              className="w-full border p-3 rounded"
            />

            <button
              onClick={upload}
              className="bg-slate-950 text-white px-6 py-3 rounded font-bold"
            >
              Upload Dataset
            </button>

            {message && <p className="font-bold text-teal-700">{message}</p>}
          </div>
        </div>
      </main>
    </div>
  );
}