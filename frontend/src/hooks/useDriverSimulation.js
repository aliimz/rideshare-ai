/**
 * useDriverSimulation — demo-mode hook that animates available drivers
 * with small random position changes every 2 seconds, giving the map a
 * live-tracking feel when the backend is offline.
 *
 * @param {Array} initialDrivers  The baseline driver array (e.g. MOCK_DRIVERS).
 * @returns {Array}               A stateful copy that updates every 2 s.
 */

import { useState, useEffect, useRef } from 'react';

const TICK_MS = 2_000;

/**
 * Slightly move a coordinate value by at most ±0.0005 degrees
 * (roughly ±55 m at Lahore's latitude).
 *
 * @param {number} value
 * @returns {number}
 */
function jitter(value) {
  return value + (Math.random() - 0.5) * 0.001;
}

/**
 * Return a new driver object with updated lat/lng, leaving all other fields
 * unchanged (immutable update).
 *
 * @param {Object} driver
 * @returns {Object}
 */
function moveDriver(driver) {
  if (!driver.available) return driver;
  return {
    ...driver,
    lat: jitter(driver.lat),
    lng: jitter(driver.lng),
  };
}

export function useDriverSimulation(initialDrivers) {
  const [drivers, setDrivers] = useState(() =>
    Array.isArray(initialDrivers) ? initialDrivers : []
  );

  // Keep a ref so the interval always sees the latest initialDrivers without
  // restarting the timer on each render
  const initialRef = useRef(initialDrivers);
  useEffect(() => {
    initialRef.current = initialDrivers;
  }, [initialDrivers]);

  // Sync state when the caller swaps out the whole initial array
  useEffect(() => {
    setDrivers(Array.isArray(initialDrivers) ? initialDrivers : []);
  }, [initialDrivers]);

  useEffect(() => {
    const id = setInterval(() => {
      setDrivers((prev) => prev.map(moveDriver));
    }, TICK_MS);

    return () => clearInterval(id);
  }, []); // intentionally empty — timer runs for the lifetime of the component

  return drivers;
}
