import React, { useState, useEffect, useCallback } from 'react';
import MapView from './components/MapView.jsx';
import Sidebar from './components/Sidebar.jsx';
import StatsBar from './components/StatsBar.jsx';
import { getDrivers, matchRide, getPrice } from './services/api.js';

// ── Karachi rider position ────────────────────────────────────────────────────
const RIDER_LAT = 24.8607;
const RIDER_LNG = 67.0011;

// ── Mock data fallback (used when backend is offline) ─────────────────────────
const MOCK_DRIVERS = [
  { id: 1, name: 'Ahmed Khan',    lat: 24.8720, lng: 67.0120, rating: 4.8, vehicle_type: 'sedan',  available: true,  distance_km: 1.2, eta_minutes: 4,  total_trips: 512 },
  { id: 2, name: 'Bilal Raza',    lat: 24.8550, lng: 66.9950, rating: 4.6, vehicle_type: 'suv',    available: true,  distance_km: 2.1, eta_minutes: 7,  total_trips: 287 },
  { id: 3, name: 'Farrukh Ali',   lat: 24.8800, lng: 67.0300, rating: 4.9, vehicle_type: 'luxury', available: true,  distance_km: 2.8, eta_minutes: 9,  total_trips: 741 },
  { id: 4, name: 'Sara Mirza',    lat: 24.8450, lng: 67.0200, rating: 4.4, vehicle_type: 'sedan',  available: false, distance_km: 3.3, eta_minutes: 11, total_trips: 198 },
  { id: 5, name: 'Usman Tariq',   lat: 24.8650, lng: 67.0400, rating: 4.7, vehicle_type: 'bike',   available: true,  distance_km: 1.8, eta_minutes: 5,  total_trips: 334 },
  { id: 6, name: 'Nadia Sheikh',  lat: 24.8900, lng: 66.9900, rating: 4.5, vehicle_type: 'van',    available: true,  distance_km: 3.6, eta_minutes: 12, total_trips: 156 },
  { id: 7, name: 'Kamran Malik',  lat: 24.8380, lng: 67.0050, rating: 4.3, vehicle_type: 'sedan',  available: false, distance_km: 4.1, eta_minutes: 14, total_trips: 422 },
  { id: 8, name: 'Zara Hussain',  lat: 24.8700, lng: 66.9800, rating: 4.9, vehicle_type: 'suv',    available: true,  distance_km: 2.5, eta_minutes: 8,  total_trips: 603 },
];

const MOCK_MATCH = {
  ...MOCK_DRIVERS[0],
  confidence: 0.94,
  features_used: 12,
};

const MOCK_PRICE = {
  base_fare: 150,
  distance_charge: 80,
  service_fee: 20,
  surge_multiplier: 1.0,
  total: 250,
};

// ── Notification toast ────────────────────────────────────────────────────────
const Toast = ({ message, type = 'info', onClose }) => {
  useEffect(() => {
    const t = setTimeout(onClose, 4000);
    return () => clearTimeout(t);
  }, [onClose]);

  const colors = {
    info:    'bg-slate-800 border-slate-600 text-slate-200',
    success: 'bg-green-900/80 border-green-600/60 text-green-200',
    error:   'bg-red-900/80 border-red-600/60 text-red-200',
    warning: 'bg-amber-900/80 border-amber-600/60 text-amber-200',
  };

  return (
    <div
      className={`
        animate-slide-up flex items-start gap-3
        px-4 py-3 rounded-xl border shadow-xl
        text-sm max-w-xs
        ${colors[type]}
      `}
    >
      <span className="flex-shrink-0 mt-0.5">
        {type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}
      </span>
      <span className="flex-1">{message}</span>
      <button
        onClick={onClose}
        className="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity"
      >
        ✕
      </button>
    </div>
  );
};

