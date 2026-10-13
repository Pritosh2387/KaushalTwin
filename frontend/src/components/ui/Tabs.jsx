import React from 'react';

export function Tabs({ tabs, activeTab, onChange, className = '' }) {
  return (
    <div className={`border-b border-white/10 overflow-x-auto no-scrollbar ${className}`}>
      <nav className="flex space-x-6 min-w-max" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={`flex items-center gap-2 py-3 px-1 border-b-2 font-medium text-xs tracking-wider uppercase transition-all duration-150 cursor-pointer ${
                isActive
                  ? 'border-white text-white font-semibold'
                  : 'border-transparent text-zinc-500 hover:text-zinc-300 hover:border-zinc-700'
              }`}
            >
              {Icon && <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-zinc-500'}`} />}
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span
                  className={`ml-1 px-1.5 py-0.5 text-[10px] font-mono border ${
                    isActive
                      ? 'bg-white text-black border-white font-semibold'
                      : 'bg-[#0a0a0a] text-zinc-400 border-white/10'
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
}

export default Tabs;
