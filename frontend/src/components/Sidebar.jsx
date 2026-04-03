import React, { useEffect, useRef, useState } from 'react';
import DriverCard from './DriverCard.jsx';

// ── Helpers ───────────────────────────────────────────────────────────────────
const StarRating = ({ rating }) => {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);
  return (
    <span className="flex items-center gap-0.5">
      {Array.from({ length: full }).map((_, i) => (
        <span key={`f${i}`} className="text-amber-400 text-base">★</span>
      ))}
      {half && <span className="text-amber-400 opacity-60 text-base">★</span>}
      {Array.from({ length: empty }).map((_, i) => (
        <span key={`e${i}`} className="text-slate-600 text-base">★</span>
      ))}
      <span className="text-slate-400 text-xs ml-1">{rating.toFixed(1)}</span>
    </span>
  );
};

const SectionHeading = ({ children }) => (
  <h2 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-2 px-1">
    {children}
  </h2>
);

// Animated confidence bar
const ConfidenceBar = ({ value }) => {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setWidth(value), 120);
    return () => clearTimeout(timer);
  }, [value]);

  const color =
    value >= 85
      ? '#22c55e'
      : value >= 65
      ? '#f59e0b'
      : '#ef4444';

  return (
    <div className="mt-1">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-slate-400">Match Confidence</span>
        <span
          className="text-sm font-bold"
          style={{ color }}
        >
          {value}%
        </span>
      </div>
      <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full progress-fill"
          style={{
            width: `${width}%`,
            background: `linear-gradient(90deg, ${color}99, ${color})`,
          }}
        />
      </div>
    </div>
  );
};

// Price row helper
const PriceRow = ({ label, value, accent = false, large = false }) => (
  <div className="flex items-center justify-between py-1">
    <span className={`${large ? 'text-sm font-semibold text-slate-200' : 'text-xs text-slate-400'}`}>
      {label}
    </span>
    <span
      className={`font-semibold ${
        large ? 'text-base text-green-400' : accent ? 'text-amber-400 text-xs' : 'text-slate-300 text-xs'
      }`}
    >
      {value}
    </span>
  </div>
);

// ── RIDE STATUS CARD ───────────────────────────────────────────────────────────
const RideStatusCard = ({ status }) => {
  const statusConfig = {
    idle: { label: 'No active ride', color: 'text-slate-500', dot: 'bg-slate-600' },
    searching: { label: 'Searching for driver…', color: 'text-amber-400', dot: 'bg-amber-500 animate-pulse' },
    matched: { label: 'Driver matched!', color: 'text-green-400', dot: 'bg-green-500' },
    error: { label: 'Match failed', color: 'text-red-400', dot: 'bg-red-500' },
  };

  const cfg = statusConfig[status] ?? statusConfig.idle;

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
      <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
      <span className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
    </div>
  );
};