// ── App ───────────────────────────────────────────────────────────────────────
const App = () => {
  const [drivers,       setDrivers]       = useState([]);
  const [matchedDriver, setMatchedDriver] = useState(null);
  const [priceData,     setPriceData]     = useState(null);
  const [loading,       setLoading]       = useState(false);
  const [rideStatus,    setRideStatus]    = useState('idle');
  const [toasts,        setToasts]        = useState([]);
  const [usingMockData, setUsingMockData] = useState(false);
  const [mobileTab,     setMobileTab]     = useState('map'); // 'map' | 'panel'

  // ── Toast helpers ─────────────────────────────────────────────────────────
  const addToast = useCallback((message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // ── Load drivers on mount ─────────────────────────────────────────────────
  useEffect(() => {
    const loadDrivers = async () => {
      try {
        const data = await getDrivers();
        const list = Array.isArray(data) ? data : data?.drivers ?? [];
        setDrivers(list);
        setUsingMockData(false);
      } catch {
        // Backend not running — use mock data for demo
        setDrivers(MOCK_DRIVERS);
        setUsingMockData(true);
        addToast('Backend offline — showing demo data', 'warning');
      }
    };

    loadDrivers();
  }, [addToast]);

  // ── Request ride handler ──────────────────────────────────────────────────
  const handleRequestRide = useCallback(async () => {
    // Reset previous match
    setMatchedDriver(null);
    setPriceData(null);
    setRideStatus('searching');
    setLoading(true);

    try {
      let matched;
      let price;

      if (usingMockData) {
        // Simulate network delay for realism
        await new Promise((r) => setTimeout(r, 1200));
        matched = MOCK_MATCH;

        await new Promise((r) => setTimeout(r, 600));
        price = MOCK_PRICE;
      } else {
        // Real backend calls
        const matchResponse = await matchRide(RIDER_LAT, RIDER_LNG);
        matched = matchResponse?.driver ?? matchResponse;

        const distanceKm =
          typeof matched?.distance_km === 'number' ? matched.distance_km : 3.5;
        const demandFactor = 1.0;

        const priceResponse = await getPrice(distanceKm, demandFactor);
        price = priceResponse;
      }

      setMatchedDriver(matched);
      setPriceData(price);
      setRideStatus('matched');
      addToast(
        `${matched.name} matched — ${matched.eta_minutes ?? 4} min ETA`,
        'success'
      );
    } catch (err) {
      setRideStatus('error');
      addToast(err?.message ?? 'Failed to find a driver. Please retry.', 'error');
    } finally {
      setLoading(false);
    }
  }, [usingMockData, addToast]);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-screen w-screen bg-[#0f172a] overflow-hidden">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <header className="flex-shrink-0 flex items-center justify-between px-5 py-3 bg-[#0f172a] border-b border-slate-700/60 z-10">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-green-500/20 border border-green-500/30 flex items-center justify-center text-xl">
            🚗
          </div>
          <div>
            <span className="text-lg font-extrabold text-white tracking-tight">
              RideShare{' '}
              <span className="text-green-400">AI</span>
            </span>
            <p className="text-[10px] text-slate-500 leading-none -mt-0.5">
              Karachi Intelligent Transport
            </p>
          </div>
        </div>

        {/* Centre badge */}
        <div className="hidden sm:flex items-center gap-2 bg-slate-800/60 border border-slate-700/50 rounded-full px-4 py-1.5">
          <span className="text-xs text-slate-400">📍</span>
          <span className="text-xs font-medium text-slate-300">Karachi, Pakistan</span>
        </div>

        {/* AI status */}
        <div className="flex items-center gap-2">
          {usingMockData && (
            <span className="text-[10px] bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded-full font-medium">
              Demo Mode
            </span>
          )}
          <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/30 rounded-full px-3 py-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
            </span>
            <span className="text-xs font-semibold text-green-400">AI Active</span>
          </div>
        </div>
      </header>

      {/* ── Stats bar ───────────────────────────────────────────────────── */}
      <StatsBar drivers={drivers} />

      {/* ── Body: sidebar + map ─────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* Sidebar — hidden on mobile when map tab active, full width when panel tab active, fixed on desktop */}
        <div className={`
          flex-shrink-0 border-r border-slate-700/60 overflow-hidden flex-col
          w-full md:w-[380px]
          ${mobileTab === 'panel' ? 'flex' : 'hidden'} md:flex
        `}>
          <Sidebar
            drivers={drivers}
            matchedDriver={matchedDriver}
            priceData={priceData}
            loading={loading}
            rideStatus={rideStatus}
            onRequestRide={() => { handleRequestRide(); setMobileTab('map'); }}
          />
        </div>

        {/* Map — full screen on mobile when map tab active */}
        <div className={`
          flex-1 relative flex-col
          ${mobileTab === 'map' ? 'flex' : 'hidden'} md:flex
        `}>
          <MapView
            drivers={drivers}
            matchedDriver={matchedDriver}
          />

          {/* Map overlay: model info badge — hidden on small screens */}
          <div className="absolute bottom-6 right-4 z-[1000] hidden sm:flex flex-col gap-2 items-end pointer-events-none">
            <div className="bg-[#0f172a]/90 backdrop-blur border border-slate-700/60 rounded-xl px-3 py-2 text-xs text-slate-400 shadow-xl">
              <div className="flex items-center gap-2 font-medium text-slate-300 mb-1">
                <span>🤖</span> AI Engine
              </div>
              <div className="space-y-0.5">
                <p>Model: <span className="text-green-400">Random Forest</span></p>
                <p>Features: <span className="text-slate-200">Distance, Rating, Demand</span></p>
                <p>City: <span className="text-slate-200">Karachi, PKT</span></p>
              </div>
            </div>
          </div>

          {/* Loading overlay on map */}
          {loading && (
            <div className="absolute inset-0 z-[999] bg-slate-950/40 backdrop-blur-sm flex items-center justify-center pointer-events-none">
              <div className="bg-[#1e293b]/95 border border-slate-600/60 rounded-2xl px-8 py-6 flex flex-col items-center gap-3 shadow-2xl">
                <div className="relative">
                  <div className="w-12 h-12 rounded-full border-4 border-slate-700 border-t-green-500 animate-spin" />
                  <span className="absolute inset-0 flex items-center justify-center text-lg">🤖</span>
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-white">AI Matching…</p>
                  <p className="text-xs text-slate-400 mt-0.5">Running Random Forest classifier</p>
                </div>
                <div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="w-1.5 h-1.5 rounded-full bg-green-500 animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Mobile bottom tab bar (hidden on md+) ───────────────────────── */}
      <nav className="md:hidden flex-shrink-0 flex border-t border-slate-700/60 bg-[#1e293b]">
        <button
          onClick={() => setMobileTab('map')}
          className={`flex-1 flex flex-col items-center justify-center py-3 gap-0.5 text-xs font-medium transition-colors
            ${mobileTab === 'map' ? 'text-green-400' : 'text-slate-500'}`}
        >
          <span className="text-xl">🗺️</span>
          Map
        </button>
        <button
          onClick={() => setMobileTab('panel')}
          className={`relative flex-1 flex flex-col items-center justify-center py-3 gap-0.5 text-xs font-medium transition-colors
            ${mobileTab === 'panel' ? 'text-green-400' : 'text-slate-500'}`}
        >
          <span className="text-xl">🚀</span>
          Ride
          {rideStatus === 'matched' && (
            <span className="absolute top-2 right-8 w-2 h-2 rounded-full bg-green-500" />
          )}
        </button>
      </nav>

      {/* ── Toast stack ─────────────────────────────────────────────────── */}
      <div className="fixed bottom-16 md:bottom-6 left-1/2 -translate-x-1/2 z-[2000] flex flex-col gap-2 items-center">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </div>
  );
};

export default App;
