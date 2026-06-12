import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { reportUrl } from "../api/api";

export default function Reports() {
  const [cnic, setCnic] = useState(localStorage.getItem("selected_cnic") || "");

  const download = () => {
    if (cnic) {
      window.open(reportUrl(cnic), "_blank");
    }
  };

  return (
    <div className="flex min-h-screen bg-[#F4F6FB]">
      <Sidebar />
      <main className="flex-1">
        <Navbar />

        <div className="p-8 space-y-6">
          <h1 className="text-4xl font-black">Reports</h1>
          <p className="text-slate-600">
            Download PDF investigation reports.
          </p>

          <div className="bg-white border rounded-xl p-6 flex gap-4">
            <input
              value={cnic}
              onChange={(e) => setCnic(e.target.value)}
              placeholder="Enter CNIC"
              className="border px-4 py-2 rounded w-80"
            />

            <button
              onClick={download}
              className="bg-slate-950 text-white px-5 py-2 rounded font-bold"
            >
              Download PDF
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}