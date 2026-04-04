import React from 'react';

const TABS = [
  { key: 'rider', label: 'Rider', path: '/' },
  { key: 'admin', label: 'Admin', path: '/admin' },
  { key: 'driver', label: 'Driver', path: '/driver' },
];

const ModeNav = ({ currentRoute, onNavigate }) => {
  return (
    <div className="fixed top-4 right-4 z-[3000]">
      <div className="flex items-center gap-1 rounded-2xl border border-slate-700/70 bg-slate-950/75 p-1.5 shadow-2xl backdrop-blur-xl">
        {TABS.map((tab) => {
          const active = currentRoute === tab.key;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => onNavigate(tab.path)}
              className={`rounded-xl px-3 py-2 text-xs font-semibold transition ${
                active
                  ? 'bg-emerald-500 text-slate-950'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default ModeNav;
