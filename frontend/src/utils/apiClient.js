import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors and token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 - Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Try to refresh token
        const token = localStorage.getItem('token');
        if (token) {
          const response = await axios.post(
            `${API_BASE}/auth/refresh-token`,
            {},
            { headers: { Authorization: `Bearer ${token}` } }
          );

          const newToken = response.data.token;
          localStorage.setItem('token', newToken);
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle 429 - Rate Limit
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'] || 60;
      console.warn(`Rate limited. Retry after ${retryAfter}s`);
    }

    return Promise.reject(error);
  }
);

// API endpoints
export const api = {
  // Auth
  auth: {
    login: (credentials) => apiClient.post('/auth/login', credentials),
    register: (userData) => apiClient.post('/auth/register', userData),
    refreshToken: () => apiClient.post('/auth/refresh-token'),
    logout: () => apiClient.post('/auth/logout'),
  },
  
  // Transactions
  transactions: {
    getAll: (params) => apiClient.get('/transactions', { params }),
    getSummary: () => apiClient.get('/transactions/summary'),
    create: (data) => apiClient.post('/transactions', data),
    update: (id, data) => apiClient.put(`/transactions/${id}`, data),
    delete: (id) => apiClient.delete(`/transactions/${id}`),
  },
  
  // Analytics
  analytics: {
    getLeaderboard: (params) => apiClient.get('/analytics/leaderboard', { params }),
    getInsights: () => apiClient.get('/analytics/insights'),
  },
  
  // Gamification
  gamification: {
    getProfile: () => apiClient.get('/gamification/profile'),
    claimReward: (rewardId) => apiClient.post(`/gamification/rewards/${rewardId}/claim`),
  },
  
  // Engagement
  engagement: {
    getDailyTip: () => apiClient.get('/engagement/daily-tip'),
    getCountdownAlerts: () => apiClient.get('/engagement/countdown-alerts'),
    getLimitedOffers: () => apiClient.get('/engagement/limited-offers'),
  },
  
  // Dashboard - Aggregated endpoint (to be created on backend)
  dashboard: {
    getAll: () => apiClient.get('/dashboard/all'),
  },
};

export default apiClient;
