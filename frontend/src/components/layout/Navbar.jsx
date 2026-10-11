import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Menu,
  Bell,
  LogOut,
  User as UserIcon,
  Shield,
  Activity,
  ChevronDown
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { RoleBadge } from '../ui/Badge';

export function Navbar({ onMobileMenuToggle }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 sticky top-0 z-20 px-4 sm:px-6 flex items-center justify-between">
      {/* Mobile Toggle & Left Branding */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMobileMenuToggle}
          className="md:hidden p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <Menu className="w-5 h-5" />
          <span className="sr-only">Toggle navigation</span>
        </button>

        <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-slate-500 bg-slate-50 py-1.5 px-3 rounded-full border border-slate-200">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>FastAPI + MongoDB Connected</span>
          <span className="text-slate-300">|</span>
          <span className="text-cyan-700 font-semibold">Embedded ML Engine v1.0</span>
        </div>
      </div>

      {/* Right Controls: Notifications, User Profile & Menu */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* User Dropdown */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2.5 p-1.5 sm:px-3 sm:py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors text-left"
          >
            <div className="w-8 h-8 rounded-lg bg-navy-900 text-cyan-400 font-bold flex items-center justify-center text-xs shadow-inner">
              {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="hidden sm:block text-left">
              <div className="text-xs font-semibold text-slate-900 leading-tight">
                {user?.full_name || 'Authenticated User'}
              </div>
              <div className="text-[10px] text-slate-500 font-medium">
                {user?.email || 'user@kaushaltwin.gov.in'}
              </div>
            </div>
            <RoleBadge role={user?.role || 'ASSESSOR'} size="sm" className="hidden lg:inline-flex ml-1" />
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-0.5" />
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-20"
                onClick={() => setDropdownOpen(false)}
              />
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-slate-200 py-1 z-30 animate-in fade-in zoom-in-95 duration-100">
                <div className="px-4 py-2.5 border-b border-slate-100 sm:hidden">
                  <div className="text-xs font-semibold text-slate-900">
                    {user?.full_name}
                  </div>
                  <div className="text-[11px] text-slate-500">{user?.email}</div>
                  <div className="mt-1.5">
                    <RoleBadge role={user?.role || 'ASSESSOR'} size="sm" />
                  </div>
                </div>

                <div className="px-2 py-1">
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      navigate('/settings');
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-700 hover:bg-slate-50 hover:text-slate-900 rounded-lg transition-colors text-left"
                  >
                    <Activity className="w-4 h-4 text-slate-400" />
                    <span>System Status & Health</span>
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-rose-600 hover:bg-rose-50 rounded-lg transition-colors text-left font-medium"
                  >
                    <LogOut className="w-4 h-4 text-rose-500" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
