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

// ── Default centre ────────────────────────────────────────────────────────────
const DEFAULT_CENTER = [31.5204, 74.3587];

// ── Icon factories ────────────────────────────────────────────────────────────
const createDriverIcon = (available, isMatched, vehicleType = 'sedan') => {
  const size = isMatched ? 44 : 40;
  const height = Math.round(size * 1.2); // 53 or 48
  const iconTop = Math.round(size * 0.25); // ~11 or 10

  let light, dark;
  if (isMatched) {
    light = '#4ade80'; // green-400
    dark = '#16a34a';  // green-600
  } else if (available) {
    light = '#60a5fa'; // blue-400
    dark = '#2563eb';  // blue-600
  } else {
    light = '#94a3b8'; // slate-400
    dark = '#475569';  // slate-600
  }

  const opacity = available ? 1 : 0.65;

  const vehicleIcons = {
    bike: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="5.5" cy="17.5" r="3.5"/><circle cx="18.5" cy="17.5" r="3.5"/><circle cx="15" cy="5" r="1"/><path d="M12 17.5V14l-3-3 4-3 2 3h2"/></svg>`,
    suv: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 17h4V5H2v12h3m15 0h2a1 1 0 0 0 1-1v-4a1 1 0 0 0-1-1h-3V5h-6v12h2"/><circle cx="7.5" cy="17.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>`,
    van: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="13" height="11" rx="1"/><path d="M16 10h3a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1h-2"/><circle cx="7.5" cy="17.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>`,
    luxury: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l2.4 7.2h7.6l-6 4.8 2.4 7.2-6-4.8-6 4.8 2.4-7.2-6-4.8h7.6z" fill="white" stroke="none"/></svg>`,
    sedan: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/></svg>`,
  };

  const vehicleSvg = vehicleIcons[vehicleType] || vehicleIcons.sedan;

  const pulse = isMatched
    ? `<div style="position:absolute;left:50%;top:${height - 4}px;transform:translate(-50%,-50%);width:${size}px;height:${size}px;border-radius:50%;background:${dark};opacity:0.5;animation:pinPulse 2s ease-out infinite;z-index:-1;"></div>
       <style>@keyframes pinPulse{0%{transform:translate(-50%,-50%) scale(1);opacity:0.5}70%{transform:translate(-50%,-50%) scale(2.2);opacity:0}100%{transform:translate(-50%,-50%) scale(1);opacity:0}}</style>`
    : '';

  const html = `
    <div style="position:relative;width:${size}px;height:${height}px;opacity:${opacity};">
      ${pulse}
      <svg width="${size}" height="${height}" viewBox="0 0 40 48" style="display:block;filter:drop-shadow(0 3px 5px rgba(0,0,0,0.4));">
        <defs>
          <linearGradient id="pinGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:${light};stop-opacity:1" />
            <stop offset="100%" style="stop-color:${dark};stop-opacity:1" />
          </linearGradient>
        </defs>
        <path d="M20 0C9 0 0 9 0 20c0 11 20 28 20 28s20-17 20-28C40 9 31 0 20 0z" fill="url(#pinGrad)"/>
      </svg>
      <div style="position:absolute;top:${iconTop}px;left:50%;transform:translateX(-50%);width:20px;height:20px;">
        ${vehicleSvg}
      </div>
    </div>
  `;

  return L.divIcon({
    className: '',
    iconSize: [size, height],
    iconAnchor: [size / 2, height],
    popupAnchor: [0, -height + 6],
    html,
  });
};

const riderIcon = L.divIcon({
  className: '',
  iconSize: [32, 40],
  iconAnchor: [16, 40],
  popupAnchor: [0, -34],
  html: `
    <div style="position:relative;width:32px;height:40px;">
      <svg width="32" height="40" viewBox="0 0 32 40" style="display:block;filter:drop-shadow(0 3px 6px rgba(59,130,246,0.5));">
        <path d="M16 0C7.2 0 0 7.2 0 16c0 8.8 16 24 16 24s16-15.2 16-24C32 7.2 24.8 0 16 0z" fill="#3b82f6"/>
        <circle cx="16" cy="11" r="3.5" fill="white"/>
        <path d="M11 21c0-2.8 2.2-5 5-5s5 2.2 5 5v1H11v-1z" fill="white"/>
      </svg>
    </div>
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
    if (!matchedDriver) {
      prevMatched.current = null;
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
const MapView = ({ drivers = [], matchedDriver = null, riderPosition = DEFAULT_CENTER }) => {
  return (
    <MapContainer
      center={riderPosition}
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
        center={riderPosition}
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
      <Marker position={riderPosition} icon={riderIcon}>
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
            icon={createDriverIcon(driver.available, isMatched, driver.vehicle_type)}
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
