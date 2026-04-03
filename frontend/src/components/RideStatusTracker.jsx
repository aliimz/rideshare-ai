import React, { useEffect, useState } from 'react';

// ---------------------------------------------------------------------------
// Status step definitions
// ---------------------------------------------------------------------------

const STEPS = [
  { key: 'requested',   label: 'Requested',   icon: '🔵', shortLabel: 'Requested' },
  { key: 'matched',     label: 'Matched',     icon: '🟡', shortLabel: 'Matched'   },
  { key: 'en_route',   label: 'En Route',    icon: '🚗', shortLabel: 'En Route'  },
  { key: 'arrived',    label: 'Arrived',     icon: '📍', shortLabel: 'Arrived'   },
  { key: 'in_progress', label: 'In Progress', icon: '🚀', shortLabel: 'In Prog.'  },
  { key: 'completed',  label: 'Completed',   icon: '✅', shortLabel: 'Done'      },
];

const STATUS_ORDER = STEPS.map((s) => s.key);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Return how many seconds have elapsed since the given ISO timestamp. */
function secondsSince(isoString) {
  if (!isoString) return null;
  return Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
}

/** Format elapsed seconds to a human-readable string like "2m 34s" or "45s". */
function formatElapsed(seconds) {
  if (seconds === null || seconds < 0) return null;
  if (seconds < 60) return `${seconds}s ago`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s ago`;
}

// ---------------------------------------------------------------------------
// Step indicator
// ---------------------------------------------------------------------------

const StepDot = ({ step, stepIndex, activeIndex, timestamps }) => {
  const isPast    = stepIndex < activeIndex;
  const isCurrent = stepIndex === activeIndex;
  const isFuture  = stepIndex > activeIndex;

  const [elapsed, setElapsed] = useState(null);

  useEffect(() => {
    const ts = timestamps[step.key];
    if (!ts) return;

    const tick = () => setElapsed(secondsSince(ts));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [step.key, timestamps]);

  return (
    <div className="flex flex-col items-center" style={{ minWidth: 0, flex: 1 }}>
      {/* Dot */}
      <div
        className={`
          relative flex items-center justify-center
          w-9 h-9 rounded-full text-base
          border-2 transition-all duration-500
          ${isCurrent
            ? 'border-green-500 bg-green-500/20 shadow-[0_0_12px_rgba(34,197,94,0.5)]'
            : isPast
            ? 'border-green-600/60 bg-green-900/30'
            : 'border-slate-600/60 bg-slate-800/40'}
        `}
      >
        {/* Pulse ring on current step */}
        {isCurrent && (
          <span className="absolute inset-0 rounded-full border-2 border-green-500 animate-ping opacity-60" />
        )}
        <span className={isFuture ? 'opacity-30' : ''}>{step.icon}</span>
      </div>

      {/* Label */}
      <span
        className={`
          mt-1.5 text-[10px] font-semibold text-center leading-tight
          ${isCurrent ? 'text-green-400' : isPast ? 'text-green-600/80' : 'text-slate-600'}
        `}
      >
        {step.shortLabel}
      </span>

      {/* Elapsed time (only for past or current steps that have a timestamp) */}
      {(isPast || isCurrent) && elapsed !== null && (
        <span className="mt-0.5 text-[9px] text-slate-500 text-center leading-tight">
          {formatElapsed(elapsed)}
        </span>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Connector line between steps
// ---------------------------------------------------------------------------

const Connector = ({ filled }) => (
  <div className="flex-1 relative flex items-center" style={{ marginTop: '-18px' }}>
    <div className="w-full h-0.5 bg-slate-700/60 rounded-full overflow-hidden">
      <div
        className="h-full bg-green-500/70 rounded-full transition-all duration-700"
        style={{ width: filled ? '100%' : '0%' }}
      />
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// RideStatusTracker
// ---------------------------------------------------------------------------

/**
 * Visual ride status timeline.
 *
 * Props
 * -----
 * status      : string  — current ride status key (e.g. "matched", "en_route")
 * timestamps  : object  — { requested_at, matched_at, completed_at, ... }
 *                         Keys match step keys with "_at" suffix where applicable.
 *
 * The component normalises "idle" / "searching" / "error" to "requested" so it
 * renders gracefully before a ride exists.
 */
const RideStatusTracker = ({ status = 'requested', timestamps = {} }) => {
  // Normalise pre-ride states
  const normalisedStatus =
    status === 'idle' || status === 'searching' || status === 'error'
      ? 'requested'
      : status;

  const activeIndex = STATUS_ORDER.indexOf(normalisedStatus);
  const safeActiveIndex = activeIndex === -1 ? 0 : activeIndex;

  // Build a timestamp lookup keyed by step key
  const stepTimestamps = {
    requested:   timestamps.requested_at   ?? null,
    matched:     timestamps.matched_at     ?? null,
    en_route:   timestamps.en_route_at    ?? null,
    arrived:    timestamps.arrived_at     ?? null,
    in_progress: timestamps.in_progress_at ?? null,
    completed:  timestamps.completed_at   ?? null,
  };

  const currentStep = STEPS[safeActiveIndex];

  return (
    <div className="rounded-xl bg-[#1e293b] border border-slate-700/50 p-4 shadow-md">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">
          Ride Progress
        </h3>
        <span
          className={`
            text-[10px] font-bold px-2 py-0.5 rounded-full border
            ${normalisedStatus === 'completed'
              ? 'bg-green-500/20 text-green-400 border-green-500/30'
              : normalisedStatus === 'requested'
              ? 'bg-slate-700/60 text-slate-400 border-slate-600/40'
              : 'bg-blue-500/20 text-blue-400 border-blue-500/30 animate-pulse'}
          `}
        >
          {currentStep.label}
        </span>
      </div>

      {/* Timeline */}
      <div className="flex items-start gap-0">
        {STEPS.map((step, idx) => (
          <React.Fragment key={step.key}>
            <StepDot
              step={step}
              stepIndex={idx}
              activeIndex={safeActiveIndex}
              timestamps={stepTimestamps}
            />
            {idx < STEPS.length - 1 && (
              <Connector filled={idx < safeActiveIndex} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Status message */}
      <p className="mt-3 text-xs text-slate-500 text-center">
        {normalisedStatus === 'requested'  && 'Waiting for a driver to be matched…'}
        {normalisedStatus === 'matched'    && 'Your driver has been matched and is preparing to depart.'}
        {normalisedStatus === 'en_route'  && 'Your driver is on the way to pick you up.'}
        {normalisedStatus === 'arrived'   && 'Your driver has arrived at the pickup point.'}
        {normalisedStatus === 'in_progress' && 'You are currently on your trip.'}
        {normalisedStatus === 'completed' && 'Ride complete. Thank you for riding with us!'}
      </p>
    </div>
  );
};

export default RideStatusTracker;
