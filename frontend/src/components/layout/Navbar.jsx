import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Menu,
  LogOut,
  User as UserIcon,
  Shield,
  Activity,
  ChevronDown,
  Compass
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
    <header className="h-16 bg-[#000000] border-b border-white/10 sticky top-0 z-20 px-4 sm:px-6 flex items-center justify-between">
      {/* Mobile Toggle & Left Branding */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMobileMenuToggle}
          className="md:hidden p-2 text-zinc-400 hover:text-white hover:bg-white/5 rounded-none transition-colors"
        >
          <Menu className="w-5 h-5" />
          <span className="sr-only">Toggle navigation</span>
        </button>

        <div className="hidden sm:flex items-center gap-2 text-xs font-sans text-zinc-400 bg-[#050505] py-1.5 px-3 border border-white/10">
          <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></span>
          <span className="text-zinc-300 font-medium">Evaluation Engine Active</span>
          <span className="text-zinc-600">•</span>
          <span className="text-zinc-400">RPL Prior Learning Standards</span>
        </div>
      </div>

      {/* Right Controls: Hero Portal, User Profile & Menu */}
      <div className="flex items-center gap-3 sm:gap-4">
        <Link
          to="/"
          className="hidden lg:flex items-center gap-1.5 text-xs font-sans text-zinc-400 hover:text-white px-3 py-1.5 border border-white/10 hover:border-white/30 bg-[#050505] transition-colors"
        >
          <Compass className="w-3.5 h-3.5" />
          <span>Platform Overview</span>
        </Link>

        {/* User Dropdown */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2.5 p-1.5 sm:px-3 sm:py-1.5 rounded-none border border-white/15 hover:border-white/30 bg-[#050505] transition-colors text-left cursor-pointer"
          >
            <div className="w-7 h-7 rounded-none bg-zinc-900 border border-white/20 text-white font-mono font-bold flex items-center justify-center text-xs">
              {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="hidden sm:block text-left">
              <div className="text-xs font-mono font-semibold text-white leading-tight">
                {user?.full_name || 'Authenticated User'}
              </div>
              <div className="text-[10px] text-zinc-500 font-mono">
                {user?.email || 'user@kaushaltwin.gov.in'}
              </div>
            </div>
            <RoleBadge role={user?.role || 'ASSESSOR'} size="sm" className="hidden lg:inline-flex ml-1" />
            <ChevronDown className="w-3.5 h-3.5 text-zinc-400 ml-0.5" />
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-20"
                onClick={() => setDropdownOpen(false)}
              />
              <div className="absolute right-0 mt-2 w-56 bg-[#050505] shadow-2xl border border-white/15 py-1 z-30 specular-top-edge animate-in fade-in zoom-in-95 duration-100">
                <div className="px-4 py-2.5 border-b border-white/10 sm:hidden">
                  <div className="text-xs font-mono font-semibold text-white">
                    {user?.full_name}
                  </div>
                  <div className="text-[10px] font-mono text-zinc-500">{user?.email}</div>
                  <div className="mt-1.5">
                    <RoleBadge role={user?.role || 'ASSESSOR'} size="sm" />
                  </div>
                </div>

                <div className="px-2 py-1">
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      navigate('/');
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs font-mono text-zinc-300 hover:bg-white/5 hover:text-white transition-colors text-left cursor-pointer"
                  >
                    <Compass className="w-3.5 h-3.5 text-zinc-400" />
                    <span>Platform Overview</span>
                  </button>
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      navigate('/settings');
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs font-mono text-zinc-300 hover:bg-white/5 hover:text-white transition-colors text-left cursor-pointer"
                  >
                    <Activity className="w-3.5 h-3.5 text-zinc-400" />
                    <span>System Status & Health</span>
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs font-mono text-zinc-300 hover:bg-white/10 hover:text-white border-t border-white/10 mt-1 pt-2 transition-colors text-left cursor-pointer"
                  >
                    <LogOut className="w-3.5 h-3.5 text-zinc-400" />
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

export default Navbar;
