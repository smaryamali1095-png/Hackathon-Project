import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Network,
  Database,
  Shield,
  FileText,
  BarChart3,
  PlusCircle
} from "lucide-react";

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  const menuItems = [
    { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { name: "Knowledge Graph", path: "/graph", icon: Network },
    { name: "Entity Resolution", path: "/entity-resolution", icon: Shield },
    { name: "Data Sources", path: "/data-sources", icon: Database },
    { name: "Audit Trail", path: "/audit-trail", icon: FileText },
    { name: "Reports", path: "/reports", icon: BarChart3 }
  ];

  return (
    <div className="w-64 bg-slate-950 p-6 text-white min-h-screen flex flex-col">
      <h1 className="font-bold text-xl mb-10 tracking-tighter">
        Tax Intel AI
      </h1>

      <nav className="space-y-2 flex-1">
        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <div
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                location.pathname === item.path
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:bg-slate-800"
              }`}
            >
              <Icon size={20} />
              <span className="text-sm font-medium">{item.name}</span>
            </div>
          );
        })}
      </nav>

      <button
        onClick={() => navigate("/entity-resolution")}
        className="flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white w-full py-3 rounded-lg text-sm font-bold transition-all mt-auto"
      >
        <PlusCircle size={18} />
        New Investigation
      </button>
    </div>
  );
}