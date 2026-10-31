import React, { useState } from 'react';
import { Briefcase, Menu } from 'lucide-react';
import Sidebar from './Sidebar';
import type { UseAppState } from '../../hooks/useAppState';

interface MainLayoutProps {
  appState: UseAppState;
  children: React.ReactNode;
}

export default function MainLayout({ appState, children }: MainLayoutProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      <Sidebar appState={appState} open={menuOpen} onClose={() => setMenuOpen(false)} />

      {/* Overlay khi mở menu trên màn hình nhỏ */}
      {menuOpen && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/30 md:hidden"
          onClick={() => setMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      <div className="flex-1 min-w-0 flex flex-col">
        {/* Thanh đầu trang chỉ hiện trên màn hình nhỏ */}
        <header className="sticky top-0 z-20 flex items-center gap-3 px-4 h-14 bg-white border-b border-slate-200 md:hidden">
          <button
            onClick={() => setMenuOpen(true)}
            className="btn-ghost p-2"
            aria-label="Mở menu"
          >
            <Menu size={18} />
          </button>
          <div className="w-7 h-7 bg-blue-600 rounded-md flex items-center justify-center">
            <Briefcase size={14} className="text-white" />
          </div>
          <span className="font-bold text-slate-900">SmartCareer</span>
        </header>

        <main className="flex-1 min-w-0 overflow-x-hidden">
          <div className="max-w-6xl mx-auto px-4 py-5 md:px-6 md:py-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
