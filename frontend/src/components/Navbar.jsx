import React from 'react';
import { Bell, Settings, Search } from 'lucide-react';

export default function Navbar() {
  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8">
      <div className="relative w-96">
        <Search className="absolute left-3 top-2.5 text-slate-400" size={18} />
        <input type="text" placeholder="Search taxpayers, entities, or cases..." 
               className="w-full bg-slate-100 rounded-lg pl-10 py-2 text-sm focus:outline-none" />
      </div>
      <div className="flex items-center gap-6">
        <Bell className="text-slate-500 cursor-pointer" size={20} />
        <Settings className="text-slate-500 cursor-pointer" size={20} />
        <div className="flex items-center gap-3 border-l pl-6">
          <div className="text-right">
            <p className="text-sm font-bold">Senior Auditor</p>
            <p className="text-[10px] text-slate-500">ID: 8829-KHI</p>
          </div>
          <div className="w-8 h-8 bg-slate-300 rounded-full"></div>
        </div>
      </div>
    </header>
  );
}