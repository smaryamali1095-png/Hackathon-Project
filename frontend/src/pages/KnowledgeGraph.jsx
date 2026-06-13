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
  AlertTriangle,
  BadgeCheck,
  Database
} from "lucide-react";

import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { searchCitizens, knowledgeGraphByCnic, calculateAllRiskScores } from "../api/api";

const YEARS = ["All", ...Array.from({ length: 11 }, (_, i) => String(2016 + i))];

const typeColor = {
  Person: "#2563eb",         // Sharp Blue Accent
  Alias: "#7c3aed",          // Deep Royal Violet
  Vehicle: "#16a34a",        // Forest Green
  Property: "#ea580c",       // Rich Amber Orange
  "Utility Meter": "#9333ea", // Vibrant Purple
  "Tax Return": "#dc2626",   // Pure Crimson
  Business: "#0f766e",       // Sharp Teal
  "Bank Account": "#ca8a04", // Dark Brass Gold
  Travel: "#0891b2"          // Oceanic Cyan
};

const typeIcon = {
  Person: User,
  Alias: BadgeCheck,
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
  const [fiscalYear, setFiscalYear] = useState("2026");
  const [people, setPeople] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(false);
  const [riskCalculating, setRiskCalculating] = useState(false);
  const [riskSaved, setRiskSaved] = useState(false);
  // Tracks active node details mapping for the side panel card inspector
  const [activeSelectedNodeId, setActiveSelectedNodeId] = useState(null);

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
  const autoCalculateRiskScores = async () => {
    try {
      setRiskCalculating(true);
      setRiskSaved(false);

      const res = await calculateAllRiskScores();

      console.log("Risk scores calculated and saved in MongoDB:", res.data);

      setRiskSaved(true);
    } catch (err) {
      console.error("Auto risk calculation failed:", err);
      setRiskSaved(false);
    } finally {
      setRiskCalculating(false);
    }
  };

  autoCalculateRiskScores();
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
      setActiveSelectedNodeId(null); // Clear detailed item view on new target trace

      const res = await knowledgeGraphByCnic(person.cnic, fiscalYear);
      setGraph(res.data);
      localStorage.setItem("selected_cnic", person.cnic);
    } catch (err) {
      console.error("Graph generation failed:", err);
      setGraph(null);
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
    <div className="flex min-h-screen bg-[#F8FAFC] text-slate-900 selection:bg-blue-100 selection:text-blue-900">
      <Sidebar />

      <main className="flex-1 pb-12">
        <Navbar />

        <div className="p-8 space-y-6">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-slate-900">
              Knowledge Graph Layer
            </h1>
            <p className="text-slate-500 mt-1.5 text-sm max-w-2xl">
              Search by CNIC or name to systematically isolate aliases and view cross-referenced entity assets.
            </p>
          </div>
          {riskCalculating && (
  <div className="mt-4 bg-blue-50 border border-blue-200 text-blue-700 rounded-xl px-4 py-3 text-sm font-bold">
    Calculating risk scores and saving to MongoDB...
  </div>
)}

{riskSaved && (
  <div className="mt-4 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl px-4 py-3 text-sm font-bold">
    Risk scores calculated and saved in MongoDB successfully.
  </div>
)}
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-1 space-y-5">
              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <h2 className="font-black text-lg text-slate-800 mb-4 tracking-tight">Search Taxpayer</h2>

                <div className="relative">
                  <Search size={18} className="absolute left-3 top-3.5 text-slate-400" />

                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search CNIC or name..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-3 py-3 text-sm text-slate-900 placeholder-slate-400 outline-none focus:border-blue-500 focus:bg-white transition-all duration-150"
                  />
                </div>

                <div className="mt-4">
                  <label className="text-[11px] font-black uppercase tracking-wider text-slate-500">
                    Fiscal Year
                  </label>

                  <select
                    value={fiscalYear}
                    onChange={(e) => setFiscalYear(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-3 mt-1.5 text-sm text-slate-800 outline-none focus:border-blue-500 focus:bg-white transition-all"
                  >
                    {YEARS.map((year) => (
                      <option key={year} value={year}>
                        {year}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
                <div className="p-4 border-b border-slate-100 bg-slate-50/70">
                  <h2 className="font-black text-sm text-slate-800 tracking-tight">People List / Suggestions</h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Unified accounts containing mapped identity links.
                  </p>
                </div>

                <div className="max-h-[520px] overflow-y-auto divide-y divide-slate-100 custom-scrollbar">
                  {people.map((p, index) => (
                    <button
                      key={`${p.cnic}-${index}`}
                      onClick={() => generateGraph(p)}
                      className={`w-full text-left p-4 hover:bg-slate-50 transition-all duration-150 block ${
                        selectedPerson?.cnic === p.cnic ? "bg-blue-50/80 border-l-4 border-blue-600" : "bg-transparent"
                      }`}
                    >
                      <p className="font-black text-slate-900 text-sm">
                        {p.name || "Unknown Citizen"}
                      </p>

                      <p className="font-mono text-[11px] text-blue-600 font-semibold mt-0.5">
                        {p.cnic}
                      </p>

                      <p className="text-xs text-slate-500 truncate mt-0.5">
                        {p.address || "No address found"}
                      </p>

                      {p.all_names?.length > 1 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {p.all_names.slice(1, 5).map((alias, aliasIndex) => (
                            <span
                              key={aliasIndex}
                              className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 text-[10px] font-medium"
                            >
                              {alias}
                            </span>
                          ))}
                        </div>
                      )}
                    </button>
                  ))}

                  {!people.length && (
                    <p className="p-5 text-slate-400 text-sm text-center">
                      No citizens found.
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="xl:col-span-3 space-y-6">
              {risk && <RiskPanel risk={risk} fiscalYear={fiscalYear} />}

              <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
                <div className="p-5 border-b border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <h2 className="font-black text-xl text-slate-800 tracking-tight">
                      Neo4j-Inspired Graph Visualization
                    </h2>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Central user node trace for fiscal year {fiscalYear}. Click nodes to drill into data maps.
                    </p>
                  </div>

                  <Legend />
                </div>

                {loading ? (
                  <div className="h-[820px] flex flex-col gap-2 items-center justify-center font-bold text-slate-400 bg-white">
                    <div className="w-7 h-7 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-xs tracking-wider text-slate-400 uppercase font-mono mt-1">
                      Querying relational clusters...
                    </span>
                  </div>
                ) : graph?.found ? (
                  <div className="grid grid-cols-1 2xl:grid-cols-[1fr_340px] h-[820px] bg-[#FAFBFD]">
                    <div className="overflow-auto border-r border-slate-200/80 relative custom-scrollbar">
                      <GraphCanvas 
                        graph={graph} 
                        activeSelectedNodeId={activeSelectedNodeId}
                        setActiveSelectedNodeId={setActiveSelectedNodeId}
                      />
                    </div>

                    <div className="bg-white">
                      <GraphRecordCard 
                        graph={graph} 
                        activeSelectedNodeId={activeSelectedNodeId} 
                      />
                    </div>
                  </div>
                ) : (
                  <div className="h-[820px] relative bg-white">
                    <EmptyGraph />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <footer className="fixed bottom-0 left-64 right-0 bg-white border-t border-slate-200 h-8 flex items-center justify-center gap-6 text-[11px] font-mono text-slate-400 z-50">
          <span className="text-red-600 font-black tracking-wider">INTERNAL USE ONLY</span>
          <span className="w-1 h-1 rounded-full bg-slate-300"></span>
          <span>Knowledge Graph Layer</span>
          <span className="w-1 h-1 rounded-full bg-slate-300"></span>
          <span>Fiscal Year: {fiscalYear}</span>
          <span className="w-1 h-1 rounded-full bg-slate-300"></span>
          <span className="flex items-center gap-1.5 text-slate-500 font-sans font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Online
          </span>
        </footer>
      </main>
    </div>
  );
}

function getRecordPersonName(record, fallbackName) {
  const data = record?.data || {};

  return (
    data.owner_name ||
    data.consumer_name ||
    data.full_name ||
    data.buyer_name ||
    data.traveler_name ||
    fallbackName ||
    "Unknown Person"
  );
}

function GraphRecordCard({ graph, activeSelectedNodeId }) {
  const citizenName =
    graph?.citizen?.name ||
    graph?.nodes?.find((n) => n.type === "Person")?.label ||
    "Unknown Citizen";

  const allNodes = graph?.nodes || [];
  const records = allNodes.filter((node) => node.type !== "Person");

  const highlightedNode = activeSelectedNodeId 
    ? allNodes.find(n => n.id === activeSelectedNodeId) 
    : null;

  return (
    <div className="h-full flex flex-col overflow-hidden bg-white border-l border-slate-100">
      <div className="p-5 bg-slate-50 border-b border-slate-200/60">
        <p className="text-[10px] font-black uppercase tracking-widest text-blue-600">
          {highlightedNode ? `${highlightedNode.type} Properties` : "Selected Profile Data"}
        </p>

        <h3 className="font-black text-lg truncate mt-0.5 text-slate-900">
          {highlightedNode ? highlightedNode.label : citizenName}
        </h3>

        <p className="font-mono text-[11px] text-slate-400 tracking-tight truncate mt-0.5">
          {highlightedNode && highlightedNode.type !== "Person" 
            ? `Node UID: ${highlightedNode.id}` 
            : (graph?.citizen?.cnic || graph?.cnic || "No CNIC Data")}
        </p>
      </div>

      <div className="p-4 flex-1 overflow-y-auto space-y-3 custom-scrollbar">
        {highlightedNode ? (
          <div className="bg-slate-50/50 border border-slate-200 rounded-2xl p-4 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center text-white shrink-0 shadow-sm"
                style={{ backgroundColor: typeColor[highlightedNode.type] || "#64748b" }}
              >
                {React.createElement(typeIcon[highlightedNode.type] || Database, { size: 18 })}
              </div>
              <div>
                <span className="text-[9px] font-black uppercase px-2 py-0.5 rounded-full bg-white border border-slate-300 text-slate-700">
                  {highlightedNode.type}
                </span>
              </div>
            </div>

            <div className="space-y-2 font-mono text-xs">
              <div className="bg-white p-2.5 rounded-xl border border-slate-200/60">
                <span className="text-slate-400 block text-[9px] uppercase font-bold tracking-wider">Node Name</span>
                <span className="text-slate-900 font-sans font-black text-sm">{highlightedNode.label}</span>
              </div>
              
              {highlightedNode.data && Object.entries(highlightedNode.data).map(([key, val]) => (
                <div key={key} className="bg-white p-2.5 rounded-xl border border-slate-200/60">
                  <span className="text-slate-400 block text-[9px] uppercase tracking-wider">{key.replace(/_/g, ' ')}</span>
                  <span className="text-slate-800 font-semibold break-all">
                    {typeof val === 'number' ? val.toLocaleString() : String(val)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          records.length ? (
            records.map((record) => {
              const Icon = typeIcon[record.type] || Database;
              const color = typeColor[record.type] || "#64748b";
              const recordPersonName = getRecordPersonName(record, citizenName);

              return (
                <div
                  key={record.id}
                  className="bg-white border border-slate-200/80 rounded-xl p-3.5 shadow-sm hover:border-slate-300 transition duration-150"
                >
                  <div className="flex items-start gap-3">
                    <div
                      className="w-9 h-9 rounded-xl flex items-center justify-center text-white shrink-0 shadow-sm"
                      style={{ backgroundColor: color }}
                    >
                      <Icon size={16} />
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="font-black text-xs text-slate-800 truncate">
                          {recordPersonName}
                        </p>

                        <span 
                          className="text-[8px] font-black uppercase px-1.5 py-0.5 rounded shrink-0"
                          style={{ backgroundColor: `${color}12`, color: color }}
                        >
                          {record.type}
                        </span>
                      </div>

                      <p className="text-[11px] font-mono font-bold text-slate-600 truncate mt-1">
                        {record.label}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <p className="text-sm text-slate-400 text-center py-8">No matching records available.</p>
          )
        )}
      </div>
    </div>
  );
}

function RiskPanel({ risk, fiscalYear }) {
  const score = Math.min(Number(risk.risk_score || 0), 100);
  const deviationScore = Math.min(Number(risk.deviation_percentage || 0), 100);

  const colors =
    score >= 85
      ? { border: "border-red-200", bg: "bg-red-50/50", text: "text-red-700", fill: "#dc2626" }
      : score >= 60
      ? { border: "border-orange-200", bg: "bg-orange-50/50", text: "text-orange-700", fill: "#ea580c" }
      : score >= 25
      ? { border: "border-yellow-200", bg: "bg-yellow-50/60", text: "text-yellow-700", fill: "#ca8a04" }
      : { border: "border-emerald-200", bg: "bg-emerald-50/50", text: "text-emerald-700", fill: "#16a34a" };

  return (
    <div className={`border rounded-2xl p-6 ${colors.border} ${colors.bg} shadow-sm`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="text-xs font-black uppercase tracking-widest text-slate-500">
            Tax Compliance Deviation Score
          </p>

          <h2 className="text-5xl font-black mt-1 tracking-tight text-slate-900">
            {score}<span className="text-lg text-slate-400 font-normal">/100</span>
          </h2>

          <p className={`font-bold mt-1 text-sm ${colors.text}`}>Risk Level: {risk.risk_level}</p>
        </div>

        <AlertTriangle size={32} style={{ color: colors.fill }} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5 text-sm">
        <RiskBox label="Fiscal Year" value={fiscalYear} />
        <RiskBox
          label="Declared Income"
          value={`PKR ${Number(risk.declared_income || 0).toLocaleString()}`}
        />
        <RiskBox
          label="Lifestyle Value"
          value={`PKR ${Number(risk.observed_lifestyle_value || 0).toLocaleString()}`}
        />
        <RiskBox label="Deviation Score" value={`${score}/100`} />
      </div>
    </div>
  );
}

function RiskBox({ label, value }) {
  return (
    <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-sm">
      <p className="text-[10px] uppercase font-black tracking-wider text-slate-400">{label}</p>
      <h3 className="font-black mt-0.5 text-slate-800 text-sm font-mono">{value}</h3>
    </div>
  );
}

function GraphCanvas({ graph, activeSelectedNodeId, setActiveSelectedNodeId }) {
  const layout = useMemo(() => {
    const nodes = graph.nodes || [];
    const edges = graph.edges || [];

    const person = nodes.find((n) => n.type === "Person");
    const others = nodes.filter((n) => n.type !== "Person");

    const width = 1050;
    const height = 760;
    const cx = width * 0.45;
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
      "Alias",
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
      Alias: -140,
      Vehicle: -10,
      Property: 210,
      "Utility Meter": 160,
      "Tax Return": -90,
      Travel: 60,
      Business: 20,
      "Bank Account": 110
    };

    Object.entries(grouped).forEach(([type, group]) => {
      if (!group.length) return;

      const baseAngle = typeAngles[type] ?? 0;
      const spread = Math.min(80, 18 * group.length);
      const radius = 200 + Math.min(group.length, 5) * 25;

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
    <div className="min-w-[1050px] flex justify-start py-8 pl-6">
      <svg
        width={layout.width}
        height={layout.height}
        viewBox={`0 0 ${layout.width} ${layout.height}`}
        className="bg-[#FAFBFD]"
      >
        <defs>
          {/* Subtle grid mesh structure */}
          <pattern id="light-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#E2E8F0" strokeWidth="0.75" />
          </pattern>

          <marker
            id="arrow"
            markerWidth="8"
            markerHeight="8"
            refX="17"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,6 L8,3 z" fill="#94A3B8" />
          </marker>
        </defs>

        <rect width={layout.width} height={layout.height} fill="url(#light-grid)" />

        {/* Connections Mapping Line Mesh */}
        {layout.edges.map((edge, index) => {
          const source = layout.nodeMap[edge.source];
          const target = layout.nodeMap[edge.target];

          if (!source || !target) return null;

          const dx = target.x - source.x;
          const dy = target.y - source.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;

          const x1 = source.x + (dx / distance) * 44;
          const y1 = source.y + (dy / distance) * 44;
          const x2 = target.x - (dx / distance) * 48;
          const y2 = target.y - (dy / distance) * 48;

          const midX = (x1 + x2) / 2;
          const midY = (y1 + y2) / 2;

          return (
            <g key={index}>
              <line
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#CBD5E1"
                strokeWidth="2"
                markerEnd="url(#arrow)"
              />

              {/* Edge Property Type Label Flag */}
              <g transform={`translate(${midX}, ${midY})`}>
                <rect
                  x="-40"
                  y="-11"
                  width="80"
                  height="22"
                  rx="6"
                  fill="white"
                  stroke="#E2E8F0"
                  strokeWidth="1.5"
                  className="shadow-sm"
                />
                <text
                  textAnchor="middle"
                  y="3"
                  fontSize="9"
                  fontWeight="bold"
                  className="fill-slate-500 font-mono tracking-wide uppercase text-[8px]"
                >
                  {edge.label}
                </text>
              </g>
            </g>
          );
        })}

        {/* Interactive Node Render Cycle */}
        {layout.nodes.map((node) => {
          const isSelected = activeSelectedNodeId === node.id;
          return (
            <g 
              key={node.id} 
              onClick={() => setActiveSelectedNodeId(node.id)}
              className="cursor-pointer select-none group"
            >
              <GraphNodeSvg node={node} isSelected={isSelected} />
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function GraphNodeSvg({ node, isSelected }) {
  const baseColor = typeColor[node.type] || "#64748b";
  const Icon = typeIcon[node.type] || User;

  return (
    <foreignObject 
      x={node.x - 70} 
      y={node.y - 60} 
      width="140" 
      height="130"
      className="overflow-visible"
    >
      <div className="flex flex-col items-center text-center transition-transform duration-150 transform group-hover:scale-105 active:scale-95">
        
        {/* Node Shape Shell */}
        <div
          className={`w-13 h-13 rounded-2xl flex items-center justify-center text-white relative transition-all duration-200 shadow-md ${
            isSelected 
              ? "ring-4 ring-slate-900 ring-offset-2 border-2 border-transparent" 
              : "border-4 border-white group-hover:border-slate-200"
          }`}
          style={{ 
            backgroundColor: baseColor,
            boxShadow: isSelected ? `0 0 20px ${baseColor}80` : `0 4px 12px ${baseColor}30`
          }}
        >
          <Icon size={20} className="drop-shadow-sm" />
        </div>

        {/* Text Details Shield Label */}
        <div className={`mt-2 bg-white/95 border rounded-xl px-2.5 py-1.5 shadow-sm transition-all duration-150 max-w-[130px] ${
          isSelected ? "border-slate-900 bg-white shadow-md" : "border-slate-200/80 group-hover:border-slate-300"
        }`}>
          <p className="text-[10px] font-black truncate text-slate-800 tracking-tight">
            {node.label}
          </p>
          <p 
            className="text-[8px] font-mono tracking-wider uppercase font-black mt-0.5"
            style={{ color: baseColor }}
          >
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
    "Alias",
    "Vehicle",
    "Property",
    "Utility Meter",
    "Tax Return",
    "Business",
    "Bank Account",
    "Travel"
  ];

  return (
    <div className="flex flex-wrap gap-1.5 max-w-xl justify-start sm:justify-end">
      {items.map((item) => (
        <span
          key={item}
          className="text-[9px] font-black uppercase tracking-wider px-2.5 py-1 rounded-lg border border-slate-200 bg-white text-slate-600 flex items-center gap-1.5 shadow-sm"
        >
          <span
            className="inline-block w-1.5 h-1.5 rounded-full"
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
    <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-6 bg-white">
      <div className="w-16 h-16 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center shadow-sm">
        <Search size={26} className="text-blue-600" />
      </div>

      <h2 className="text-lg font-black mt-4 text-slate-800 tracking-tight">Select a Taxpayer Node</h2>

      <p className="text-slate-400 text-xs mt-1 max-w-xs leading-relaxed">
        Trace systemic data variables instantly by executing an index cluster search selection.
      </p>
    </div>
  );
}