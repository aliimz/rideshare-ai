import React from 'react';

const StatItem = ({ label, value, accent = false, icon }) => (
  <div className="flex items-center gap-2 px-4 py-2">
    {icon && <span className="text-base">{icon}</span>}
    <div className="flex flex-col">
      <span className="text-[10px] uppercase tracking-widest text-slate-500 font-medium">
        {label}
      </span>
      <span
        className={`text-sm font-bold leading-tight ${
          accent ? 'text-green-400' : 'text-slate-200'
        }`}
      >
        {value}
      </span>
    </div>
  </div>
);

const Divider = () => (
  <div className="w-px h-8 bg-slate-700/60 self-center" />
);

const StatsBar = ({ drivers = [] }) => {
  const activeDrivers = drivers.filter((d) => d.available).length;
  const totalDrivers = drivers.length;

  const avgRating =
    drivers.length > 0
      ? (
          drivers.reduce((sum, d) => sum + (d.rating ?? 0), 0) / drivers.length
        ).toFixed(1)
      : '—';

  // Simulate surge: higher when fewer active drivers
  const surgeMultiplier =
    totalDrivers > 0
      ? activeDrivers / totalDrivers < 0.4
        ? '2.1×'
        : activeDrivers / totalDrivers < 0.7
        ? '1.4×'
        : '1.0×'
      : '1.0×';

  const surgeIsHigh = surgeMultiplier !== '1.0×';

  return (
    <div
      className="
        flex items-stretch divide-x divide-slate-700/60
        bg-[#1e293b] border-b border-slate-700/60
        text-slate-300 text-sm select-none
        overflow-x-auto scrollbar-none
      "
    >
      <StatItem
        icon="🚗"
        label="Active Drivers"
        value={`${activeDrivers} / ${totalDrivers}`}
        accent
      />
      <Divider />
      <StatItem
        icon="⭐"
        label="Avg Rating"
        value={avgRating !== '—' ? `${avgRating} / 5.0` : '—'}
      />
      <Divider />
      <StatItem
        icon="⚡"
        label="Current Surge"
        value={surgeMultiplier}
        accent={surgeIsHigh}
      />
      <Divider />
      <StatItem
        icon="🤖"
        label="AI Model"
        value="Random Forest"
        accent
      />
      <Divider />
      {/* Live indicator */}
      <div className="flex items-center gap-2 px-4 py-2 ml-auto">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
        </span>
        <span className="text-[10px] uppercase tracking-widest text-slate-500 font-medium">
          Live
        </span>
      </div>
    </div>
  );
};

export default StatsBar;
