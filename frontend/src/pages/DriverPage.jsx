import React, { useEffect, useState } from 'react';
import { Geolocation } from '@capacitor/geolocation';

import DriverMap from '../components/DriverMap.jsx';
import {
  acceptDriverRide,
  getCurrentUser,
  getDriverDashboard,
  login,
  rejectDriverRide,
  setAuthToken,
  updateDriverAvailability,
  updateDriverLocation,
  updateDriverRideStatus,
} from '../services/api.js';

const DRIVER_TOKEN_KEY = 'rideshare_driver_token';

const ACTIONS = {
  matched: { label: 'Head to pickup', nextStatus: 'en_route' },
  en_route: { label: 'Arrived at pickup', nextStatus: 'arrived' },
  arrived: { label: 'Pick up rider', nextStatus: 'in_progress' },
  in_progress: { label: 'Complete ride', nextStatus: 'completed' },
};

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

const DriverStat = ({ label, value, detail }) => (
  <div className="rounded-3xl border border-slate-800 bg-slate-950/75 p-5 shadow-2xl">
    <p className="text-xs uppercase tracking-[0.28em] text-slate-500">{label}</p>
    <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
    <p className="mt-2 text-sm text-slate-400">{detail}</p>
  </div>
);

const DriverPage = () => {
  const [token, setToken] = useState(() => window.localStorage.getItem(DRIVER_TOKEN_KEY) || '');
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [error, setError] = useState('');
  const [loginForm, setLoginForm] = useState({
    email: 'asad.raza@demo.com',
    password: 'Driver@123',
  });
  const [busyAction, setBusyAction] = useState('');

  useEffect(() => {
    setAuthToken(token || null);
  }, [token]);

  useEffect(() => {
    if (!token) {
      setDashboard(null);
      return;
    }

    let cancelled = false;

    const loadDashboard = async ({ silent = false } = {}) => {
      if (!silent) setLoading(true);
      try {
        const [me, data] = await Promise.all([getCurrentUser(), getDriverDashboard()]);
        if (me.role !== 'driver') {
          throw new Error('This account is not a driver.');
        }
        if (!cancelled) {
          setDashboard(data);
          setError('');
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to load driver dashboard.');
          if (/401|403|driver/i.test(err.message || '')) {
            window.localStorage.removeItem(DRIVER_TOKEN_KEY);
            setToken('');
          }
        }
      } finally {
        if (!cancelled && !silent) setLoading(false);
      }
    };

    loadDashboard();
    const intervalId = window.setInterval(() => loadDashboard({ silent: true }), 10000);
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [token]);

  useEffect(() => {
    if (!token) return undefined;

    let cancelled = false;

    const syncLocation = async () => {
      try {
        const permission = await Geolocation.requestPermissions();
        const granted =
          permission.location === 'granted' || permission.coarseLocation === 'granted';
        if (!granted) return;

        const position = await Geolocation.getCurrentPosition({ enableHighAccuracy: true });
        if (!cancelled) {
          await updateDriverLocation(position.coords.latitude, position.coords.longitude);
        }
      } catch {
        // Use seeded DB location when geolocation is unavailable.
      }
    };

    syncLocation();
    const intervalId = window.setInterval(syncLocation, 60000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [token]);

  const reloadDashboard = async () => {
    const data = await getDriverDashboard();
    setDashboard(data);
    return data;
  };

  const handleLogin = async (event) => {
    event.preventDefault();
    setAuthLoading(true);
    try {
      const response = await login(loginForm.email, loginForm.password);
      window.localStorage.setItem(DRIVER_TOKEN_KEY, response.access_token);
      setToken(response.access_token);
      setError('');
    } catch (err) {
      setError(err.message || 'Driver login failed.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    window.localStorage.removeItem(DRIVER_TOKEN_KEY);
    setAuthToken(null);
    setToken('');
    setDashboard(null);
  };

  const handleAvailabilityToggle = async () => {
    if (!dashboard?.driver) return;
    setBusyAction('availability');
    try {
      const updatedDriver = await updateDriverAvailability(!dashboard.driver.available);
      setDashboard((current) => (current ? { ...current, driver: updatedDriver } : current));
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to update availability.');
    } finally {
      setBusyAction('');
    }
  };

  const handleAcceptRide = async (rideId) => {
    setBusyAction(`accept-${rideId}`);
    try {
      await acceptDriverRide(rideId);
      await reloadDashboard();
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to accept ride.');
    } finally {
      setBusyAction('');
    }
  };

  const handleRejectRide = async (rideId) => {
    setBusyAction(`reject-${rideId}`);
    try {
      await rejectDriverRide(rideId);
      setDashboard((current) => {
        if (!current) return current;
        return {
          ...current,
          incoming_requests: current.incoming_requests.filter((ride) => ride.id !== rideId),
        };
      });
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to reject ride.');
    } finally {
      setBusyAction('');
    }
  };

  const handleAdvanceRide = async () => {
    if (!dashboard?.active_ride) return;
    const config = ACTIONS[dashboard.active_ride.status];
    if (!config) return;

    setBusyAction(`ride-${dashboard.active_ride.id}`);
    try {
      await updateDriverRideStatus(dashboard.active_ride.id, config.nextStatus);
      await reloadDashboard();
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to update ride status.');
    } finally {
      setBusyAction('');
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen overflow-y-auto bg-[#050816] px-4 pb-10 pt-24 text-slate-100 sm:px-6">
        <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="rounded-[2rem] border border-slate-800 bg-slate-950/70 p-8 shadow-2xl">
            <p className="text-xs uppercase tracking-[0.34em] text-emerald-400">Driver Workspace</p>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-white">
              Accept trips and run the ride flow from one console.
            </h1>
            <p className="mt-4 max-w-xl text-sm leading-6 text-slate-400">
              This driver view is wired to the database-backed ride queue. Go online, accept an incoming request, then move the trip through pickup and completion.
            </p>

            <div className="mt-8 grid gap-4 sm:grid-cols-3">
              <DriverStat label="Queue" value="Live" detail="Requested rides pull from SQL" />
              <DriverStat label="Flow" value="4 steps" detail="Accept, pickup, drop off, complete" />
              <DriverStat label="Fleet" value="20" detail="Seeded drivers ready for demo" />
            </div>
          </div>

          <div className="rounded-[2rem] border border-slate-800 bg-slate-950/80 p-8 shadow-2xl">
            <p className="text-xs uppercase tracking-[0.34em] text-slate-500">Driver Login</p>
            <h2 className="mt-3 text-2xl font-semibold text-white">Sign in as a driver</h2>
            <p className="mt-3 text-sm text-slate-400">
              Demo account: <span className="font-medium text-white">asad.raza@demo.com</span> /{' '}
              <span className="font-medium text-white">Driver@123</span>
            </p>

            <form className="mt-6 space-y-4" onSubmit={handleLogin}>
              <label className="block">
                <span className="mb-2 block text-sm text-slate-400">Email</span>
                <input
                  type="email"
                  value={loginForm.email}
                  onChange={(event) =>
                    setLoginForm((current) => ({ ...current, email: event.target.value }))
                  }
                  className="w-full rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-sm text-slate-400">Password</span>
                <input
                  type="password"
                  value={loginForm.password}
                  onChange={(event) =>
                    setLoginForm((current) => ({ ...current, password: event.target.value }))
                  }
                  className="w-full rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
                />
              </label>

              {error ? <p className="text-sm text-rose-300">{error}</p> : null}

              <button
                type="submit"
                disabled={authLoading}
                className="w-full rounded-2xl bg-emerald-500 px-4 py-3 font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-emerald-500/60"
              >
                {authLoading ? 'Signing in...' : 'Enter driver app'}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  const driver = dashboard?.driver;
  const incomingRequests = dashboard?.incoming_requests || [];
  const activeRide = dashboard?.active_ride;
  const recentCompleted = dashboard?.recent_completed || [];
  const rideAction = activeRide ? ACTIONS[activeRide.status] : null;

  return (
    <div className="min-h-screen overflow-y-auto bg-[#050816] text-slate-100">
      <div className="mx-auto max-w-7xl px-4 pb-10 pt-24 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.34em] text-emerald-400">Driver Operations</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-white">
              {driver?.name || 'Driver'} dispatch console
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
              Monitor the ride queue, accept requests, and advance the trip through pickup and completion.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              disabled={busyAction === 'availability'}
              onClick={handleAvailabilityToggle}
              className={`rounded-2xl px-4 py-3 text-sm font-semibold transition ${
                driver?.available
                  ? 'bg-emerald-500 text-slate-950 hover:bg-emerald-400'
                  : 'bg-slate-900 text-slate-200 hover:bg-slate-800'
              }`}
            >
              {busyAction === 'availability'
                ? 'Updating...'
                : driver?.available
                  ? 'Go offline'
                  : 'Go online'}
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3 text-sm font-semibold text-slate-300 transition hover:bg-slate-900"
            >
              Log out
            </button>
          </div>
        </div>

        {error ? (
          <div className="mb-6 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <DriverStat
            label="Status"
            value={driver?.available ? 'Online' : 'Offline'}
            detail={activeRide ? `Ride #${activeRide.id} in progress` : 'No active assignment'}
          />
          <DriverStat
            label="Rides Today"
            value={driver?.rides_today || 0}
            detail="Completed trips in Pakistan time"
          />
          <DriverStat
            label="Earned Today"
            value={formatPkr(driver?.earnings_today)}
            detail="Paid ride value recorded today"
          />
          <DriverStat
            label="Rating"
            value={driver?.rating?.toFixed(1) || '--'}
            detail={`${driver?.total_trips || 0} total trips completed`}
          />
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.45fr_1fr]">
          <div className="space-y-6">
            <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5 shadow-2xl">
              <div className="mb-5 flex items-end justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Driver Map</p>
                  <h2 className="mt-1 text-xl font-semibold text-white">Requests and active ride</h2>
                </div>
                <p className="text-sm text-slate-400">
                  {loading ? 'Refreshing...' : `${incomingRequests.length} open requests`}
                </p>
              </div>
              <DriverMap
                driver={driver}
                incomingRequests={incomingRequests}
                activeRide={activeRide}
              />
            </div>

            <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5 shadow-2xl">
              <div className="mb-5">
                <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Ride Queue</p>
                <h2 className="mt-1 text-xl font-semibold text-white">Incoming ride requests</h2>
              </div>

              <div className="space-y-3">
                {incomingRequests.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-950/60 px-5 py-10 text-center text-sm text-slate-500">
                    No open requests right now.
                  </div>
                ) : (
                  incomingRequests.map((request) => (
                    <div
                      key={request.id}
                      className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4"
                    >
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                        <div>
                          <p className="font-semibold text-white">
                            Ride #{request.id} for {request.rider_name}
                          </p>
                          <p className="mt-2 text-sm text-slate-400">{request.pickup_address}</p>
                          <p className="mt-1 text-sm text-slate-500">Dropoff: {request.dropoff_address}</p>
                          <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-400">
                            <span>{formatPkr(request.fare_amount)}</span>
                            <span>{request.distance_km?.toFixed(1)} km trip</span>
                            <span>
                              {request.distance_from_driver_km != null
                                ? `${request.distance_from_driver_km.toFixed(1)} km away`
                                : 'Distance unavailable'}
                            </span>
                            <span>{formatDateTime(request.requested_at)}</span>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            disabled={!driver?.available || !!activeRide || busyAction === `accept-${request.id}`}
                            onClick={() => handleAcceptRide(request.id)}
                            className="rounded-2xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-emerald-500/40"
                          >
                            {busyAction === `accept-${request.id}` ? 'Accepting...' : 'Accept'}
                          </button>
                          <button
                            type="button"
                            disabled={busyAction === `reject-${request.id}`}
                            onClick={() => handleRejectRide(request.id)}
                            className="rounded-2xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm font-semibold text-slate-300 transition hover:bg-slate-900"
                          >
                            {busyAction === `reject-${request.id}` ? 'Rejecting...' : 'Reject'}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5 shadow-2xl">
              <div className="mb-5">
                <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Active Ride</p>
                <h2 className="mt-1 text-xl font-semibold text-white">Current assignment</h2>
              </div>

              {activeRide ? (
                <div className="space-y-4">
                  <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
                    <p className="text-sm text-slate-400">Rider</p>
                    <p className="mt-1 text-lg font-semibold text-white">{activeRide.rider_name}</p>
                    <p className="mt-4 text-sm text-slate-400">Pickup</p>
                    <p className="mt-1 text-sm text-slate-200">{activeRide.pickup_address}</p>
                    <p className="mt-4 text-sm text-slate-400">Dropoff</p>
                    <p className="mt-1 text-sm text-slate-200">{activeRide.dropoff_address}</p>
                    <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-400">
                      <span className="rounded-full border border-slate-800 px-3 py-1 capitalize">
                        {activeRide.status.replace('_', ' ')}
                      </span>
                      <span>{activeRide.distance_km?.toFixed(1)} km</span>
                      <span>{formatPkr(activeRide.fare_amount)}</span>
                    </div>
                  </div>

                  {rideAction ? (
                    <button
                      type="button"
                      disabled={busyAction === `ride-${activeRide.id}`}
                      onClick={handleAdvanceRide}
                      className="w-full rounded-2xl bg-sky-500 px-4 py-3 font-semibold text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-sky-500/40"
                    >
                      {busyAction === `ride-${activeRide.id}` ? 'Updating ride...' : rideAction.label}
                    </button>
                  ) : null}
                </div>
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-950/60 px-5 py-10 text-center text-sm text-slate-500">
                  Accept a request to begin the ride flow.
                </div>
              )}
            </div>

            <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5 shadow-2xl">
              <div className="mb-5">
                <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Recent Earnings</p>
                <h2 className="mt-1 text-xl font-semibold text-white">Completed rides</h2>
              </div>

              <div className="space-y-3">
                {recentCompleted.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-950/60 px-5 py-10 text-center text-sm text-slate-500">
                    No completed rides yet today.
                  </div>
                ) : (
                  recentCompleted.map((ride) => (
                    <div
                      key={ride.id}
                      className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-900/80 px-4 py-3"
                    >
                      <div>
                        <p className="font-semibold text-white">Ride #{ride.id}</p>
                        <p className="mt-1 text-sm text-slate-400">{ride.dropoff_address}</p>
                        <p className="mt-1 text-xs text-slate-500">{formatDateTime(ride.completed_at)}</p>
                      </div>
                      <p className="text-sm font-semibold text-emerald-300">{formatPkr(ride.fare_amount)}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DriverPage;
