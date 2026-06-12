import React, { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { entityResolution } from "../api/api";

export default function EntityResolution() {
  const [threshold, setThreshold] = useState(75);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadMatches = async () => {
    try {
      setLoading(true);
      const res = await entityResolution(threshold);
      setMatches(res.data.matches || []);
    } catch (err) {
      console.error("Entity resolution failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMatches();
  }, []);

  return (
    <div className="flex min-h-screen bg-[#F4F6FB]">
      <Sidebar />
      <main className="flex-1">
        <Navbar />

        <div className="p-8 space-y-6">
          <h1 className="text-4xl font-black">Entity Resolution</h1>
          <p className="text-slate-600">
            Matches fragmented citizen identities using CNIC, fuzzy text matching, and multilingual embeddings.
          </p>

          <div className="bg-white p-6 rounded-xl border flex items-center gap-4">
            <label className="font-bold">Match Threshold</label>
            <input
              type="number"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              className="border px-4 py-2 rounded"
            />
            <button
              onClick={loadMatches}
              className="bg-slate-950 text-white px-5 py-2 rounded font-bold"
            >
              Run Resolution
            </button>
          </div>

          {loading ? (
            <p className="font-bold">Loading matches...</p>
          ) : (
            <div className="bg-white rounded-xl border overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-100">
                  <tr>
                    <th className="p-4 text-left">Source A</th>
                    <th className="p-4 text-left">Source B</th>
                    <th className="p-4 text-left">CNIC A</th>
                    <th className="p-4 text-left">CNIC B</th>
                    <th className="p-4 text-left">Confidence</th>
                    <th className="p-4 text-left">Reason</th>
                  </tr>
                </thead>

                <tbody>
                  {matches.map((m, index) => (
                    <tr key={index} className="border-t">
                      <td className="p-4">{m.record_a?.source_collection}</td>
                      <td className="p-4">{m.record_b?.source_collection}</td>
                      <td className="p-4 font-mono">{m.record_a?.cnic}</td>
                      <td className="p-4 font-mono">{m.record_b?.cnic}</td>
                      <td className="p-4 font-black">{m.match_confidence}%</td>
                      <td className="p-4">{m.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {!matches.length && (
                <p className="p-6 text-slate-500">No matches found.</p>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}