import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for consistent error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';
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
 * Get dynamic pricing for a ride.
 * @param {number} distance - Estimated distance in km
 * @param {number} demand - Current demand multiplier (1.0 = normal)
 * @returns {Promise<Object>} Price breakdown object
 */
export const getPrice = (distance, demand) =>
  apiClient.post('/price', { distance_km: distance, demand_factor: demand });

/**
 * Fetch heatmap data for demand visualization.
 * @returns {Promise<Array>} Array of [lat, lng, intensity] tuples
 */
export const getHeatmap = () => apiClient.get('/heatmap');

export default apiClient;
