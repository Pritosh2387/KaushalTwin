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
  Sparkles,
  Compass,
  User,
  Briefcase
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export function Sidebar({ collapsed, onToggle }) {
  const { user, isWorker, isAssessor, isAdmin } = useAuth();

  // Define navigation items based on user role
  let navItems = [];

  if (isWorker) {
    // Worker-specific navigation
    navItems = [
      {
        to: '/dashboard',
        label: 'Dashboard',
        icon: LayoutDashboard,
        roles: ['WORKER'],
      },
      {
        to: '/workers/profile',
        label: 'My Profile',
        icon: User,
        roles: ['WORKER'],
      },
      {
        to: '/workers/experience',
        label: 'My Work Experience',
        icon: Briefcase,
        roles: ['WORKER'],
      },
      {
        to: '/competencies',
        label: 'My Skills',
        icon: Cpu,
        roles: ['WORKER'],
        badge: 'Twin',
      },
      {
        to: '/evidence',
        label: 'My Evidence',
        icon: FileCheck2,
        roles: ['WORKER'],
      },
      {
        to: '/assessments',
        label: 'My Assessments',
        icon: ClipboardCheck,
        roles: ['WORKER'],
      },
      {
        to: '/reports',
        label: 'My Reports',
        icon: FileText,
        roles: ['WORKER'],
      },
      {
        to: '/settings',
        label: 'Account Settings',
        icon: Settings,
        roles: ['WORKER'],
      },
    ];
  } else if (isAssessor || isAdmin) {
    // Assessor/Admin navigation (existing)
    navItems = [
      {
        to: '/dashboard',
        label: 'Dashboard',
        icon: LayoutDashboard,
        roles: ['ASSESSOR', 'ADMIN'],
      },
      {
        to: '/workers',
        label: 'Candidates',
        icon: Users,
        roles: ['ASSESSOR', 'ADMIN'],
      },
      {
        to: '/assessments',
        label: 'Assessments',
        icon: ClipboardCheck,
        roles: ['ASSESSOR', 'ADMIN'],
      },
      {
        to: '/evidence',
        label: 'Evidence Review',
        icon: FileCheck2,
        roles: ['ASSESSOR', 'ADMIN'],
      },
      {
        to: '/competencies',
        label: 'Competency Matrix',
        icon: Cpu,
        roles: ['ASSESSOR', 'ADMIN'],
        badge: 'Twin',
      },
      {
        to: '/reports',
        label: 'Reports & Dossiers',
        icon: FileText,
        roles: ['ASSESSOR', 'ADMIN'],
      },
      {
        to: '/audit',
        label: 'Audit History',
        icon: History,
        roles: ['ASSESSOR', 'ADMIN'],
      },
      {
        to: '/settings',
        label: 'System Settings',
        icon: Settings,
        roles: ['ASSESSOR', 'ADMIN'],
      },
    ];
  } else {
    // Fallback (shouldn't happen in practice)
    navItems = [
      {
        to: '/dashboard',
        label: 'Dashboard',
        icon: LayoutDashboard,
        roles: ['ASSESSOR', 'ADMIN', 'WORKER'],
      },
    ];
  }

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-30 flex flex-col bg-[#000000] text-zinc-300 border-r border-white/10 transition-all duration-200 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-white/10 bg-[#030303]">
        <div className="flex items-center gap-3 overflow-hidden">
          {/* Obsidian Diamond Icon */}
          <div className="w-8 h-8 border border-white/30 bg-[#080808] flex items-center justify-center rotate-45 flex-shrink-0">
            <div className="w-3.5 h-3.5 bg-white -rotate-45" />
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="font-mono font-bold text-white text-xs tracking-wider uppercase flex items-center gap-1.5">
                KAUSHALTWIN
                <span className="text-[9px] uppercase font-mono px-1 py-0.2 rounded-none bg-white/10 text-white border border-white/20">
                  RPL
                </span>
              </span>
              <span className="text-[10px] text-zinc-500 font-mono tracking-widest uppercase truncate">
                SKILL INTELLIGENCE
              </span>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={onToggle}
          className="hidden md:flex p-1.5 text-zinc-500 hover:text-white hover:bg-white/5 rounded-none transition-colors cursor-pointer"
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
      <nav className="flex-1 px-2.5 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-none font-mono text-xs tracking-wider uppercase transition-all duration-150 group relative ${
                  isActive
                    ? 'bg-white/10 text-white font-semibold border-l-2 border-white'
                    : 'text-zinc-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0 text-zinc-400 group-hover:text-white transition-colors" />
              {!collapsed && <span className="truncate">{item.label}</span>}
              {!collapsed && item.badge && (
                <span className="ml-auto text-[9px] font-mono px-1 py-0.5 bg-white/10 text-white border border-white/20">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}

        {/* Link back to Platform Overview */}
        <div className="pt-3 mt-3 border-t border-white/10">
          <NavLink
            to="/"
            className="flex items-center gap-3 px-3 py-2.5 rounded-none font-mono text-xs tracking-wider uppercase text-zinc-400 hover:text-white hover:bg-white/5 transition-colors"
          >
            <Compass className="w-4 h-4 flex-shrink-0 text-zinc-400" />
            {!collapsed && <span>Platform Overview</span>}
          </NavLink>
        </div>
      </nav>

      {/* Bottom Compliance Notice */}
      {!collapsed && (
        <div className="p-3.5 mx-2.5 mb-3 bg-[#050505] border border-white/10 rounded-none text-xs space-y-1.5 specular-top-edge">
          <div className="flex items-center gap-1.5 text-white font-mono text-[10px] tracking-wider uppercase">
            <ShieldCheck className="w-3.5 h-3.5 text-white" />
            <span>{isWorker ? 'RPL Governance' : 'Assessor Governance'}</span>
          </div>
          <p className="text-[10px] text-zinc-400 leading-tight font-light font-sans">
            {isWorker
              ? 'AI provides skill recommendations only. Certified human assessors make all final RPL certification decisions.'
              : 'AI provides recommendations only. Certified human assessors make all final certification decisions.'}
          </p>
        </div>
      )}
    </aside>
  );
}

export default Sidebar;