// ── MAIN SIDEBAR ───────────────────────────────────────────────────────────────
const Sidebar = ({
  drivers = [],
  matchedDriver = null,
  priceData = null,
  loading = false,
  rideStatus = 'idle',
  onRequestRide,
}) => {
  const driversListRef = useRef(null);

  // Scroll matched driver into view in the list
  useEffect(() => {
    if (matchedDriver && driversListRef.current) {
      const el = driversListRef.current.querySelector(`[data-driver-id="${matchedDriver.id}"]`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }, [matchedDriver]);

  const availableCount = drivers.filter((d) => d.available).length;

  return (
    <aside className="flex flex-col h-full bg-[#1e293b] overflow-hidden">
      {/* ── Request button ─────────────────────────────────────── */}
      <div className="p-4 border-b border-slate-700/60 space-y-3 flex-shrink-0">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center text-base">
            📍
          </div>
          <div>
            <p className="text-xs text-slate-500 leading-none">Pickup</p>
            <p className="text-sm font-medium text-slate-200 leading-tight">
              Karachi City Centre
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-slate-700/60 flex items-center justify-center text-base">
            🏁
          </div>
          <div>
            <p className="text-xs text-slate-500 leading-none">Drop-off</p>
            <p className="text-sm font-medium text-slate-200 leading-tight">
              AI-Determined Route
            </p>
          </div>
        </div>

        <button
          onClick={onRequestRide}
          disabled={loading || rideStatus === 'searching'}
          className={`
            w-full py-3 rounded-xl font-bold text-sm tracking-wide
            flex items-center justify-center gap-2
            transition-all duration-200 select-none
            ${
              loading || rideStatus === 'searching'
                ? 'bg-green-600/50 text-green-300 cursor-not-allowed'
                : 'bg-green-500 hover:bg-green-400 active:bg-green-600 text-white shadow-lg shadow-green-900/40 hover:shadow-green-900/60'
            }
          `}
        >
          {loading || rideStatus === 'searching' ? (
            <>
              <svg
                className="animate-spin h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12" cy="12" r="10"
                  stroke="currentColor" strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v8z"
                />
              </svg>
              Matching with AI…
            </>
          ) : rideStatus === 'matched' ? (
            <>✓ Request Another Ride</>
          ) : (
            <>🚀 Request a Ride</>
          )}
        </button>

        <RideStatusCard status={rideStatus} />
      </div>

      {/* ── Scrollable content ──────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto space-y-5 p-4">

        {/* AI Match card — show only after a match */}
        {matchedDriver && (
          <div className="animate-slide-up">
            <SectionHeading>AI Match Result</SectionHeading>
            <div className="rounded-xl bg-gradient-to-br from-green-900/30 to-slate-800/80 border border-green-500/30 p-4 space-y-3 shadow-lg">
              {/* Driver avatar + name */}
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-green-500/20 border-2 border-green-500/50 flex items-center justify-center text-2xl shadow">
                  {matchedDriver.vehicle_type === 'bike'
                    ? '🏍️'
                    : matchedDriver.vehicle_type === 'suv'
                    ? '🚙'
                    : matchedDriver.vehicle_type === 'luxury'
                    ? '🚘'
                    : '🚗'}
                </div>
                <div>
                  <p className="text-base font-bold text-green-300 leading-tight">
                    {matchedDriver.name}
                  </p>
                  <p className="text-xs text-slate-400 capitalize">
                    {matchedDriver.vehicle_type}
                  </p>
                  <StarRating rating={matchedDriver.rating ?? 4.8} />
                </div>
                <div className="ml-auto text-right">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500">ETA</p>
                  <p className="text-xl font-bold text-white leading-tight">
                    {matchedDriver.eta_minutes ?? 4}
                    <span className="text-xs text-slate-400 ml-0.5">min</span>
                  </p>
                </div>
              </div>

              {/* Details row */}
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-slate-800/60 rounded-lg px-3 py-2">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500">Distance</p>
                  <p className="text-sm font-semibold text-slate-200">
                    {typeof matchedDriver.distance_km === 'number'
                      ? `${matchedDriver.distance_km.toFixed(1)} km`
                      : matchedDriver.distance_km ?? '—'}
                  </p>
                </div>
                <div className="bg-slate-800/60 rounded-lg px-3 py-2">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500">Trips</p>
                  <p className="text-sm font-semibold text-slate-200">
                    {matchedDriver.total_trips ?? Math.floor(Math.random() * 400 + 100)}+
                  </p>
                </div>
              </div>

              {/* Confidence bar */}
              <ConfidenceBar
                value={
                  matchedDriver.confidence
                    ? Math.round(matchedDriver.confidence * 100)
                    : 94
                }
              />

              {/* Algorithm badge */}
              <div className="flex items-center gap-2 pt-1">
                <span className="text-[10px] bg-green-500/20 text-green-400 border border-green-500/30 px-2 py-0.5 rounded-full font-medium">
                  🤖 Random Forest
                </span>
                <span className="text-[10px] bg-slate-700/60 text-slate-400 border border-slate-600/40 px-2 py-0.5 rounded-full">
                  {matchedDriver.features_used ?? 12} features
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Price breakdown — show only after pricing */}
        {priceData && matchedDriver && (
          <div className="animate-slide-up">
            <SectionHeading>Price Breakdown</SectionHeading>
            <div className="rounded-xl bg-slate-800/60 border border-slate-700/50 px-4 py-3 space-y-0.5 shadow">
              <PriceRow
                label="Base Fare"
                value={`PKR ${priceData.base_fare ?? 150}`}
              />
              <PriceRow
                label="Distance Charge"
                value={`PKR ${priceData.distance_charge ?? 80}`}
              />
              <PriceRow
                label="Service Fee"
                value={`PKR ${priceData.service_fee ?? 20}`}
              />

              {priceData.surge_multiplier && priceData.surge_multiplier > 1.0 && (
                <div className="flex items-center justify-between py-1">
                  <span className="text-xs text-slate-400">Surge Pricing</span>
                  <span className="text-xs bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded-full font-bold">
                    {priceData.surge_multiplier.toFixed(1)}×
                  </span>
                </div>
              )}

              <div className="border-t border-slate-700/50 pt-2 mt-1">
                <PriceRow
                  label="Total"
                  value={`PKR ${priceData.total ?? 250}`}
                  large
                />
              </div>

              <p className="text-[10px] text-slate-600 text-right pt-1">
                Estimated — final may vary
              </p>
            </div>
          </div>
        )}

        {/* Nearby drivers list */}
        <div>
          <div className="flex items-center justify-between mb-2 px-1">
            <SectionHeading>
              Nearby Drivers
            </SectionHeading>
            <span className="text-[10px] text-slate-500">
              {availableCount} available
            </span>
          </div>

          {drivers.length === 0 ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="skeleton h-16 w-full" />
              ))}
            </div>
          ) : (
            <div
              ref={driversListRef}
              className="space-y-2"
            >
              {drivers.map((driver) => (
                <div key={driver.id} data-driver-id={driver.id}>
                  <DriverCard
                    driver={driver}
                    isMatched={matchedDriver?.id === driver.id}
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Bottom padding */}
        <div className="h-4" />
      </div>
    </aside>
  );
};

export default Sidebar;
