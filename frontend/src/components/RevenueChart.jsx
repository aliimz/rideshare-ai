import React from 'react';

const RevenueChart = ({ series = [], title }) => {
  const peak = Math.max(...series.map((item) => item.amount), 0);

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5 shadow-2xl">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Revenue</p>
          <h3 className="mt-1 text-lg font-semibold text-white">{title}</h3>
        </div>
        <p className="text-sm text-slate-400">
          Total PKR{' '}
          <span className="font-semibold text-emerald-400">
            {series.reduce((sum, item) => sum + item.amount, 0).toFixed(0)}
          </span>
        </p>
      </div>

      <div className="flex h-56 items-end gap-3">
        {series.map((item) => {
          const height = peak > 0 ? Math.max((item.amount / peak) * 100, 8) : 8;
          return (
            <div key={item.label} className="flex flex-1 flex-col items-center gap-3">
              <span className="text-[11px] font-medium text-slate-400">
                {item.amount > 0 ? `PKR ${item.amount.toFixed(0)}` : 'PKR 0'}
              </span>
              <div className="flex h-40 w-full items-end rounded-2xl bg-slate-900/80 p-1.5">
                <div
                  className="w-full rounded-xl bg-gradient-to-t from-emerald-500 via-teal-400 to-cyan-300 transition-all duration-500"
                  style={{ height: `${height}%` }}
                />
              </div>
              <span className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
                {item.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RevenueChart;
