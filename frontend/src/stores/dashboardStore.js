import { create } from 'zustand';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CACHE_DURATION = 30000; // 30 seconds

const useDashboardStore = create((set, get) => ({
  // Data
  summary: {
    income: 0,
    expense: 0,
    net_savings: 0,
    income_count: 0,
    expense_count: 0
  },
  recentTransactions: [],
  leaderboard: [],
  gamificationProfile: null,
  insights: {},
  dailyTip: null,
  countdownAlerts: [],
  limitedOffers: [],
  
  // State
  loading: false,
  refreshing: false,
  error: null,
  lastFetch: null,
  
  // Check if data is stale
  isStale: () => {
    const { lastFetch } = get();
    if (!lastFetch) return true;
    return Date.now() - lastFetch > CACHE_DURATION;
  },
  
  // Fetch all dashboard data
  fetchDashboard: async (force = false) => {
    const { isStale, loading } = get();
    
    // Return cached data if not stale and not forcing refresh
    if (!force && !isStale() && !loading) {
      return;
    }
    
    try {
      set({ loading: !get().lastFetch, refreshing: !!get().lastFetch, error: null });
      
      const token = localStorage.getItem('token');
      const headers = { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      const [
        summaryRes, 
        transactionsRes, 
        leaderboardRes, 
        insightsRes, 
        gamificationRes, 
        dailyTipRes, 
        countdownRes,
        offersRes
      ] = await Promise.all([
        axios.get(`${API}/transactions/summary`, { headers }),
        axios.get(`${API}/transactions?limit=5`, { headers }),
        axios.get(`${API}/analytics/leaderboard`, { headers }),
        axios.get(`${API}/analytics/insights`, { headers }),
        axios.get(`${API}/gamification/profile`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/engagement/daily-tip`, { headers }).catch(() => ({ data: null })),
        axios.get(`${API}/engagement/countdown-alerts`, { headers }).catch(() => ({ data: { countdown_alerts: [] } })),
        axios.get(`${API}/engagement/limited-offers`, { headers }).catch(() => ({ data: [] }))
      ]);

      set({
        summary: summaryRes.data,
        recentTransactions: transactionsRes.data,
        leaderboard: leaderboardRes.data,
        insights: insightsRes.data,
        gamificationProfile: gamificationRes.data,
        dailyTip: dailyTipRes.data,
        countdownAlerts: countdownRes.data?.countdown_alerts || [],
        limitedOffers: offersRes.data || [],
        lastFetch: Date.now(),
        loading: false,
        refreshing: false,
        error: null
      });
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      set({ 
        error: error.message,
        loading: false,
        refreshing: false
      });
    }
  },
  
  // Update specific parts of dashboard
  updateSummary: (summary) => set({ summary }),
  updateTransactions: (transactions) => set({ recentTransactions: transactions }),
  updateLeaderboard: (leaderboard) => set({ leaderboard }),
  
  // Reset store
  reset: () => set({
    summary: { income: 0, expense: 0, net_savings: 0, income_count: 0, expense_count: 0 },
    recentTransactions: [],
    leaderboard: [],
    gamificationProfile: null,
    insights: {},
    dailyTip: null,
    countdownAlerts: [],
    limitedOffers: [],
    loading: false,
    refreshing: false,
    error: null,
    lastFetch: null
  })
}));

export default useDashboardStore;
