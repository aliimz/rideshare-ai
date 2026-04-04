import React, { useEffect, useState } from 'react';

import AdminMap from '../components/AdminMap.jsx';
import RevenueChart from '../components/RevenueChart.jsx';
import { getAdminOverview, updateAdminDriverAvailability } from '../services/api.js';

const PERIOD_OPTIONS = [
  { key: 'day', label: 'Daily' },
  { key: 'week', label: 'Weekly' },
  { key: 'month', label: 'Monthly' },
];

const formatPkr = (value) =>
  new Intl.NumberFormat('en-PK', {
    style: 'currency',
    currency: 'PKR',
    maximumFractionDigits: 0,
  }).format(value || 0);

const formatDateTime = (value) =>
  value
    ? new Date(value).toLocaleString('en-PK', {
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '--';

const statusClasses = {
  requested: 'bg-amber-500/15 text-amber-300 border-amber-500/25',
  matched: 'bg-sky-500/15 text-sky-300 border-sky-500/25',
  en_route: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/25',
  arrived: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/25',
  in_progress: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25',
  completed: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25',
  cancelled: 'bg-rose-500/15 text-rose-300 border-rose-500/25',
};

const StatCard = ({ label, value, detail }) => (
  <div className="rounded-3xl border border-slate-800 bg-slate-950/75 p-5 shadow-2xl">
    <p className="text-xs uppercase tracking-[0.28em] text-slate-500">{label}</p>
    <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
    <p className="mt-2 text-sm text-slate-400">{detail}</p>
  </div>
);

const StatusPill = ({ status }) => (
  <span
    className={`rounded-full border px-3 py-1 text-xs font-semibold capitalize ${
      statusClasses[status] || 'bg-slate-800 text-slate-300 border-slate-700'
    }`}
  >
    {status.replace('_', ' ')}
  </span>
);

const AdminPage = () => {
  const [overview, setOverview] = useState(null);
  const [period, setPeriod] = useState('day');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [mutatingDrivers, setMutatingDrivers] = useState([]);

  useEffect(() => {
    let cancelled = false;

    const loadOverview = async ({ silent = false } = {}) => {
      if (!silent) setLoading(true);
      try {
        const data = await getAdminOverview();
        if (!cancelled) {
          setOverview(data);
          setError('');
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to load admin dashboard.');
        }
      } finally {
        if (!cancelled && !silent) setLoading(false);
      }
    };

    loadOverview();
    const intervalId = window.setInterval(() => loadOverview({ silent: true }), 20000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  const handleDriverToggle = async (driverId, nextAvailability) => {
    setMutatingDrivers((prev) => [...prev, driverId]);
    try {
      const updatedDriver = await updateAdminDriverAvailability(driverId, nextAvailability);
      setOverview((current) => {
        if (!current) return current;
        const nextDrivers = current.drivers.map((driver) =>
          driver.id === driverId ? updatedDriver : driver
        );
        return {
          ...current,
          drivers: nextDrivers,
          stats: {
            ...current.stats,
            active_drivers: nextDrivers.filter((driver) => driver.available && driver.is_active).length,
          },
        };
      });
    } catch (err) {
      setError(err.message || 'Failed to update driver availability.');
    } finally {
      setMutatingDrivers((prev) => prev.filter((id) => id !== driverId));
    }
  };

  if (loading && !overview) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#050816] text-slate-300">
        Loading admin dashboard...
      </div>
    );
  }

  if (error && !overview) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#050816] px-6 text-center text-rose-300">
        {error}
      </div>
    );
  }

  const stats = overview?.stats || {};
  const drivers = overview?.drivers || [];
  const rides = overview?.rides || [];
  const revenueSeries = overview?.revenue?.[period] || [];

  return (
    <div className="min-h-screen overflow-y-auto bg-[#050816] text-slate-100">
      <div className="mx-auto max-w-7xl px-4 pb-10 pt-24 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.34em] text-cyan-400">Investor Command View</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-white">
              RideShare Admin Dashboard
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
              Live operations, driver supply, PKR revenue, and demand intensity pulled directly from the database.
            </p>
          </div>

          <div className="rounded-3xl border border-slate-800 bg-slate-950/70 px-5 py-4 text-sm text-slate-400 shadow-2xl">
            <p>Last refresh</p>
            <p className="mt-1 font-semibold text-white">{formatDateTime(overview?.generated_at)}</p>
            {error ? <p className="mt-2 text-rose-300">{error}</p> : null}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <StatCard
            label="Total Rides"
            value={stats.total_rides || 0}
            detail={`${stats.active_rides || 0} live now`}
          />
          <StatCard
            label="Revenue"
            value={formatPkr(stats.total_revenue)}
            detail={`${stats.completed_rides || 0} completed rides`}
          />
          <StatCard
            label="Active Drivers"
            value={stats.active_drivers || 0}
            detail={`${stats.online_drivers || 0} online in fleet`}
          />
          <StatCard
            label="Average Fare"
            value={formatPkr(stats.avg_fare)}
            detail="Average completed trip value"
          />
          <StatCard
            label="Surge Zones"
            value={stats.surge_zones || 0}
            detail="Hot pickup clusters in the last 14 days"
          />
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.55fr_1fr]">
          <div className="space-y-6">
            <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5 shadow-2xl">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Revenue Windows</p>
                  <h2 className="mt-1 text-xl font-semibold text-white">PKR earned by period</h2>
                </div>
                <div className="flex rounded-2xl border border-slate-800 bg-slate-900 p-1">
                  {PERIOD_OPTIONS.map((option) => (
                    <button
                      key={option.key}
                      type="button"
                      onClick={() => setPeriod(option.key)}
                      className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                        period === option.key
                          ? 'bg-emerald-500 text-slate-950'
                          : 'text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
              <RevenueChart
                series={revenueSeries}
                title={`Revenue by ${PERIOD_OPTIONS.find((option) => option.key === period)?.label.toLowerCase()}`}
              />
            </div>

            <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5 shadow-2xl">
              <div className="mb-5 flex items-end justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Demand Map</p>
                  <h2 className="mt-1 text-xl font-semibold text-white">Heatmap and live rides</h2>
                </div>
                <p className="text-sm text-slate-400">{overview?.heatmap?.length || 0} hotspots tracked</p>
              </div>
              <AdminMap heatmap={overview?.heatmap || []} rides={rides} />
            </div>
          </div>

          <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5 shadow-2xl">
            <div className="mb-5 flex items-end justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Fleet Controls</p>
                <h2 className="mt-1 text-xl font-semibold text-white">Driver management</h2>
              </div>
              <p className="text-sm text-slate-400">{drivers.length} drivers</p>
            </div>

            <div className="space-y-3">
              {drivers.map((driver) => (
                <div
                  key={driver.id}
                  className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-white">{driver.name}</p>
                      <p className="mt-1 text-sm capitalize text-slate-400">
                        {driver.vehicle_type} • {driver.rating.toFixed(1)} rating
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        Trips: {driver.total_trips} • Active ride: {driver.active_ride_id || 'None'}
                      </p>
                    </div>
                    <button
                      type="button"
                      disabled={mutatingDrivers.includes(driver.id)}
                      onClick={() => handleDriverToggle(driver.id, !driver.available)}
                      className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                        driver.available
                          ? 'bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30'
                          : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {mutatingDrivers.includes(driver.id)
                        ? 'Updating...'
                        : driver.available
                          ? 'Set Offline'
                          : 'Set Online'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-950/70 p-5 shadow-2xl">
          <div className="mb-5 flex items-end justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Ride Ledger</p>
              <h2 className="mt-1 text-xl font-semibold text-white">All rides, live and historical</h2>
            </div>
            <p className="text-sm text-slate-400">{rides.length} rows</p>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.22em] text-slate-500">
                <tr>
                  <th className="pb-3 pr-4">Ride</th>
                  <th className="pb-3 pr-4">Status</th>
                  <th className="pb-3 pr-4">Rider</th>
                  <th className="pb-3 pr-4">Driver</th>
                  <th className="pb-3 pr-4">Fare</th>
                  <th className="pb-3 pr-4">Pickup</th>
                  <th className="pb-3">Requested</th>
                </tr>
              </thead>
              <tbody>
                {rides.map((ride) => (
                  <tr key={ride.id} className="border-t border-slate-900/80 align-top">
                    <td className="py-4 pr-4 font-semibold text-white">#{ride.id}</td>
                    <td className="py-4 pr-4">
                      <StatusPill status={ride.status} />
                    </td>
                    <td className="py-4 pr-4 text-slate-300">{ride.rider_name}</td>
                    <td className="py-4 pr-4 text-slate-300">{ride.driver_name}</td>
                    <td className="py-4 pr-4 text-emerald-300">{formatPkr(ride.fare_amount)}</td>
                    <td className="py-4 pr-4 text-slate-400">{ride.pickup_address || '--'}</td>
                    <td className="py-4 text-slate-400">{formatDateTime(ride.requested_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
