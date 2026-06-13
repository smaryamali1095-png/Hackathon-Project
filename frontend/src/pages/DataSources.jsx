import React, { useState } from "react";
import {
  UploadCloud,
  Database,
  Calendar,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Car,
  Home,
  FileText,
  Zap,
  Plane
} from "lucide-react";

import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { uploadDataset } from "../api/api";

const datasetOptions = [
  { value: "vehicles", label: "Vehicles", icon: Car, color: "from-emerald-500 to-teal-500" },
  { value: "properties", label: "Properties", icon: Home, color: "from-orange-500 to-amber-500" },
  { value: "tax_records", label: "Tax Records", icon: FileText, color: "from-red-500 to-rose-500" },
  { value: "utilities", label: "Utilities", icon: Zap, color: "from-purple-500 to-violet-500" },
  { value: "travel_records", label: "Luxury Travel Records", icon: Plane, color: "from-cyan-500 to-blue-500" }
];

export default function DataSources() {
  const [datasetType, setDatasetType] = useState("vehicles");
  const [fiscalYear, setFiscalYear] = useState("2026");
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("");
  const [uploading, setUploading] = useState(false);

  const selectedDataset = datasetOptions.find((item) => item.value === datasetType);

  const upload = async () => {
    if (!file) {
      setStatus("error");
      setMessage("Please select a CSV file before uploading.");
      return;
    }

    try {
      setUploading(true);
      setStatus("");
      setMessage("");

      const res = await uploadDataset(datasetType, fiscalYear, file);

      setStatus("success");
      setMessage(res.data.message || "Dataset uploaded successfully.");
    } catch (err) {
      setStatus("error");
      setMessage(err.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/40 to-cyan-50 text-slate-900">
      <Sidebar />

      <main className="flex-1">
        <Navbar />

        <div className="p-8 space-y-7">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-950 via-blue-950 to-slate-900 p-8 text-white shadow-2xl">
            <div className="absolute -top-20 -right-20 h-64 w-64 rounded-full bg-cyan-500/20 blur-3xl" />
            <div className="absolute -bottom-24 -left-20 h-64 w-64 rounded-full bg-blue-500/20 blur-3xl" />

            <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-4 py-2 text-xs font-black uppercase tracking-widest text-cyan-100">
                  <Database size={15} />
                  Data ingestion center
                </div>

                <h1 className="mt-5 text-4xl lg:text-5xl font-black tracking-tight">
                  Data Sources
                </h1>

                <p className="mt-3 max-w-2xl text-sm lg:text-base text-slate-300 leading-relaxed">
                  Upload synthetic Pakistani civic datasets and feed them into the graph intelligence pipeline for entity resolution, relationship mapping, and tax-risk scoring.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 min-w-[280px]">
                <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur">
                  <p className="text-xs text-slate-300 font-bold">Accepted Format</p>
                  <p className="text-2xl font-black mt-1">CSV</p>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur">
                  <p className="text-xs text-slate-300 font-bold">Pipeline Status</p>
                  <p className="text-2xl font-black mt-1 text-emerald-300">Online</p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2 rounded-3xl border border-slate-200 bg-white/90 shadow-xl overflow-hidden">
              <div className={`bg-gradient-to-r ${selectedDataset.color} p-6 text-white`}>
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur">
                    {React.createElement(selectedDataset.icon, { size: 25 })}
                  </div>

                  <div>
                    <h2 className="text-2xl font-black">Upload Dataset</h2>
                    <p className="text-sm text-white/85">
                      Selected source: {selectedDataset.label}
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-6 space-y-5">
                <div>
                  <label className="text-xs font-black uppercase tracking-widest text-slate-500">
                    Dataset Type
                  </label>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2">
                    {datasetOptions.map((item) => {
                      const Icon = item.icon;
                      const active = datasetType === item.value;

                      return (
                        <button
                          key={item.value}
                          type="button"
                          onClick={() => setDatasetType(item.value)}
                          className={`flex items-center gap-3 rounded-2xl border p-4 text-left transition-all ${
                            active
                              ? "border-blue-500 bg-blue-50 shadow-md"
                              : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                          }`}
                        >
                          <div className={`h-10 w-10 rounded-xl bg-gradient-to-br ${item.color} text-white flex items-center justify-center`}>
                            <Icon size={19} />
                          </div>

                          <div>
                            <p className="font-black text-sm text-slate-900">{item.label}</p>
                            <p className="text-xs text-slate-500">CSV source mapping</p>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-black uppercase tracking-widest text-slate-500">
                      Fiscal Year
                    </label>

                    <div className="relative mt-2">
                      <Calendar size={18} className="absolute left-4 top-3.5 text-slate-400" />
                      <input
                        value={fiscalYear}
                        onChange={(e) => setFiscalYear(e.target.value)}
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 text-sm font-bold outline-none focus:border-blue-500 focus:bg-white"
                        placeholder="Fiscal Year"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-black uppercase tracking-widest text-slate-500">
                      CSV File
                    </label>

                    <label className="mt-2 flex cursor-pointer items-center gap-3 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-3 hover:border-blue-400 hover:bg-blue-50 transition-all">
                      <FileSpreadsheet size={22} className="text-blue-600" />
                      <span className="min-w-0 flex-1 text-sm font-bold text-slate-700 truncate">
                        {file ? file.name : "Choose CSV file"}
                      </span>
                      <input
                        type="file"
                        accept=".csv"
                        onChange={(e) => setFile(e.target.files[0])}
                        className="hidden"
                      />
                    </label>
                  </div>
                </div>

                <button
                  onClick={upload}
                  disabled={uploading}
                  className="w-full md:w-auto inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-slate-950 to-blue-900 px-7 py-3.5 text-sm font-black text-white shadow-lg shadow-blue-900/20 transition-all hover:scale-[1.01] hover:shadow-xl disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  <UploadCloud size={19} />
                  {uploading ? "Uploading Dataset..." : "Upload Dataset"}
                </button>

                {message && (
                  <div
                    className={`flex items-start gap-3 rounded-2xl border p-4 text-sm font-bold ${
                      status === "success"
                        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                        : "border-red-200 bg-red-50 text-red-700"
                    }`}
                  >
                    {status === "success" ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
                    <span>{message}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-xl">
                <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 text-white flex items-center justify-center">
                  <ShieldCheck size={24} />
                </div>

                <h3 className="mt-4 text-xl font-black text-slate-900">
                  Pipeline Flow
                </h3>

                <div className="mt-5 space-y-3">
                  {[
                    "CSV upload",
                    "Data validation",
                    "Neo4j graph insert",
                    "Entity resolution",
                    "Risk scoring"
                  ].map((step, index) => (
                    <div key={step} className="flex items-center gap-3">
                      <span className="h-7 w-7 rounded-full bg-blue-50 text-blue-700 flex items-center justify-center text-xs font-black">
                        {index + 1}
                      </span>
                      <span className="text-sm font-bold text-slate-700">{step}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-slate-950 p-6 shadow-xl text-white overflow-hidden relative">
                <div className="absolute -right-14 -top-14 h-40 w-40 rounded-full bg-blue-500/20 blur-3xl" />
                <h3 className="relative text-xl font-black">Upload Guidelines</h3>

                <ul className="relative mt-4 space-y-3 text-sm text-slate-300">
                  <li>• File must be in CSV format.</li>
                  <li>• Use clean column names matching backend schema.</li>
                  <li>• Keep fiscal year consistent with dataset records.</li>
                  <li>• Upload one dataset category at a time.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}