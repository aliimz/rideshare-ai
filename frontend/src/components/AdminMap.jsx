import React from 'react';
import { CircleMarker, MapContainer, Marker, Popup, Polyline, TileLayer } from 'react-leaflet';
import L from 'leaflet';

const LAHORE_CENTER = [31.5204, 74.3587];

const createStatusIcon = (color) =>
  L.divIcon({
    className: '',
    iconSize: [18, 18],
    iconAnchor: [9, 9],
    html: `
      <div style="width:18px;height:18px;border-radius:999px;background:${color};border:3px solid rgba(15,23,42,0.9);box-shadow:0 0 0 6px ${color}22;"></div>
    `,
  });

const requestedIcon = createStatusIcon('#f59e0b');
const activeIcon = createStatusIcon('#22c55e');

const AdminMap = ({ heatmap = [], rides = [] }) => {
  const activeRides = rides.filter((ride) =>
    ['requested', 'matched', 'en_route', 'arrived', 'in_progress'].includes(ride.status)
  );

  return (
    <div className="h-[420px] overflow-hidden rounded-3xl border border-slate-800 shadow-2xl">
      <MapContainer center={LAHORE_CENTER} zoom={12} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap &copy; CARTO'
          subdomains="abcd"
          maxZoom={20}
        />

        {heatmap.map((point, index) => (
          <CircleMarker
            key={`heat-${index}`}
            center={[point.lat, point.lng]}
            radius={12 + point.intensity * 26}
            pathOptions={{
              color: point.avg_surge > 1.05 ? '#f97316' : '#14b8a6',
              fillColor: point.avg_surge > 1.05 ? '#fb923c' : '#2dd4bf',
              fillOpacity: 0.2 + point.intensity * 0.35,
              weight: 1.5,
            }}
          >
            <Popup>
              <div className="space-y-1 text-sm">
                <p className="font-semibold text-white">Demand cluster</p>
                <p className="text-slate-300">Rides: {point.rides}</p>
                <p className="text-slate-300">Avg surge: {point.avg_surge.toFixed(2)}x</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {activeRides.map((ride) => (
          <React.Fragment key={ride.id}>
            <Polyline
              positions={[
                [ride.pickup_lat, ride.pickup_lng],
                [ride.dropoff_lat, ride.dropoff_lng],
              ]}
              pathOptions={{
                color: ride.status === 'requested' ? '#f59e0b' : '#22c55e',
                weight: 3,
                opacity: 0.5,
                dashArray: ride.status === 'requested' ? '5 8' : undefined,
              }}
            />
            <Marker
              position={[ride.pickup_lat, ride.pickup_lng]}
              icon={ride.status === 'requested' ? requestedIcon : activeIcon}
            >
              <Popup>
                <div className="space-y-1 text-sm">
                  <p className="font-semibold text-white">Ride #{ride.id}</p>
                  <p className="capitalize text-slate-300">Status: {ride.status.replace('_', ' ')}</p>
                  <p className="text-slate-300">Rider: {ride.rider_name}</p>
                  <p className="text-slate-300">Driver: {ride.driver_name}</p>
                </div>
              </Popup>
            </Marker>
          </React.Fragment>
        ))}
      </MapContainer>
    </div>
  );
};

export default AdminMap;
