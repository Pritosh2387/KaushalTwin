import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  ClipboardCheck,
  FileCheck2,
  Cpu,
  FileText,
  History,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Sparkles
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export function Sidebar({ collapsed, onToggle }) {
  const { user, isAssessor, isAdmin, isWorker } = useAuth();

  const navItems = [
    {
      to: '/',
      label: 'Overview',
      icon: LayoutDashboard,
      roles: ['ASSESSOR', 'ADMIN', 'WORKER'],
    },
    {
      to: '/workers',
      label: 'Workers',
      icon: Users,
      roles: ['ASSESSOR', 'ADMIN'],
    },
    {
      to: '/assessments',
      label: 'Assessments',
      icon: ClipboardCheck,
      roles: ['ASSESSOR', 'ADMIN', 'WORKER'],
    },
    {
      to: '/evidence',
      label: 'Evidence Review',
      icon: FileCheck2,
      roles: ['ASSESSOR', 'ADMIN', 'WORKER'],
    },
    {
      to: '/competencies',
      label: 'Competency Twin',
      icon: Cpu,
      roles: ['ASSESSOR', 'ADMIN'],
      badge: 'AI',
    },
    {
      to: '/reports',
      label: 'Reports',
      icon: FileText,
      roles: ['ASSESSOR', 'ADMIN', 'WORKER'],
    },
    {
      to: '/audit',
      label: 'Audit History',
      icon: History,
      roles: ['ASSESSOR', 'ADMIN'],
    },
    {
      to: '/settings',
      label: 'Settings',
      icon: Settings,
      roles: ['ASSESSOR', 'ADMIN', 'WORKER'],
    },
  ];

  const userRole = user?.role || 'ASSESSOR';
  const filteredNavItems = navItems.filter((item) =>
    item.roles.includes(userRole)
  );

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-30 flex flex-col bg-navy-950 text-slate-300 border-r border-navy-800 transition-all duration-300 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-navy-800/80">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-teal-400 flex items-center justify-center text-navy-950 font-black shadow-md shadow-cyan-500/20 flex-shrink-0">
            <Sparkles className="w-5 h-5 text-navy-950" />
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="font-bold text-white text-base tracking-wide flex items-center gap-1.5">
                KaushalTwin
                <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  RPL
                </span>
              </span>
              <span className="text-[11px] text-slate-400 font-medium truncate">
                AI Prior Learning Tool
              </span>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={onToggle}
          className="hidden md:flex p-1.5 text-slate-400 hover:text-white hover:bg-navy-800/60 rounded-lg transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
        {filteredNavItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 group relative ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/20 to-teal-500/10 text-cyan-300 font-semibold border-l-4 border-cyan-400 shadow-sm'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-navy-900/60'
                }`
              }
            >
              <Icon className="w-5 h-5 flex-shrink-0 transition-transform group-hover:scale-105" />
              {!collapsed && <span className="truncate">{item.label}</span>}
              {!collapsed && item.badge && (
                <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded bg-cyan-400/20 text-cyan-300 border border-cyan-400/30">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Assessor Compliance Notice */}
      {!collapsed && (
        <div className="p-4 mx-3 mb-3 bg-navy-900/70 border border-navy-800 rounded-xl text-xs space-y-1.5">
          <div className="flex items-center gap-1.5 text-cyan-400 font-semibold">
            <ShieldCheck className="w-4 h-4" />
            <span>Human-in-the-Loop</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-tight">
            AI provides recommendations only. Human assessors make final RPL decisions.
          </p>
        </div>
      )}
    </aside>
  );
}
