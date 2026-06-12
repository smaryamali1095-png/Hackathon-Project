import React, { useEffect, useMemo, useState } from "react";
import {
  Search,
  User,
  Car,
  Home,
  Zap,
  FileText,
  Briefcase,
  Landmark,
  Plane,
  AlertTriangle
} from "lucide-react";

import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { searchCitizens, knowledgeGraphByCnic } from "../api/api";

const typeColor = {
  Person: "#2563eb",
  Vehicle: "#16a34a",
  Property: "#f97316",
  "Utility Meter": "#9333ea",
  "Tax Return": "#dc2626",
  Business: "#0f766e",
  "Bank Account": "#ca8a04",
  Travel: "#0891b2"
};

const typeIcon = {
  Person: User,
  Vehicle: Car,
  Property: Home,
  "Utility Meter": Zap,
  "Tax Return": FileText,
  Business: Briefcase,
  "Bank Account": Landmark,
  Travel: Plane
};

export default function KnowledgeGraph() {
  const [query, setQuery] = useState("");
  const [fiscalYear, setFiscalYear] = useState("");
  const [people, setPeople] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadPeople = async (q = "") => {
    try {
      const res = await searchCitizens(q);
      setPeople(res.data.citizens || []);
    } catch (err) {
      console.error("Citizen search failed:", err);
    }
  };

  useEffect(() => {
    loadPeople("");
  }, []);

  useEffect(() => {
    const delay = setTimeout(() => {
      loadPeople(query);
    }, 300);

    return () => clearTimeout(delay);
  }, [query]);

  const generateGraph = async (person) => {
    if (!person?.cnic) return;

    try {
      setLoading(true);
      setSelectedPerson(person);

      const res = await knowledgeGraphByCnic(person.cnic, fiscalYear);
      setGraph(res.data);
      localStorage.setItem("selected_cnic", person.cnic);
    } catch (err) {
      console.error("Graph generation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedPerson?.cnic) {
      generateGraph(selectedPerson);
    }
  }, [fiscalYear]);

  const risk = graph?.risk;

  return (
    <div className="flex min-h-screen bg-[#F4F6FB] text-slate-950">
      <Sidebar />

      <main className="flex-1">
        <Navbar />

        <div className="p-8 space-y-6">
          <div>
            <h1 className="text-4xl font-black">Knowledge Graph Layer</h1>
            <p className="text-slate-600 mt-2">
              Search taxpayers by CNIC/name, generate Neo4j-style relationship visualization,
              and compare risk by fiscal year.
            </p>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-1 space-y-5">
              <div className="bg-white border border-slate-200 rounded-xl p-5">
                <h2 className="font-black text-xl mb-4">Search Taxpayer</h2>

                <div className="relative">
                  <Search size={18} className="absolute left-3 top-3 text-slate-400" />

                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search CNIC or name..."
                    className="w-full border border-slate-300 rounded-lg pl-10 pr-3 py-3 text-sm outline-none"
                  />
                </div>

                <div className="mt-4">
                  <label className="text-xs font-black uppercase text-slate-500">
                    Fiscal Year
                  </label>

                  <select
                    value={fiscalYear}
                    onChange={(e) => setFiscalYear(e.target.value)}
                    className="w-full border border-slate-300 rounded-lg px-3 py-3 mt-1 text-sm"
                  >
                    <option value="">All Years</option>
                    <option value="2024">2024</option>
                    <option value="2025">2025</option>
                    <option value="2026">2026</option>
                  </select>
                </div>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                <div className="p-4 border-b bg-slate-50">
                  <h2 className="font-black">People List / Suggestions</h2>
                  <p className="text-xs text-slate-500">Click a person to generate graph</p>
                </div>

                <div className="max-h-[520px] overflow-y-auto">
                  {people.map((p) => (
                    <button
                      key={p.cnic}
                      onClick={() => generateGraph(p)}
                      className={`w-full text-left p-4 border-b hover:bg-blue-50 transition ${
                        selectedPerson?.cnic === p.cnic ? "bg-blue-50" : "bg-white"
                      }`}
                    >
                      <p className="font-black">{p.name || "Unknown Citizen"}</p>
                      <p className="font-mono text-xs text-slate-500">{p.cnic}</p>
                      <p className="text-xs text-slate-400 truncate">{p.address}</p>
                    </button>
                  ))}

                  {!people.length && (
                    <p className="p-5 text-slate-500 text-sm">No citizens found.</p>
                  )}
                </div>
              </div>
            </div>

            <div className="xl:col-span-3 space-y-6">
              {risk && <RiskPanel risk={risk} fiscalYear={fiscalYear} />}

              <div className="bg-white border border-slate-300 rounded-xl overflow-hidden">
                <div className="p-5 border-b bg-slate-50 flex items-center justify-between">
                  <div>
                    <h2 className="font-black text-2xl">
                      Neo4j-Inspired Graph Visualization
                    </h2>
                    <p className="text-sm text-slate-500">
                      Central person node with all linked vehicles, properties, utilities, tax records and travel logs.
                    </p>
                  </div>

                  <Legend />
                </div>

                <div className="h-[820px] relative bg-white overflow-auto">
                  {loading ? (
                    <div className="absolute inset-0 flex items-center justify-center font-black text-slate-500">
                      Generating visualization graph...
                    </div>
                  ) : graph?.found ? (
                    <GraphCanvas graph={graph} />
                  ) : (
                    <EmptyGraph />
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        <footer className="fixed bottom-0 left-64 right-0 bg-white border-t border-slate-200 h-7 flex items-center justify-center gap-4 text-[11px] font-mono">
          <span className="text-red-600 font-bold">INTERNAL USE ONLY</span>
          <span>Knowledge Graph Layer</span>
          <span>System Status: Operational</span>
        </footer>
      </main>
    </div>
  );
}

function RiskPanel({ risk, fiscalYear }) {
  const score = Math.min(Number(risk.risk_score || 0), 100);
  const deviationScore = Math.min(Number(risk.deviation_percentage || 0), 100);

  const color =
    score >= 85
      ? "text-red-700 bg-red-50 border-red-200"
      : score >= 60
      ? "text-orange-700 bg-orange-50 border-orange-200"
      : score >= 25
      ? "text-yellow-700 bg-yellow-50 border-yellow-200"
      : "text-emerald-700 bg-emerald-50 border-emerald-200";

  return (
    <div className={`border rounded-xl p-6 ${color}`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="text-xs font-black uppercase tracking-widest">
            Tax Compliance Deviation Score
          </p>

          <h2 className="text-5xl font-black mt-2">{score}/100</h2>

          <p className="font-bold mt-1">Risk Level: {risk.risk_level}</p>
        </div>

        <AlertTriangle size={42} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 text-sm">
        <RiskBox label="Fiscal Year" value={fiscalYear || "All"} />
        <RiskBox label="Declared Income" value={`PKR ${Number(risk.declared_income || 0).toLocaleString()}`} />
        <RiskBox label="Lifestyle Value" value={`PKR ${Number(risk.observed_lifestyle_value || 0).toLocaleString()}`} />
        <RiskBox label="Deviation Score" value={`${deviationScore}/100`} />
      </div>

      <p className="mt-5 text-sm font-semibold">
        Declared income is PKR {Number(risk.declared_income || 0).toLocaleString()}.
        Observed lifestyle value is PKR {Number(risk.observed_lifestyle_value || 0).toLocaleString()}.
        Final investigation score is {score}/100.
      </p>
    </div>
  );
}

function RiskBox({ label, value }) {
  return (
    <div className="bg-white/70 rounded-lg p-3 border">
      <p className="text-xs uppercase font-black opacity-70">{label}</p>
      <h3 className="font-black mt-1">{value}</h3>
    </div>
  );
}

function GraphCanvas({ graph }) {
  const layout = useMemo(() => {
    const nodes = graph.nodes || [];
    const edges = graph.edges || [];

    const person = nodes.find((n) => n.type === "Person");
    const others = nodes.filter((n) => n.type !== "Person");

    const width = 1300;
    const height = 760;
    const cx = width / 2;
    const cy = height / 2;

    const positioned = {};

    if (person) {
      positioned[person.id] = {
        ...person,
        x: cx,
        y: cy
      };
    }

    const typeOrder = [
      "Vehicle",
      "Property",
      "Utility Meter",
      "Tax Return",
      "Travel",
      "Business",
      "Bank Account"
    ];

    const grouped = {};

    typeOrder.forEach((type) => {
      grouped[type] = others.filter((n) => n.type === type);
    });

    const typeAngles = {
      Vehicle: -20,
      Property: 200,
      "Utility Meter": 160,
      "Tax Return": -90,
      Travel: 60,
      Business: 20,
      "Bank Account": 110
    };

    Object.entries(grouped).forEach(([type, group]) => {
      if (!group.length) return;

      const baseAngle = typeAngles[type] ?? 0;
      const spread = Math.min(80, 20 * group.length);
      const radius = 250 + Math.min(group.length, 5) * 35;

      group.forEach((node, index) => {
        const offset =
          group.length === 1
            ? 0
            : -spread / 2 + (spread / (group.length - 1)) * index;

        const angle = ((baseAngle + offset) * Math.PI) / 180;

        positioned[node.id] = {
          ...node,
          x: cx + radius * Math.cos(angle),
          y: cy + radius * Math.sin(angle)
        };
      });
    });

    return {
      width,
      height,
      nodeMap: positioned,
      nodes: Object.values(positioned),
      edges
    };
  }, [graph]);

  return (
    <div className="min-w-[1300px] flex justify-center py-8">
      <svg
        width={layout.width}
        height={layout.height}
        viewBox={`0 0 ${layout.width} ${layout.height}`}
        className="bg-white"
      >
        <defs>
          <marker
            id="arrow"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,6 L9,3 z" fill="#64748b" />
          </marker>
        </defs>

        {layout.edges.map((edge, index) => {
          const source = layout.nodeMap[edge.source];
          const target = layout.nodeMap[edge.target];

          if (!source || !target) return null;

          const dx = target.x - source.x;
          const dy = target.y - source.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;

          const sourcePadding = 58;
          const targetPadding = 58;

          const x1 = source.x + (dx / distance) * sourcePadding;
          const y1 = source.y + (dy / distance) * sourcePadding;
          const x2 = target.x - (dx / distance) * targetPadding;
          const y2 = target.y - (dy / distance) * targetPadding;

          const midX = (x1 + x2) / 2;
          const midY = (y1 + y2) / 2;

          return (
            <g key={index}>
              <line
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#94a3b8"
                strokeWidth="2"
                markerEnd="url(#arrow)"
              />

              <rect
                x={midX - 45}
                y={midY - 13}
                width="90"
                height="26"
                rx="13"
                fill="white"
                stroke="#cbd5e1"
              />

              <text
                x={midX}
                y={midY + 4}
                textAnchor="middle"
                fontSize="10"
                fontWeight="900"
                fill="#334155"
              >
                {edge.label}
              </text>
            </g>
          );
        })}

        {layout.nodes.map((node) => (
          <GraphNodeSvg key={node.id} node={node} />
        ))}
      </svg>
    </div>
  );
}

function GraphNodeSvg({ node }) {
  const color = typeColor[node.type] || "#475569";
  const Icon = typeIcon[node.type] || User;

  return (
    <foreignObject x={node.x - 75} y={node.y - 65} width="150" height="145">
      <div className="flex flex-col items-center text-center">
        <div
          className="w-20 h-20 rounded-2xl flex items-center justify-center shadow-xl border-4 border-white text-white"
          style={{ backgroundColor: color }}
        >
          <Icon size={32} />
        </div>

        <div className="mt-2 bg-white border border-slate-200 rounded-lg px-3 py-1 shadow-sm max-w-[145px]">
          <p className="text-[11px] font-black truncate">{node.label}</p>
          <p className="text-[9px] font-bold text-slate-500 uppercase">
            {node.type}
          </p>
        </div>
      </div>
    </foreignObject>
  );
}

function Legend() {
  const items = [
    "Person",
    "Vehicle",
    "Property",
    "Utility Meter",
    "Tax Return",
    "Business",
    "Bank Account",
    "Travel"
  ];

  return (
    <div className="flex flex-wrap gap-2 max-w-xl justify-end">
      {items.map((item) => (
        <span
          key={item}
          className="text-[10px] font-black uppercase px-2 py-1 rounded-full border"
        >
          <i
            className="inline-block w-2 h-2 rounded-full mr-1"
            style={{ backgroundColor: typeColor[item] }}
          />
          {item}
        </span>
      ))}
    </div>
  );
}

function EmptyGraph() {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
      <div className="w-24 h-24 rounded-full bg-slate-100 flex items-center justify-center">
        <Search size={42} className="text-slate-400" />
      </div>

      <h2 className="text-2xl font-black mt-4">Select a taxpayer</h2>

      <p className="text-slate-500 mt-2 max-w-md">
        Search by CNIC or select a person from the list to generate the knowledge graph.
      </p>
    </div>
  );
}