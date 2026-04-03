import React, { useState } from 'react';

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const ReceiptRow = ({ label, value, accent = false, muted = false }) => (
  <div className="flex items-center justify-between py-1.5">
    <span className={`text-xs ${muted ? 'text-slate-600' : 'text-slate-400'}`}>
      {label}
    </span>
    <span
      className={`text-xs font-semibold ${
        accent ? 'text-amber-400' : muted ? 'text-slate-600' : 'text-slate-300'
      }`}
    >
      {value}
    </span>
  </div>
);

const StatusBadge = ({ paid }) => (
  <span
    className={`
      inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider
      px-2.5 py-1 rounded-full border
      ${paid
        ? 'bg-green-500/20 text-green-400 border-green-500/30'
        : 'bg-amber-500/15 text-amber-400 border-amber-500/30'}
    `}
  >
    <span
      className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
        paid ? 'bg-green-500' : 'bg-amber-500 animate-pulse'
      }`}
    />
    {paid ? 'Paid' : 'Pending'}
  </span>
);

const Spinner = () => (
  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
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
);

// ---------------------------------------------------------------------------
// PaymentCard
// ---------------------------------------------------------------------------

/**
 * Receipt-style payment card shown after a ride completes.
 *
 * Props
 * -----
 * fare         : { base, surge_charge, total }   — PKR amounts
 * surgeMultiplier : number                        — e.g. 1.4
 * onPaid       : () => void                       — called after payment succeeds
 */
const PaymentCard = ({
  fare = { base: 150, surge_charge: 0, total: 150 },
  surgeMultiplier = 1.0,
  onPaid,
}) => {
  const [paid,    setPaid]    = useState(false);
  const [loading, setLoading] = useState(false);

  const handlePayNow = async () => {
    if (paid || loading) return;

    setLoading(true);
    // Simulate a 1.5-second payment processing delay
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setPaid(true);
    setLoading(false);
    if (typeof onPaid === 'function') onPaid();
  };

  const hasSurge = surgeMultiplier > 1.0;

  return (
    <div
      className="
        rounded-xl bg-[#1e293b] border border-slate-700/50 shadow-md
        overflow-hidden
      "
    >
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <h3 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">
          Payment
        </h3>
        <StatusBadge paid={paid} />
      </div>

      {/* Dashed receipt body */}
      <div
        className="mx-4 mb-4 rounded-lg border border-dashed border-slate-600/50 px-4 py-3"
        style={{ background: 'rgba(15, 23, 42, 0.5)' }}
      >
        {/* Fare rows */}
        <ReceiptRow
          label="Base Fare"
          value={`PKR ${fare.base?.toFixed(2) ?? '—'}`}
        />

        {hasSurge && (
          <ReceiptRow
            label={`Surge (${surgeMultiplier.toFixed(1)}×)`}
            value={`PKR ${fare.surge_charge?.toFixed(2) ?? '—'}`}
            accent
          />
        )}

        {/* Divider */}
        <div className="my-2 border-t border-dashed border-slate-700/60" />

        {/* Total */}
        <div className="flex items-center justify-between py-1">
          <span className="text-sm font-bold text-slate-200">Total</span>
          <span className="text-base font-extrabold text-green-400">
            PKR {fare.total?.toFixed(2) ?? '—'}
          </span>
        </div>

        <p className="text-[9px] text-slate-700 text-right mt-0.5">
          All amounts in Pakistani Rupees (PKR)
        </p>
      </div>

      {/* Pay Now button */}
      <div className="px-4 pb-4">
        <button
          onClick={handlePayNow}
          disabled={paid || loading}
          className={`
            w-full py-3 rounded-xl font-bold text-sm tracking-wide
            flex items-center justify-center gap-2
            transition-all duration-200 select-none
            ${paid
              ? 'bg-green-600/30 text-green-400 cursor-default border border-green-500/30'
              : loading
              ? 'bg-green-600/50 text-green-300 cursor-not-allowed'
              : 'bg-green-500 hover:bg-green-400 active:bg-green-600 text-white shadow-lg shadow-green-900/40 hover:shadow-green-900/60'}
          `}
        >
          {loading && <Spinner />}
          {paid    ? '✓ Payment Complete' : loading ? 'Processing…' : '💳 Pay Now'}
        </button>

        {paid && (
          <p className="mt-2 text-[10px] text-slate-600 text-center">
            Receipt sent to your account
          </p>
        )}
      </div>
    </div>
  );
};

export default PaymentCard;
