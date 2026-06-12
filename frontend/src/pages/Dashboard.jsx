import React, { useEffect, useMemo, useState } from "react";
import {
  Calendar,
  Download,
  Filter,
  RefreshCcw,
  Users,
  MapPin
} from "lucide-react";

import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";

import {
  riskRanking,
  summaryStats,
  graphAiAnomalies,
  regionalCompliance,
  reportUrl
} from "../api/api";

export default function Dashboard() {
  const [stats, setStats] = useState({});
  const [ranking, setRanking] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [regions, setRegions] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadDashboard = async () => {
    try {
      setLoading(true);

      const [statsRes, rankingRes, anomalyRes, regionRes] =
        await Promise.all([
          summaryStats(),
          riskRanking(),
          graphAiAnomalies(),
          regionalCompliance()
        ]);

      setStats(statsRes.data || {});
      setRanking(rankingRes.data.ranking || []);
      setAnomalies(anomalyRes.data.graph_ai_anomalies || []);
      setRegions(regionRes.data.regions || []);
      setSelectedRegion(regionRes.data.regions?.[0] || null);
    } catch (err) {
      console.error("Dashboard loading failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const highRisk = useMemo(
    () =>
      ranking.filter((x) =>
        ["High", "Critical"].includes(x.risk_level)
      ).length,
    [ranking]
  );

  const mediumRisk = useMemo(
    () => ranking.filter((x) => x.risk_level === "Medium").length,
    [ranking]
  );

  const nonFilers = useMemo(
    () =>
      ranking.filter(
        (x) => String(x.filer_status).toLowerCase() === "non-filer"
      ).length,
    [ranking]
  );

  const riskPercent = (level) => {
    if (!ranking.length) return 0;
    return Math.round(
      (ranking.filter((x) => x.risk_level === level).length /
        ranking.length) *
        100
    );
  };

  const exportPdf = () => {
    if (ranking[0]?.cnic) {
      window.open(reportUrl(ranking[0].cnic), "_blank");
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-[#F4F6FB]">
        <Sidebar />
        <main className="flex-1">
          <Navbar />
          <div className="p-10 font-bold text-slate-600">
            Loading dashboard...
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#F4F6FB] text-slate-950">
      <Sidebar />

      <main className="flex-1">
        <Navbar />

        <div className="p-8 space-y-8 pb-14">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-black tracking-tight">
                Intelligence Overview
              </h1>
              <p className="text-slate-600 mt-2 text-lg">
                Real-time analytical summary of national tax compliance and risk vectors.
              </p>
            </div>

            <div className="flex gap-3">
              <button className="flex items-center gap-2 px-5 py-3 bg-white border border-slate-300 rounded-lg text-sm font-semibold">
                <Calendar size={16} />
                Last 30 Days
              </button>

              <button
                onClick={exportPdf}
                className="flex items-center gap-2 px-5 py-3 bg-slate-950 text-white rounded-lg text-sm font-bold"
              >
                <Download size={16} />
                Export PDF
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <MetricCard
              title="Citizens Analyzed"
              value={stats.citizens || 0}
              sub="Processed profiles"
              icon={<Users />}
            />

            <MetricCard
              title="High-Risk Individuals"
              value={highRisk}
              sub="Requires Action"
              tone="red"
            />

            <MetricCard
              title="Medium-Risk Cases"
              value={mediumRisk}
              sub="Under Monitoring"
              tone="amber"
            />

            <MetricCard
              title="Non-Filers Detected"
              value={nonFilers}
              sub="AI Suggested Targeting"
              tone="teal"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-7">
              <div className="flex justify-between items-center mb-8">
                <h2 className="text-2xl font-black">
                  Risk Distribution
                </h2>

                <div className="flex gap-4 text-xs font-bold">
                  <span className="flex items-center gap-2">
                    <i className="w-3 h-3 rounded-full bg-slate-950"></i>
                    Critical
                  </span>
                  <span className="flex items-center gap-2">
                    <i className="w-3 h-3 rounded-full bg-teal-700"></i>
                    High
                  </span>
                  <span className="flex items-center gap-2">
                    <i className="w-3 h-3 rounded-full bg-cyan-300"></i>
                    Medium
                  </span>
                </div>
              </div>

              {[
                ["Critical", riskPercent("Critical")],
                ["High", riskPercent("High")],
                ["Medium", riskPercent("Medium")],
                ["Low", riskPercent("Low")]
              ].map(([label, value]) => (
                <div key={label} className="mb-7">
                  <div className="flex justify-between text-sm font-bold mb-2">
                    <span>{label}</span>
                    <span>{value}% Total Risk</span>
                  </div>

                  <div className="h-4 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-slate-950 via-teal-700 to-cyan-300 rounded-full"
                      style={{ width: `${value}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>

            <RegionalMapCard
              regions={regions}
              selectedRegion={selectedRegion}
              setSelectedRegion={setSelectedRegion}
            />
          </div>

          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            <div className="flex justify-between items-center p-6 bg-[#F1F5FF] border-b">
              <div>
                <h2 className="text-2xl font-black">
                  Recent High-Risk Detects
                </h2>
                <p className="text-slate-600">
                  Prioritized by AI Confidence Score
                </p>
              </div>

              <div className="flex gap-3">
                <button className="p-3 border bg-white rounded">
                  <Filter size={18} />
                </button>
                <button onClick={loadDashboard} className="p-3 border bg-white rounded">
                  <RefreshCcw size={18} />
                </button>
              </div>
            </div>

            <table className="w-full text-sm">
              <thead className="bg-[#DCE8FF] text-slate-700 uppercase tracking-widest text-xs">
                <tr>
                  <th className="text-left p-5">Name / Subject</th>
                  <th className="text-left p-5">CNIC / ID</th>
                  <th className="text-left p-5">Primary Flags</th>
                  <th className="text-left p-5">Risk Score</th>
                  <th className="text-left p-5">Confidence</th>
                  <th className="text-left p-5">Action</th>
                </tr>
              </thead>

              <tbody>
                {ranking.slice(0, 10).map((r) => {
                  const anomaly = anomalies.find((a) => a.cnic === r.cnic);

                  return (
                    <tr key={r.cnic} className="border-b border-slate-200">
                      <td className="p-5 font-bold">
                        {r.name || r.full_name || "Citizen Profile"}
                      </td>

                      <td className="p-5 font-mono text-xs">
                        {r.cnic}
                      </td>

                      <td className="p-5">
                        {r.vehicle_value > 0 && (
                          <Badge text="Vehicle Asset" color="red" />
                        )}

                        {r.property_value > 0 && (
                          <Badge text="Property Asset" color="teal" />
                        )}

                        {r.monthly_utility_bill > 150000 && (
                          <Badge text="High Utility" color="red" />
                        )}

                        {String(r.filer_status).toLowerCase() === "non-filer" && (
                          <Badge text="Non-Filer" color="red" />
                        )}
                      </td>

                      <td className="p-5">
                        <div className="flex items-center gap-3">
                          <div className="w-20 h-2 bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                r.risk_score >= 85
                                  ? "bg-red-600"
                                  : r.risk_score >= 60
                                  ? "bg-orange-500"
                                  : "bg-teal-600"
                              }`}
                              style={{ width: `${r.risk_score}%` }}
                            ></div>
                          </div>
                          <b>{r.risk_score}</b>
                        </div>
                      </td>

                      <td className="p-5">
                        <div className="w-9 h-9 border-4 border-teal-600 border-t-transparent rounded-full"></div>
                        <p className="text-xs mt-1">
                          {anomaly?.graph_anomaly_score || r.risk_score}%
                        </p>
                      </td>

                      <td className="p-5">
                        <button
                          onClick={() => {
                            localStorage.setItem("selected_cnic", r.cnic);
                            window.location.href = "/investigation";
                          }}
                          className="text-teal-700 font-black"
                        >
                          Investigate
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            <div className="flex justify-between items-center px-6 py-4 bg-slate-50">
              <p className="text-sm text-slate-600">
                Showing 1-{Math.min(10, ranking.length)} of {ranking.length} high-risk detects
              </p>

              <div className="flex gap-2">
                <button className="border px-4 py-2 bg-white rounded text-sm">
                  Previous
                </button>
                <button className="bg-slate-950 text-white px-4 py-2 rounded text-sm">
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>

        <footer className="fixed bottom-0 left-64 right-0 bg-white border-t border-slate-200 h-7 flex items-center justify-center gap-4 text-[11px] font-mono">
          <span className="text-red-600 font-bold">INTERNAL USE ONLY</span>
          <span>System Status: Operational</span>
          <span>Last Sync: Live</span>
          <span>© 2024 National Tax Infrastructure</span>
        </footer>
      </main>
    </div>
  );
}

function RegionalMapCard({ regions, selectedRegion, setSelectedRegion }) {
  const maxRisk = Math.max(...regions.map((r) => r.risk_score || 0), 1);

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-7">
      <div className="flex justify-between items-start mb-5">
        <div>
          <h2 className="text-2xl font-black">
            Regional Compliance Insights
          </h2>
          <p className="text-slate-600 text-sm">
            Click province/region to inspect database-driven compliance.
          </p>
        </div>

        <MapPin className="text-teal-700" />
      </div>

      <div className="relative h-72 rounded-xl overflow-hidden bg-gradient-to-br from-slate-800 to-teal-300 p-4">
        <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_center,_white_1px,_transparent_1px)] [background-size:24px_24px]"></div>

        {regions.map((r, index) => {
          const positions = [
            "left-[45%] top-[38%]",
            "left-[38%] top-[65%]",
            "left-[54%] top-[22%]",
            "left-[22%] top-[55%]",
            "left-[58%] top-[42%]"
          ];

          const size = 18 + ((r.risk_score || 0) / maxRisk) * 22;

          return (
            <button
              key={r.region}
              onClick={() => setSelectedRegion(r)}
              className={`absolute ${positions[index % positions.length]} rounded-full border-2 border-white shadow-lg transition hover:scale-110 ${
                selectedRegion?.region === r.region
                  ? "bg-red-400"
                  : "bg-cyan-200"
              }`}
              style={{
                width: `${size}px`,
                height: `${size}px`
              }}
              title={r.region}
            ></button>
          );
        })}

        <div className="absolute left-8 top-8 bg-slate-950 text-white px-4 py-3 rounded shadow-xl">
          <p className="text-xs uppercase tracking-widest">
            {selectedRegion?.region || "Region"}
          </p>
          <h3 className="font-black">
            Compliance: {selectedRegion?.compliance || 0}%
          </h3>
        </div>

        <div className="absolute right-6 bottom-6 bg-red-100 text-red-700 px-4 py-3 rounded border border-red-300">
          <p className="text-xs uppercase font-black">
            Risk Score
          </p>
          <h3 className="text-xl font-black">
            {selectedRegion?.risk_score || 0}
          </h3>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mt-5 text-sm">
        <InfoBox label="Citizens" value={selectedRegion?.citizens || 0} />
        <InfoBox label="Vehicles" value={selectedRegion?.vehicles || 0} />
        <InfoBox label="Properties" value={selectedRegion?.properties || 0} />
        <InfoBox label="Utilities" value={selectedRegion?.utilities || 0} />
      </div>
    </div>
  );
}

function InfoBox({ label, value }) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
      <p className="text-xs text-slate-500 font-bold uppercase">{label}</p>
      <h4 className="text-xl font-black">{value}</h4>
    </div>
  );
}

function MetricCard({ title, value, sub, tone, icon }) {
  const color =
    tone === "red"
      ? "text-red-700 border-r-4 border-red-700"
      : tone === "amber"
      ? "text-orange-600"
      : tone === "teal"
      ? "text-teal-700 border-r-4 border-teal-700"
      : "text-slate-950";

  return (
    <div className={`bg-white border border-slate-200 rounded-xl p-6 ${color}`}>
      <div className="flex justify-between">
        <p className="text-xs font-black uppercase tracking-widest text-slate-600">
          {title}
        </p>
        <div className="text-slate-200">{icon}</div>
      </div>

      <h2 className="text-5xl font-black mt-4">{value}</h2>

      <p className="text-xs mt-4 font-bold">{sub}</p>
    </div>
  );
}

function Badge({ text, color }) {
  return (
    <span
      className={`inline-block px-3 py-1 rounded-full text-[10px] font-black uppercase mr-2 ${
        color === "red"
          ? "bg-red-50 text-red-700"
          : "bg-teal-50 text-teal-700"
      }`}
    >
      {text}
    </span>
  );
}