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
    <div className="w-64 bg-[#0F172A] border-r border-slate-800/60 p-6 text-slate-100 min-h-screen flex flex-col justify-between shadow-[4px_0_24px_rgba(0,0,0,0.3)] sticky top-0 h-screen z-40">
      
      {/* Top Branding Section */}
      <div>
        <div className="flex items-center gap-2 mb-9 pl-2">
          <h1 className="font-black text-xl tracking-tight text-slate-100">
            Tax <span className="text-cyan-400 font-extrabold">Intel AI</span>
          </h1>
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-2.5 animate-pulse"></span>
        </div>

        {/* Navigation Layer */}
        <nav className="space-y-1.5">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <div
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer font-sans transition-all duration-200 transform active:scale-[0.98] ${
                  isActive
                    ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 font-bold shadow-lg shadow-cyan-500/10 border border-cyan-400/20"
                    : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 font-medium"
                }`}
              >
                <Icon 
                  size={18} 
                  className={`transition-colors duration-200 ${
                    isActive ? "text-slate-950" : "text-slate-500 group-hover:text-slate-300"
                  }`} 
                />
                <span className={`text-xs tracking-wide uppercase font-black ${isActive ? "text-slate-950" : ""}`}>
                  {item.name}
                </span>
              </div>
            );
          })}
        </nav>
      </div>

      {/* Footer Call to Action Button */}
      <div className="pt-4 border-t border-slate-800/80">
        <button
          onClick={() => navigate("/entity-resolution")}
          className="flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 w-full py-3 px-4 rounded-xl text-xs font-black tracking-wider uppercase transition-all duration-200 shadow-lg shadow-emerald-500/10 transform active:scale-95"
        >
          <PlusCircle size={16} />
          New Investigation
        </button>
      </div>

    </div>
  );
}