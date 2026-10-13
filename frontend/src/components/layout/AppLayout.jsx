import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#000000] flex flex-col font-sans text-white antialiased selection:bg-white selection:text-black relative">
      {/* Background ambient grid */}
      <div className="fixed inset-0 obsidian-grid opacity-20 pointer-events-none" />

      {/* Desktop Sidebar */}
      <div className="hidden md:block">
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed(!collapsed)}
        />
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-40 flex">
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-md"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative z-50 flex flex-col w-72 max-w-[85vw] bg-[#000000] text-white border-r border-white/10">
            <Sidebar
              collapsed={false}
              onToggle={() => setMobileMenuOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Container */}
      <div
        className={`flex-1 flex flex-col transition-all duration-200 relative z-10 ${
          collapsed ? 'md:pl-20' : 'md:pl-64'
        }`}
      >
        <Navbar onMobileMenuToggle={() => setMobileMenuOpen(true)} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto animate-in fade-in duration-200">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
