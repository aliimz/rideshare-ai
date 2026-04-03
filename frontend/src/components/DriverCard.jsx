import React from 'react';

const VEHICLE_EMOJI = {
  sedan: '🚗',
  suv: '🚙',
  bike: '🏍️',
  van: '🚐',
  luxury: '🚘',
};

const StarRating = ({ rating }) => {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);

  return (
    <span className="flex items-center gap-0.5 text-xs">
      {Array.from({ length: full }).map((_, i) => (
        <span key={`f${i}`} className="text-amber-400">★</span>
      ))}
      {half && <span className="text-amber-400 opacity-60">★</span>}
      {Array.from({ length: empty }).map((_, i) => (
        <span key={`e${i}`} className="text-slate-600">★</span>
      ))}
      <span className="text-slate-400 ml-1">{rating.toFixed(1)}</span>
    </span>
  );
};

const DriverCard = ({ driver, isMatched = false }) => {
  const {
    name,
    rating = 4.5,
    distance_km,
    vehicle_type = 'sedan',
    available = true,
    eta_minutes,
  } = driver;

  const vehicleEmoji = VEHICLE_EMOJI[vehicle_type] ?? '🚗';

  return (
    <div
      className={`
        relative flex items-center gap-3 px-3 py-2.5 rounded-lg
        border transition-all duration-300 cursor-default
        ${
          isMatched
            ? 'bg-green-500/10 border-green-500/50 shadow-[0_0_16px_rgba(34,197,94,0.15)]'
            : 'bg-slate-800/40 border-slate-700/50 hover:border-slate-600/60 hover:bg-slate-800/60'
        }
      `}
    >
      {/* Matched badge */}
      {isMatched && (
        <span className="absolute -top-2 -right-1 text-[9px] bg-green-500 text-white font-bold px-1.5 py-0.5 rounded-full uppercase tracking-wider shadow">
          Matched
        </span>
      )}

      {/* Vehicle emoji avatar */}
      <div
        className={`
          flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-lg
          ${isMatched ? 'bg-green-500/20' : 'bg-slate-700/60'}
        `}
      >
        {vehicleEmoji}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-1">
          <span
            className={`text-sm font-semibold truncate ${
              isMatched ? 'text-green-300' : 'text-slate-200'
            }`}
          >
            {name}
          </span>
          {/* Availability dot */}
          <span
            className={`flex-shrink-0 w-2 h-2 rounded-full ${
              available ? 'bg-green-500' : 'bg-slate-600'
            }`}
            title={available ? 'Available' : 'Unavailable'}
          />
        </div>

        <StarRating rating={rating} />

        <div className="flex items-center gap-3 mt-0.5">
          {distance_km !== undefined && (
            <span className="text-[11px] text-slate-500">
              📍 {typeof distance_km === 'number' ? distance_km.toFixed(1) : distance_km} km
            </span>
          )}
          {eta_minutes !== undefined && (
            <span className="text-[11px] text-slate-500">
              ⏱ {eta_minutes} min
            </span>
          )}
          <span className="text-[11px] text-slate-600 capitalize ml-auto">
            {vehicle_type}
          </span>
        </div>
      </div>
    </div>
  );
};

export default DriverCard;
