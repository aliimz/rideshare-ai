import React, { useEffect } from 'react';
import {
  CircleMarker,
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';

const LAHORE_CENTER = [31.5204, 74.3587];

const createIcon = (background, border) =>
  L.divIcon({
    className: '',
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    html: `
      <div style="width:22px;height:22px;border-radius:999px;background:${background};border:4px solid ${border};box-shadow:0 0 0 6px ${background}22;"></div>
    `,
  });

const driverIcon = createIcon('#22c55e', '#052e16');
const activeRideIcon = createIcon('#38bdf8', '#082f49');

const MapViewport = ({ driver, activeRide }) => {
  const map = useMap();

  useEffect(() => {
    if (activeRide) {
      map.flyTo([activeRide.pickup_lat, activeRide.pickup_lng], 13, {
        animate: true,
        duration: 0.8,
      });
      return;
    }

    if (driver?.lat && driver?.lng) {
      map.flyTo([driver.lat, driver.lng], 13, {
        animate: true,
        duration: 0.8,
      });
    }
  }, [activeRide, driver, map]);

  return null;
};

const DriverMap = ({ driver, incomingRequests = [], activeRide }) => {
  const center =
    driver?.lat && driver?.lng ? [driver.lat, driver.lng] : LAHORE_CENTER;

  return (
    <div className="h-[420px] overflow-hidden rounded-3xl border border-slate-800 shadow-2xl">
      <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap &copy; CARTO'
          subdomains="abcd"
          maxZoom={20}
        />

        {driver?.lat && driver?.lng ? (
          <Marker position={[driver.lat, driver.lng]} icon={driverIcon}>
            <Popup>
              <div className="space-y-1 text-sm">
                <p className="font-semibold text-white">{driver.name}</p>
                <p className="text-slate-300">Status: {driver.available ? 'Online' : 'Offline or busy'}</p>
              </div>
            </Popup>
          </Marker>
        ) : null}

        {incomingRequests.map((request) => (
          <CircleMarker
            key={request.id}
            center={[request.pickup_lat, request.pickup_lng]}
            radius={12}
            pathOptions={{
              color: '#f59e0b',
              fillColor: '#fbbf24',
              fillOpacity: 0.35,
              weight: 2,
            }}
          >
            <Popup>
              <div className="space-y-1 text-sm">
                <p className="font-semibold text-white">Ride #{request.id}</p>
                <p className="text-slate-300">{request.rider_name}</p>
                <p className="text-slate-300">{request.pickup_address}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {activeRide ? (
          <>
            <Marker position={[activeRide.pickup_lat, activeRide.pickup_lng]} icon={activeRideIcon}>
              <Popup>
                <div className="space-y-1 text-sm">
                  <p className="font-semibold text-white">Active pickup</p>
                  <p className="text-slate-300">{activeRide.pickup_address}</p>
                </div>
              </Popup>
            </Marker>
            <Polyline
              positions={[
                [activeRide.pickup_lat, activeRide.pickup_lng],
                [activeRide.dropoff_lat, activeRide.dropoff_lng],
              ]}
              pathOptions={{ color: '#38bdf8', weight: 4, opacity: 0.7 }}
            />
          </>
        ) : null}

        <MapViewport driver={driver} activeRide={activeRide} />
      </MapContainer>
    </div>
  );
};

export default DriverMap;
