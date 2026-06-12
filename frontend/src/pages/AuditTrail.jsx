import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { auditTrail } from "../api/api";

export default function AuditTrail() {
  const [cnic, setCnic] = useState(localStorage.getItem("selected_cnic") || "");
  const [trail, setTrail] = useState("");

  const loadTrail = async () => {
    const res = await auditTrail(cnic);
    setTrail(res.data.audit_trail);
  };

  return (
    <div className="flex min-h-screen bg-[#F4F6FB]">
      <Sidebar />
      <main className="flex-1">
        <Navbar />

        <div className="p-8 space-y-6">
          <h1 className="text-4xl font-black">Explainable Audit Trail</h1>
          <p className="text-slate-600">
            Shows why a citizen was flagged by the Tax Compliance Deviation engine.
          </p>

          <div className="bg-white border rounded-xl p-6 flex gap-4">
            <input
              value={cnic}
              onChange={(e) => setCnic(e.target.value)}
              placeholder="Enter CNIC"
              className="border px-4 py-2 rounded w-80"
            />

            <button
              onClick={loadTrail}
              className="bg-slate-950 text-white px-5 py-2 rounded font-bold"
            >
              Generate Trail
            </button>
          </div>

          {trail && (
            <pre className="bg-white border rounded-xl p-6 whitespace-pre-wrap text-sm">
              {trail}
            </pre>
          )}
        </div>
      </main>
    </div>
  );
}