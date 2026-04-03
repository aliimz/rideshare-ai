/**
 * useWebSocket — connects to the RideShare AI WebSocket server and streams
 * real-time driver position updates.
 *
 * Returns:
 *   { drivers, connected, lastUpdate }
 *
 * Reconnects automatically 3 seconds after an unexpected disconnect.
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const WS_BASE_URL = 'ws://localhost:8080/ws';
const RECONNECT_DELAY_MS = 3_000;

/**
 * @param {string} clientId  Unique identifier for this browser session.
 * @returns {{ drivers: Array, connected: boolean, lastUpdate: Date | null }}
 */
export function useWebSocket(clientId) {
  const [drivers, setDrivers] = useState([]);
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Refs let the cleanup effect close the correct socket without stale closures
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const mountedRef = useRef(true);

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimerRef.current !== null) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    const url = `${WS_BASE_URL}/${encodeURIComponent(clientId)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) {
        ws.close();
        return;
      }
      setConnected(true);
      clearReconnectTimer();
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;

      let message;
      try {
        message = JSON.parse(event.data);
      } catch {
        // Malformed payload — ignore
        return;
      }

      const type = message?.type;

      if (type === 'initial_positions') {
        const incoming = Array.isArray(message.drivers) ? message.drivers : [];
        setDrivers(incoming);
        setLastUpdate(new Date());
        return;
      }

      if (type === 'driver_moved') {
        const moved = message.driver;
        if (!moved?.driver_id) return;
        setDrivers((prev) => {
          const exists = prev.some((d) => d.driver_id === moved.driver_id);
          if (exists) {
            return prev.map((d) =>
              d.driver_id === moved.driver_id ? { ...d, ...moved } : d
            );
          }
          return [...prev, moved];
        });
        setLastUpdate(new Date());
        return;
      }

      if (type === 'drivers_update') {
        const incoming = Array.isArray(message.drivers) ? message.drivers : [];
        setDrivers(incoming);
        setLastUpdate(new Date());
        return;
      }

      // type === 'error' or unknown — log only in development
      if (import.meta.env.DEV) {
        // eslint-disable-next-line no-console
        console.warn('[useWebSocket] server message:', message);
      }
    };

    ws.onerror = () => {
      // onclose fires immediately after onerror; reconnect logic lives there
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setConnected(false);
      wsRef.current = null;

      // Schedule reconnect
      reconnectTimerRef.current = setTimeout(() => {
        if (mountedRef.current) {
          connect();
        }
      }, RECONNECT_DELAY_MS);
    };
  }, [clientId, clearReconnectTimer]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      clearReconnectTimer();
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on intentional unmount
        wsRef.current.close();
        wsRef.current = null;
      }
      setConnected(false);
    };
  }, [connect, clearReconnectTimer]);

  return { drivers, connected, lastUpdate };
}
