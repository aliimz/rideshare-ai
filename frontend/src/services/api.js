import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const setAuthToken = (token) => {
  if (token) {
    apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common.Authorization;
  }
};

// Response interceptor for consistent error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const detail = error.response?.data?.detail;
    // FastAPI validation errors return detail as an array of objects
    const message = Array.isArray(detail)
      ? detail.map((e) => e.msg).join(', ')
      : detail || error.response?.data?.message || error.message || 'An unexpected error occurred';
    return Promise.reject(new Error(message));
  }
);

/**
 * Fetch all available drivers from the backend.
 * @returns {Promise<Array>} List of driver objects
 */
export const getDrivers = () => apiClient.get('/drivers');

/**
 * Request an AI-matched ride for a given rider position.
 * @param {number} lat - Rider latitude
 * @param {number} lng - Rider longitude
 * @returns {Promise<Object>} Matched driver object with confidence score
 */
export const matchRide = (lat, lng) =>
  apiClient.post('/match', { rider_lat: lat, rider_lng: lng });

/**
 * Get AI-predicted dynamic pricing for a ride.
 * @param {number} distance - Estimated distance in km
 * @param {number} lat - Pickup latitude for demand prediction
 * @param {number} lng - Pickup longitude for demand prediction
 * @returns {Promise<Object>} Price breakdown object
 */
export const getPrice = (distance, lat, lng) =>
  apiClient.post('/price', { distance_km: distance, pickup_lat: lat, pickup_lng: lng });

/**
 * Fetch heatmap data for demand visualization.
 * @returns {Promise<Array>} Array of [lat, lng, intensity] tuples
 */
export const getHeatmap = () => apiClient.get('/heatmap');

export const createRide = (payload) => apiClient.post('/rides', payload);

export const login = (email, password) =>
  apiClient.post('/auth/login', { email, password });

export const getCurrentUser = () => apiClient.get('/auth/me');

export const getAdminOverview = () => apiClient.get('/admin/overview');

export const updateAdminDriverAvailability = (driverId, available) =>
  apiClient.patch(`/admin/drivers/${driverId}/availability`, { available });

export const getDriverDashboard = () => apiClient.get('/driver/dashboard');

export const updateDriverAvailability = (available) =>
  apiClient.patch('/driver/availability', { available });

export const updateDriverLocation = (lat, lng) =>
  apiClient.patch('/driver/location', { lat, lng });

export const acceptDriverRide = (rideId) =>
  apiClient.post(`/driver/rides/${rideId}/accept`);

export const rejectDriverRide = (rideId) =>
  apiClient.post(`/driver/rides/${rideId}/reject`);

export const updateDriverRideStatus = (rideId, status) =>
  apiClient.post(`/driver/rides/${rideId}/status`, { status });

export default apiClient;
