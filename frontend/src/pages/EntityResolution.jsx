import React, { useEffect, useState } from "react";
import {
  Search,
  Sparkles,
  Share2,
  Car,
  Home,
  Zap,
  FileText,
  Database
} from "lucide-react";

import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";

import {
  searchEntityMatches,
  getEntityComparison,
  mergeIdentities,
  flagEntityForReview,
  runEntityResolution
} from "../api/api";

const typeIcon = {
  Vehicle: Car,
  Property: Home,
  Utility: Zap,
  "Tax Record": FileText,
  Record: Database
};

const typeColor = {
  Vehicle: "bg-green-100 text-green-700 border-green-200",
  Property: "bg-orange-100 text-orange-700 border-orange-200",
  Utility: "bg-purple-100 text-purple-700 border-purple-200",
  "Tax Record": "bg-red-100 text-red-700 border-red-200",
  Record: "bg-slate-100 text-slate-700 border-slate-200"
};

export default function EntityResolution() {
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [runningAI, setRunningAI] = useState(false);

  const loadMatches = async (q = "") => {
    try {
      const res = await searchEntityMatches(q);
      const data = res.data.matches || [];

      setMatches(data);

      if (data.length > 0) {
        setSelectedMatch(data[0]);
        await loadComparison(data[0].match_id);
      } else {
        setSelectedMatch(null);
        setComparison(null);
      }
    } catch (err) {
      console.error("Entity search failed:", err);
      setMatches([]);
      setSelectedMatch(null);
      setComparison(null);
    }
  };

  const loadComparison = async (matchId) => {
    if (!matchId) return;

    try {
      setLoading(true);
      const res = await getEntityComparison(matchId);
      setComparison(res.data);
    } catch (err) {
      console.error("Comparison failed:", err);
      setComparison(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAI = async () => {
    try {
      setRunningAI(true);
      await runEntityResolution();
      await loadMatches(query);
      alert("Entity resolution completed");
    } catch (err) {
      console.error("Run AI failed:", err);
      alert("Failed to run entity resolution");
    } finally {
      setRunningAI(false);
    }
  };

  useEffect(() => {
    loadMatches("");
  }, []);

  const selectMatch = async (match) => {
    setSelectedMatch(match);
    await loadComparison(match.match_id);
  };

  const handleMerge = async () => {
    if (!selectedMatch?.match_id) return;

    try {
      await mergeIdentities(selectedMatch.match_id);
      alert("Identities merged successfully");
      await loadMatches(query);
    } catch (err) {
      console.error("Merge failed:", err);
    }
  };

  const handleFlag = async () => {
    if (!selectedMatch?.match_id) return;

    try {
      await flagEntityForReview(selectedMatch.match_id);
      alert("Flagged for review");
      await loadMatches(query);
    } catch (err) {
      console.error("Flag failed:", err);
    }
  };

  const ai = comparison?.ai_logic || {};
  const conflict = comparison?.conflict_matrix || {};
  const recordCards = comparison?.record_cards || [];

  const groupedCards = {
    Vehicle: recordCards.filter((r) => r.type === "Vehicle"),
    Property: recordCards.filter((r) => r.type === "Property"),
    Utility: recordCards.filter((r) => r.type === "Utility"),
    "Tax Record": recordCards.filter((r) => r.type === "Tax Record")
  };

  return (
    <div className="flex min-h-screen bg-[#f5f6fb] text-slate-950">
      <Sidebar />

      <main className="flex-1">
        <Navbar />

        <div className="p-8 space-y-6">
          <div className="flex max-w-4xl gap-3">
            <div className="relative flex-1">
              <Search size={20} className="absolute left-4 top-3.5 text-slate-500" />

              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") loadMatches(query);
                }}
                placeholder="Search CNIC, Name, or Phone"
                className="w-full h-12 bg-blue-50 border border-blue-100 rounded-xl pl-12 pr-4 outline-none text-sm"
              />
            </div>

            <button
              onClick={() => loadMatches(query)}
              className="h-12 px-6 rounded-xl bg-slate-950 text-white font-black hover:bg-slate-800"
            >
              Search
            </button>

          </div>

          <div className="text-sm font-mono tracking-widest">
            Investigations <span className="mx-2">›</span>
            <span className="font-black">Entity Resolution</span>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-[340px_1fr] gap-6">
            <div className="space-y-6">
              <div className="bg-white border border-slate-300 rounded-xl p-6">
                <div className="flex items-start justify-between mb-5">
                  <h2 className="text-2xl font-black">
                    Identity <br /> Matches
                  </h2>

                  <span className="bg-teal-100 text-teal-800 px-4 py-3 text-xs font-mono uppercase">
                    {matches.filter((m) => Number(m.match_score) >= 80).length} High Risk
                  </span>
                </div>

                <div className="space-y-4 max-h-[420px] overflow-y-auto pr-1">
                  {matches.length ? (
                    matches.map((match) => {
                      const active = selectedMatch?.match_id === match.match_id;
                      const score = Number(match.match_score || 0);

                      return (
                        <button
                          key={match.match_id}
                          onClick={() => selectMatch(match)}
                          className={`w-full text-left rounded-lg border p-5 transition ${
                            active
                              ? "border-teal-700 bg-white shadow"
                              : "border-slate-200 bg-slate-50 hover:bg-blue-50"
                          }`}
                        >
                          <div className="flex justify-between gap-3">
                            <h3 className="text-lg font-black">
                              {match.display_name}
                            </h3>

                            <p
                              className={`font-black text-sm ${
                                score >= 85
                                  ? "text-red-600"
                                  : score >= 70
                                  ? "text-teal-700"
                                  : "text-slate-500"
                              }`}
                            >
                              {score}% Match
                            </p>
                          </div>

                          <div className="mt-3 text-xs font-mono text-slate-700 space-y-1">
                            <p>CNIC: {match.masked_cnic || "Unknown"}</p>
                            <p>Sources: {(match.sources || []).join(", ")}</p>
                            <p>Status: {match.status || "pending"}</p>
                          </div>
                        </button>
                      );
                    })
                  ) : (
                    <p className="text-sm text-slate-500">
                      No matches found. Click Run AI first, then search.
                    </p>
                  )}
                </div>
              </div>

              <div className="bg-[#06264a] text-white rounded-xl p-6">
                <div className="flex items-center gap-3 text-slate-300 uppercase tracking-widest font-black text-sm">
                  <Sparkles size={20} />
                  AI Investigation Logic
                </div>

                <p className="mt-6 text-slate-200 leading-7 text-sm">
                  Entity resolution suggests{" "}
                  <span className="text-cyan-300 font-black">
                    {ai.record_a_label || "Record A"}
                  </span>{" "}
                  and{" "}
                  <span className="text-cyan-300 font-black">
                    {ai.record_b_label || "Record B"}
                  </span>{" "}
                  are likely the same individual based on CNIC, name, address,
                  vehicle ownership, utility usage, property records and tax data.
                </p>

                <div className="mt-7 flex items-center gap-4">
                  <div className="w-16 h-16 rounded-full border-4 border-teal-400 flex items-center justify-center font-black">
                    {ai.confidence_score || selectedMatch?.match_score || 0}%
                  </div>

                  <p className="text-xs text-slate-300 font-mono">
                    Confidence Score for automated merge.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-white border border-slate-300 rounded-xl overflow-hidden">
                <div className="p-6 bg-[#f2f5ff] border-b border-slate-300 flex items-center justify-between">
                  <div>
                    <h2 className="text-3xl font-black">
                      Resolved Identity Record Cards
                    </h2>
                    <p className="text-slate-600 mt-1">
                      Vehicle, property, utility and tax records linked to this CNIC.
                    </p>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={handleFlag}
                      disabled={!selectedMatch}
                      className="px-6 h-14 border border-red-500 text-red-600 rounded-lg font-black disabled:opacity-40"
                    >
                      Flag for Review
                    </button>

                    <button
                      onClick={handleMerge}
                      disabled={!selectedMatch}
                      className="px-6 h-14 bg-slate-950 text-white rounded-lg font-black disabled:opacity-40"
                    >
                      Merge Identities
                    </button>
                  </div>
                </div>

                {loading ? (
                  <div className="h-[500px] flex items-center justify-center font-black text-slate-500">
                    Loading records...
                  </div>
                ) : (
                  <div className="p-6 space-y-8 min-h-[500px]">
                    <RecordSection title="Vehicle Records" records={groupedCards.Vehicle} />
                    <RecordSection title="Property Records" records={groupedCards.Property} />
                    <RecordSection title="Utility Records" records={groupedCards.Utility} />
                    <RecordSection title="Tax Records" records={groupedCards["Tax Record"]} />
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white border border-slate-300 rounded-xl p-6">
                  <h3 className="font-black text-lg mb-8">Conflict Matrix</h3>

                  <ConflictBar
                    label="Name Spelling"
                    value={conflict.name_spelling || "N/A"}
                    percent={conflict.name_score || 0}
                  />

                  <ConflictBar
                    label="CNIC Alignment"
                    value={conflict.cnic_alignment || "N/A"}
                    percent={conflict.cnic_score || 0}
                    danger={conflict.cnic_alignment === "Conflict"}
                  />

                  <ConflictBar
                    label="Address Proximity"
                    value={conflict.address_proximity || "N/A"}
                    percent={conflict.address_score || 0}
                    danger={conflict.address_proximity === "High Conflict"}
                  />
                </div>

                <div className="bg-white border border-slate-300 rounded-xl p-6 flex flex-col items-center justify-center text-center">
                  <div className="w-20 h-20 bg-blue-100 rounded-2xl flex items-center justify-center">
                    <Share2 size={36} />
                  </div>

                  <h2 className="text-2xl font-black mt-5">Network View</h2>

                  <p className="text-sm max-w-xs text-slate-600">
                    Visualize {comparison?.shared_nodes || 0} shared nodes
                    between these identities.
                  </p>

                  <button className="mt-8 text-teal-700 font-black tracking-widest">
                    Launch Knowledge Graph
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <footer className="fixed bottom-0 left-64 right-0 bg-white border-t border-slate-200 h-7 flex items-center justify-center gap-4 text-[11px] font-mono">
          <span className="text-red-600 font-bold">INTERNAL USE ONLY</span>
          <span>System Status: Operational</span>
          <span>Entity Resolution</span>
        </footer>
      </main>
    </div>
  );
}

function RecordSection({ title, records }) {
  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-black text-lg">{title}</h3>
        <span className="text-xs font-black text-slate-400">
          {records.length} record(s)
        </span>
      </div>

      {records.length ? (
        <div className="grid grid-cols-1 2xl:grid-cols-2 gap-5">
          {records.map((record) => (
            <RecordCard key={`${record.type}-${record.id}`} record={record} />
          ))}
        </div>
      ) : (
        <div className="border border-dashed border-slate-300 rounded-2xl p-6 bg-slate-50 text-slate-500 text-sm font-bold">
          No data found for this person in {title}.
        </div>
      )}
    </section>
  );
}

function RecordCard({ record }) {
  const Icon = typeIcon[record?.type] || Database;
  const color = typeColor[record?.type] || typeColor.Record;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-lg transition">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className={`w-12 h-12 rounded-xl border flex items-center justify-center ${color}`}>
            <Icon size={24} />
          </div>

          <div>
            <p className="text-[10px] uppercase tracking-widest font-black text-slate-400">
              {record?.source || "Source Record"}
            </p>

            <h3 className="text-lg font-black mt-1">
              {record?.name || "Unknown Person"}
            </h3>

            <p className="text-xs font-mono text-slate-500 mt-1">
              {record?.cnic || "N/A"}
            </p>
          </div>
        </div>

        <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase border ${color}`}>
          {record?.type || "Record"}
        </span>
      </div>

      <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Title" value={record?.title} />
        <Field label="Detail 1" value={record?.field1} />
        <Field label="Detail 2" value={record?.field2} />
        <Field label="Detail 3" value={record?.field3} />
        <Field label="Amount / Value" value={record?.amount} />
        <Field label="Address" value={record?.address} />
      </div>
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-widest text-slate-400 font-black">
        {label}
      </p>
      <p className="text-sm font-bold text-slate-800 mt-1">
        {value || "N/A"}
      </p>
    </div>
  );
}

function ConflictBar({ label, value, percent, danger }) {
  return (
    <div className="mb-7">
      <div className="flex justify-between mb-3">
        <span>{label}</span>
        <span className={`font-black ${danger ? "text-red-600" : "text-teal-700"}`}>
          {value}
        </span>
      </div>

      <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${danger ? "bg-red-600" : "bg-teal-700"}`}
          style={{ width: `${Math.min(Number(percent || 0), 100)}%` }}
        />
      </div>
    </div>
  );
}