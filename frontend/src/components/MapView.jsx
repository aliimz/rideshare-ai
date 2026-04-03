import React, { useEffect, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Circle,
  Popup,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';

// Fix leaflet default icon paths broken by bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// ── Lahore centre ─────────────────────────────────────────────────────────────
const KARACHI_CENTER = [31.5204, 74.3587];

// ── Icon factories ────────────────────────────────────────────────────────────
const createDriverIcon = (available, isMatched) => {
  const bg = isMatched
    ? '#22c55e'
    : available
    ? '#3b82f6'
    : '#475569';
  const border = isMatched ? '#86efac' : available ? '#93c5fd' : '#64748b';
  const glow = isMatched
    ? '0 0 0 4px rgba(34,197,94,0.3), 0 2px 10px rgba(0,0,0,0.6)'
    : '0 2px 8px rgba(0,0,0,0.5)';
  const emoji = isMatched ? '🚗' : available ? '🚕' : '🚫';

  return L.divIcon({
    className: '',
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -18],
    html: `
      <div style="
        width:34px; height:34px;
        border-radius:50%;
        background:${bg};
        border:2.5px solid ${border};
        box-shadow:${glow};
        display:flex; align-items:center; justify-content:center;
        font-size:15px;
        position:relative;
        ${isMatched ? 'animation: matchedRing 1.8s ease-in-out infinite;' : ''}
      ">${emoji}</div>
      ${
        isMatched
          ? `<style>
              @keyframes matchedRing {
                0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,0.6),0 2px 10px rgba(0,0,0,0.6)}
                50%{box-shadow:0 0 0 10px rgba(34,197,94,0),0 2px 10px rgba(0,0,0,0.6)}
              }
            </style>`
          : ''
      }
    `,
  });
};

const riderIcon = L.divIcon({
  className: '',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
  html: `
    <div style="position:relative;width:20px;height:20px;">
      <div style="
        position:absolute; inset:0;
        border-radius:50%;
        background:rgba(59,130,246,0.25);
        animation:riderPulse 2s ease-in-out infinite;
      "></div>
      <div style="
        position:absolute; top:4px; left:4px;
        width:12px; height:12px;
        border-radius:50%;
        background:#3b82f6;
        border:2.5px solid #93c5fd;
        box-shadow:0 0 10px rgba(59,130,246,0.7);
      "></div>
    </div>
    <style>
      @keyframes riderPulse {
        0%,100%{transform:scale(1);opacity:0.8}
        50%{transform:scale(2.4);opacity:0}
      }
    </style>
  `,
});

// ── Auto-pan to matched driver ────────────────────────────────────────────────
const MapController = ({ matchedDriver }) => {
  const map = useMap();
  const prevMatched = useRef(null);

  useEffect(() => {
    if (matchedDriver && matchedDriver.id !== prevMatched.current) {
      prevMatched.current = matchedDriver.id;
      map.flyTo(
        [matchedDriver.lat, matchedDriver.lng],
        14,
        { animate: true, duration: 1.4 }
      );
    }
    if (!matchedDriver && prevMatched.current) {
      prevMatched.current = null;
      map.flyTo(KARACHI_CENTER, 13, { animate: true, duration: 1 });
    }
  }, [matchedDriver, map]);

  return null;
};

// ── Star string helper ────────────────────────────────────────────────────────
const stars = (rating) => {
  const full = Math.round(rating);
  return '★'.repeat(full) + '☆'.repeat(5 - full);
};

// ── Main component ────────────────────────────────────────────────────────────
const MapView = ({ drivers = [], matchedDriver = null }) => {
  return (
    <MapContainer
      center={KARACHI_CENTER}
      zoom={13}
      style={{ height: '100%', width: '100%' }}
      zoomControl={true}
      attributionControl={true}
    >
      {/* CartoDB Dark tiles */}
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>'
        subdomains="abcd"
        maxZoom={20}
      />

      {/* Soft demand halo around city centre */}
      <Circle
        center={KARACHI_CENTER}
        radius={3200}
        pathOptions={{
          color: '#22c55e',
          fillColor: '#22c55e',
          fillOpacity: 0.035,
          weight: 1,
          opacity: 0.18,
          dashArray: '6 4',
        }}
      />

      {/* Rider position marker */}
      <Marker position={KARACHI_CENTER} icon={riderIcon}>
        <Popup>
          <div className="text-center py-1">
            <p className="font-semibold text-blue-400 text-sm">📍 Your Location</p>
            <p className="text-slate-400 text-xs mt-0.5">Lahore City Centre</p>
          </div>
        </Popup>
      </Marker>

      {/* Driver markers */}
      {drivers.map((driver) => {
        const isMatched = matchedDriver?.id === driver.id;
        return (
          <Marker
            key={driver.id}
            position={[driver.lat, driver.lng]}
            icon={createDriverIcon(driver.available, isMatched)}
          >
            <Popup>
              <div style={{ minWidth: '170px' }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">
                    {driver.vehicle_type === 'bike'
                      ? '🏍️'
                      : driver.vehicle_type === 'suv'
                      ? '🚙'
                      : driver.vehicle_type === 'luxury'
                      ? '🚘'
                      : driver.vehicle_type === 'van'
                      ? '🚐'
                      : '🚗'}
                  </span>
                  <div>
                    <p className="font-semibold text-slate-100 text-sm leading-none">
                      {driver.name}
                    </p>
                    <p className="text-slate-400 text-xs capitalize mt-0.5">
                      {driver.vehicle_type}
                    </p>
                  </div>
                </div>

                <div className="text-amber-400 text-sm mb-1">
                  {stars(driver.rating ?? 4.5)}{' '}
                  <span className="text-slate-400 text-xs">
                    {(driver.rating ?? 4.5).toFixed(1)}
                  </span>
                </div>

                {driver.distance_km !== undefined && (
                  <p className="text-xs text-slate-400">
                    📍 {Number(driver.distance_km).toFixed(1)} km away
                  </p>
                )}
                {driver.eta_minutes !== undefined && (
                  <p className="text-xs text-slate-400">
                    ⏱ ETA: {driver.eta_minutes} min
                  </p>
                )}

                <div className="mt-2 flex items-center gap-1.5">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      driver.available ? 'bg-green-500' : 'bg-slate-600'
                    }`}
                  />
                  <span
                    className={`text-xs font-medium ${
                      driver.available ? 'text-green-400' : 'text-slate-500'
                    }`}
                  >
                    {driver.available ? 'Available' : 'Unavailable'}
                  </span>
                  {isMatched && (
                    <span className="ml-auto text-[9px] bg-green-500 text-white px-1.5 py-0.5 rounded-full font-bold uppercase">
                      AI Match
                    </span>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        );
      })}

      <MapController matchedDriver={matchedDriver} />
    </MapContainer>
  );
};

export default MapView;
