import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { useAuth, formatCurrency } from '../App';
import DailyTips from './DailyTips';
import LimitedOffers from './LimitedOffers';
import { 
  BanknotesIcon, 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon,
  PlusIcon,
  TrophyIcon,
  FireIcon,
  LightBulbIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
  BoltIcon,
  GiftIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const { user } = useAuth();
  const [summary, setSummary] = useState({
    income: 0,
    expense: 0,
    net_savings: 0,
    income_count: 0,
    expense_count: 0
  });
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [gamificationProfile, setGamificationProfile] = useState(null);
  const [insights, setInsights] = useState({});
  const [dailyTip, setDailyTip] = useState(null);
  const [countdownAlerts, setCountdownAlerts] = useState([]);
  const [limitedOffers, setLimitedOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(Date.now());

  // Enhanced data fetching with live updates
  const fetchData = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      }
      
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

      setSummary(summaryRes.data);
      setRecentTransactions(transactionsRes.data);
      setLeaderboard(leaderboardRes.data);
      setInsights(insightsRes.data);
      setGamificationProfile(gamificationRes.data);
      setDailyTip(dailyTipRes.data);
      setCountdownAlerts(countdownRes.data?.countdown_alerts || []);
      setLimitedOffers(offersRes.data || []);
      setLastUpdate(Date.now());
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh data every 30 seconds for live updates
  useEffect(() => {
    const interval = setInterval(() => {
      fetchData(false);
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchData]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      month: 'short',
      day: 'numeric'
    });
  };

  // Manual refresh handler
  const handleRefresh = () => {
    fetchData(true);
  };

  // Memoized calculations for better performance
  const savingsRate = useMemo(() => {
    if (summary.income === 0) return 0;
    return Math.round((summary.net_savings / summary.income) * 100);
  }, [summary.income, summary.net_savings]);

  const totalTransactions = useMemo(() => {
    return summary.income_count + summary.expense_count;
  }, [summary.income_count, summary.expense_count]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-8">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-32 bg-gray-200 rounded-xl"></div>
              ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
              <div className="h-96 bg-gray-200 rounded-xl"></div>
              <div className="h-96 bg-gray-200 rounded-xl"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50">
      <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-6 py-4 sm:py-8 space-y-6">
        {/* Enhanced Welcome Section - Responsive */}
        <div className="relative overflow-hidden">
        {/* Background Illustrations - Hidden on mobile */}
        <div 
          className="absolute top-0 right-0 w-1/3 h-full opacity-5 bg-cover bg-center hidden lg:block"
          style={{
            backgroundImage: "url('https://images.unsplash.com/photo-1660020619062-70b16c44bf0f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwyfHxmaW5hbmNlJTIwYXBwfGVufDB8fHxibHVlfDE3NTk0ODgwOTJ8MA&ixlib=rb-4.1.0&q=85')"
          }}
        />
        
        <div className="relative bg-gradient-to-br from-emerald-50 via-green-50 to-blue-50 rounded-xl lg:rounded-2xl p-4 sm:p-6 border border-emerald-100/60 backdrop-blur-sm">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between space-y-4 lg:space-y-0">
            <div className="flex-1 w-full">
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4 mb-4">
                <div className="relative">
                  <div className="w-10 sm:w-12 h-10 sm:h-12 bg-gradient-to-br from-emerald-500 via-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg">
                    <span className="text-white font-bold text-lg sm:text-xl">₹</span>
                  </div>
                  <div className="absolute -inset-1 bg-gradient-to-br from-emerald-400 to-green-400 rounded-xl opacity-20 blur"></div>
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <div>
                      <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold bg-gradient-to-r from-emerald-600 via-green-600 to-emerald-700 bg-clip-text text-transparent mb-1">
                        Welcome back, {user?.full_name?.split(' ')[0]}! 👋
                      </h1>
                      <p className="text-gray-600 font-medium text-sm sm:text-base">Your EarnAura financial overview</p>
                    </div>
                  </div>
                </div>
              </div>
              
              {gamificationProfile && (
                <div className="flex flex-wrap items-center gap-2 sm:gap-4 p-3 sm:p-4 bg-white/60 backdrop-blur-sm rounded-lg sm:rounded-xl border border-white/40">
                  <div className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-2 bg-yellow-50 rounded-md sm:rounded-lg border border-yellow-200">
                    <TrophyIcon className="w-4 sm:w-5 h-4 sm:h-5 text-yellow-600" />
                    <span className="text-xs sm:text-sm font-semibold text-yellow-800">
                      Level {gamificationProfile.level}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-2 bg-orange-50 rounded-md sm:rounded-lg border border-orange-200">
                    <FireIcon className="w-4 sm:w-5 h-4 sm:h-5 text-orange-600" />
                    <span className="text-xs sm:text-sm font-semibold text-orange-800">
                      {gamificationProfile.current_streak} day streak
                    </span>
                  </div>
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-3 w-full lg:w-auto">
              <Link 
                to="/transactions" 
                className="flex-1 lg:flex-initial px-4 sm:px-6 py-2 sm:py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-white rounded-lg sm:rounded-xl hover:from-emerald-600 hover:to-green-600 transition-all font-medium flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 text-sm sm:text-base"
              >
                <PlusIcon className="w-4 sm:w-5 h-4 sm:h-5" />
                Add Transaction
              </Link>
            </div>
          </div>
        </div>
        </div>

        {/* Enhanced Stats Cards - Fully Responsive */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          <div className="stat-card card-hover slide-up overflow-hidden">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="stat-label truncate">Monthly Income</p>
                <p className="stat-value text-lg sm:text-2xl lg:text-3xl break-words">{formatCurrency(summary.income)}</p>
                <p className="text-xs sm:text-sm text-emerald-600 font-medium truncate">
                  +{summary.income_count} transactions
                </p>
              </div>
              <div className="p-2 sm:p-3 bg-emerald-100 rounded-full flex-shrink-0">
                <ArrowTrendingUpIcon className="w-5 sm:w-6 h-5 sm:h-6 text-emerald-600" />
              </div>
            </div>
          </div>

          <div className="stat-card card-hover slide-up overflow-hidden" style={{ animationDelay: '0.1s' }}>
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="stat-label truncate">Monthly Expenses</p>
                <p className="stat-value text-red-500 text-lg sm:text-2xl lg:text-3xl break-words">{formatCurrency(summary.expense)}</p>
                <p className="text-xs sm:text-sm text-red-500 font-medium truncate">
                  -{summary.expense_count} transactions
                </p>
              </div>
              <div className="p-2 sm:p-3 bg-red-100 rounded-full flex-shrink-0">
                <ArrowTrendingDownIcon className="w-5 sm:w-6 h-5 sm:h-6 text-red-500" />
              </div>
            </div>
          </div>

          <div className="stat-card card-hover slide-up overflow-hidden sm:col-span-2 lg:col-span-1" style={{ animationDelay: '0.2s' }}>
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="stat-label truncate">Net Savings</p>
                <p className={`stat-value text-lg sm:text-2xl lg:text-3xl break-words ${summary.net_savings >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                  {formatCurrency(summary.net_savings)}
                </p>
                <div className="flex flex-col sm:flex-row sm:items-center sm:gap-2">
                  <p className="text-xs sm:text-sm text-gray-500 font-medium">
                    {summary.net_savings >= 0 ? 'Great progress!' : 'Need to save more'}
                  </p>
                  {savingsRate > 0 && (
                    <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full font-medium mt-1 sm:mt-0 inline-block">
                      {savingsRate}% saved
                    </span>
                  )}
                </div>
              </div>
              <div className="p-2 sm:p-3 bg-blue-100 rounded-full flex-shrink-0">
                <BanknotesIcon className="w-5 sm:w-6 h-5 sm:h-6 text-blue-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Gamification Status Widget - Responsive */}
        {gamificationProfile && (
          <div className="bg-gradient-to-r from-emerald-500 to-green-600 rounded-xl shadow-lg p-4 sm:p-6 text-white slide-up overflow-hidden">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between space-y-4 lg:space-y-0">
              <div className="w-full lg:flex-1">
                <div className="flex items-center space-x-3 mb-3">
                  <TrophyIcon className="w-6 sm:w-8 h-6 sm:h-8 text-yellow-300 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <h2 className="text-lg sm:text-xl font-bold truncate">
                      {gamificationProfile.title || 'Financial Hero'} • Level {gamificationProfile.level}
                    </h2>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-2 sm:gap-4 text-center">
                  <div>
                    <div className="text-lg sm:text-2xl font-bold">{gamificationProfile.total_badges || 0}</div>
                    <div className="text-xs sm:text-sm text-emerald-100">Badges</div>
                  </div>
                  <div>
                    <div className="text-lg sm:text-2xl font-bold flex items-center justify-center">
                      <FireIcon className="w-4 sm:w-6 h-4 sm:h-6 mr-1 text-orange-300" />
                      {gamificationProfile.current_streak || 0}
                    </div>
                    <div className="text-xs sm:text-sm text-emerald-100">Day Streak</div>
                  </div>
                </div>
              </div>
              
              <div className="w-full lg:w-auto lg:text-right">
                <Link 
                  to="/gamification" 
                  className="w-full lg:w-auto bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg transition-all flex items-center justify-center lg:justify-start space-x-2 text-sm sm:text-base"
                >
                  <span>View Progress</span>
                  <TrophyIcon className="w-4 h-4" />
                </Link>
                
                {gamificationProfile.recent_achievements?.length > 0 && (
                  <div className="mt-3 text-xs sm:text-sm">
                    <p className="text-emerald-100 mb-1">Latest Achievement:</p>
                    <div className="flex items-center justify-center lg:justify-end">
                      <span className="mr-1">{gamificationProfile.recent_achievements[0]?.icon}</span>
                      <span className="font-semibold truncate">{gamificationProfile.recent_achievements[0]?.title}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Enhanced Main Content Grid - Fully Responsive */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
          {/* Recent Transactions - Enhanced */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6 slide-up overflow-hidden" style={{ animationDelay: '0.3s' }}>
            <div className="flex items-center justify-between mb-4 sm:mb-6">
              <h2 className="text-lg sm:text-xl font-bold text-gray-900 truncate">Recent Transactions</h2>
              <Link to="/transactions" className="btn-secondary text-xs sm:text-sm whitespace-nowrap">
                View All
              </Link>
            </div>

            <div className="space-y-2 sm:space-y-3 max-h-96 overflow-y-auto">
              {recentTransactions.length > 0 ? (
                recentTransactions.map((transaction) => (
                  <div
                    key={transaction.id}
                    className={`transaction-item p-3 sm:p-4 ${
                      transaction.type === 'income' ? 'transaction-income' : 'transaction-expense'
                    }`}
                  >
                    <div className="flex items-start sm:items-center justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-gray-900 text-sm sm:text-base truncate">{transaction.description}</p>
                        <p className="text-xs sm:text-sm text-gray-500">
                          {transaction.category} • {formatDate(transaction.date)}
                        </p>
                        {transaction.is_hustle_related && (
                          <span className="inline-block mt-1 text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                            Side Hustle
                          </span>
                        )}
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className={`font-bold text-sm sm:text-base ${
                          transaction.type === 'income' ? 'text-emerald-600' : 'text-red-500'
                        }`}>
                          {transaction.type === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <BanknotesIcon className="w-10 sm:w-12 h-10 sm:h-12 mx-auto mb-3 text-gray-300" />
                  <p className="text-sm sm:text-base">No transactions yet</p>
                  <p className="text-xs sm:text-sm">Start tracking your finances!</p>
                </div>
              )}
            </div>
            
            {/* Quick Stats */}
            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <p className="text-sm font-bold text-gray-900">{totalTransactions}</p>
                  <p className="text-xs text-gray-500">Total</p>
                </div>
                <div>
                  <p className="text-sm font-bold text-emerald-600">{summary.income_count}</p>
                  <p className="text-xs text-gray-500">Income</p>
                </div>
                <div>
                  <p className="text-sm font-bold text-red-500">{summary.expense_count}</p>
                  <p className="text-xs text-gray-500">Expenses</p>
                </div>
              </div>
            </div>
          </div>

          {/* Enhanced Leaderboard & Achievements - Live Updates */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6 slide-up overflow-hidden" style={{ animationDelay: '0.4s' }}>
            <div className="flex items-center gap-2 mb-4 sm:mb-6">
              <TrophyIcon className="w-5 sm:w-6 h-5 sm:h-6 text-yellow-500" />
              <h2 className="text-lg sm:text-xl font-bold text-gray-900 truncate">Live Rankings</h2>
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">LIVE</span>
            </div>

            <div className="space-y-2 sm:space-y-3 mb-4 sm:mb-6 max-h-64 overflow-y-auto">
              {leaderboard.length > 0 ? leaderboard.slice(0, 5).map((user, index) => (
                <div key={index} className="flex items-center justify-between p-2 sm:p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                    <div className={`w-6 sm:w-8 h-6 sm:h-8 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold flex-shrink-0 ${
                      index === 0 ? 'bg-yellow-500 text-white' :
                      index === 1 ? 'bg-gray-400 text-white' :
                      index === 2 ? 'bg-orange-500 text-white' :
                      'bg-gray-200 text-gray-600'
                    }`}>
                      {index + 1}
                    </div>
                    {user.profile_photo ? (
                      <img 
                        src={`${BACKEND_URL}${user.profile_photo}`}
                        alt={user.user_name}
                        className="w-6 sm:w-8 h-6 sm:h-8 rounded-full object-cover flex-shrink-0"
                      />
                    ) : (
                      <div className="w-6 sm:w-8 h-6 sm:h-8 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
                        <span className="text-emerald-600 font-semibold text-xs sm:text-sm">
                          {user.user_name?.charAt(0) || 'U'}
                        </span>
                      </div>
                    )}
                    <p className="font-medium text-sm sm:text-base truncate">{user.user_name}</p>
                  </div>
                  <p className="font-bold text-emerald-600 text-sm sm:text-base flex-shrink-0">{formatCurrency(user.total_earnings || 0)}</p>
                </div>
              )) : (
                <div className="text-center py-4 text-gray-500">
                  <TrophyIcon className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">No rankings yet</p>
                </div>
              )}
            </div>

            {/* Enhanced User Progress Stats */}
            <div className="border-t pt-4 sm:pt-6">
              <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
                <FireIcon className="w-4 sm:w-5 h-4 sm:h-5 text-orange-500" />
                <h3 className="font-semibold text-gray-900 text-sm sm:text-base">Your Progress</h3>
                {refreshing && <div className="w-3 h-3 animate-spin rounded-full border-2 border-orange-500 border-t-transparent"></div>}
              </div>
              
              <div className="grid grid-cols-2 gap-3 sm:gap-4">
                <div className="text-center p-2 sm:p-3 bg-emerald-50 rounded-lg">
                  <p className="text-lg sm:text-2xl font-bold text-emerald-600">{insights?.income_streak || 0}</p>
                  <p className="text-xs sm:text-sm text-emerald-700">Income Streak</p>
                </div>
                <div className="text-center p-2 sm:p-3 bg-purple-50 rounded-lg">
                  <p className="text-lg sm:text-2xl font-bold text-purple-600">{gamificationProfile?.total_badges || 0}</p>
                  <p className="text-xs sm:text-sm text-purple-700">Achievements</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Real-time Alerts & Engagement Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          {/* Enhanced Daily Tips Widget */}
          {dailyTip && (
            <div className="bg-gradient-to-br from-emerald-50 to-green-100 rounded-xl border border-emerald-200 p-4 sm:p-6 slide-up overflow-hidden">
              <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
                <div className="p-1 sm:p-2 bg-emerald-500 rounded-lg flex-shrink-0">
                  <LightBulbIcon className="w-4 sm:w-6 h-4 sm:h-6 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-bold text-emerald-900 text-sm sm:text-base truncate">💡 Daily Financial Tip</h3>
                  <p className="text-xs sm:text-sm text-emerald-600">
                    {dailyTip.is_new ? 'New tip today!' : 'Today\'s tip'}
                  </p>
                </div>
              </div>
              
              <div className="bg-white/60 backdrop-blur-sm rounded-lg p-3 sm:p-4 border border-emerald-200/50">
                <div className="flex items-start gap-2 sm:gap-3">
                  <span className="text-xl sm:text-2xl flex-shrink-0">{dailyTip.tip?.icon}</span>
                  <div className="min-w-0 flex-1">
                    <h4 className="font-semibold text-blue-900 mb-2 text-sm sm:text-base">{dailyTip.tip?.title}</h4>
                    <p className="text-blue-800 text-xs sm:text-sm leading-relaxed">{dailyTip.tip?.content}</p>
                    <div className="flex items-center gap-2 mt-2 sm:mt-3 text-xs text-blue-600">
                      <SparklesIcon className="w-3 sm:w-4 h-3 sm:h-4" />
                      <span className="truncate">{dailyTip.streak_info}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Enhanced Real-time Alerts Widget */}
          <div className="bg-gradient-to-br from-orange-50 to-red-100 rounded-xl border border-orange-200 p-4 sm:p-6 slide-up overflow-hidden">
            <div className="flex items-center justify-between gap-2 sm:gap-3 mb-3 sm:mb-4">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="p-1 sm:p-2 bg-orange-500 rounded-lg flex-shrink-0">
                  <ClockIcon className="w-4 sm:w-6 h-4 sm:h-6 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-bold text-orange-900 text-sm sm:text-base truncate">⏰ Live Alerts</h3>
                  <p className="text-xs sm:text-sm text-orange-600">Real-time opportunities</p>
                </div>
              </div>
              <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full flex-shrink-0">LIVE</span>
            </div>

            <div className="space-y-2 sm:space-y-3 max-h-64 overflow-y-auto">
              {countdownAlerts && countdownAlerts.length > 0 ? (
                countdownAlerts.slice(0, 3).map((alert, index) => (
                  <div key={alert.id || index} className="bg-white/60 backdrop-blur-sm rounded-lg p-3 sm:p-4 border border-orange-200/50 hover:bg-white/80 transition-colors">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          {alert.urgency === 'critical' && <ExclamationTriangleIcon className="w-3 sm:w-4 h-3 sm:h-4 text-red-500 flex-shrink-0" />}
                          {alert.urgency === 'high' && <BoltIcon className="w-3 sm:w-4 h-3 sm:h-4 text-orange-500 flex-shrink-0" />}
                          {alert.urgency === 'medium' && <ClockIcon className="w-3 sm:w-4 h-3 sm:h-4 text-yellow-500 flex-shrink-0" />}
                          <span className="font-semibold text-xs sm:text-sm text-gray-900 truncate">{alert.title}</span>
                        </div>
                        <p className="text-xs text-gray-700 mb-2 line-clamp-2">{alert.message}</p>
                        
                        {alert.seconds_remaining && (
                          <div className="flex items-center gap-1 sm:gap-2 text-xs mb-1">
                            <ClockIcon className="w-3 h-3 text-orange-500" />
                            <span className="font-mono bg-orange-100 px-1 sm:px-2 py-0.5 rounded text-orange-800 text-xs">
                              {Math.floor(alert.seconds_remaining / 3600)}h {Math.floor((alert.seconds_remaining % 3600) / 60)}m left
                            </span>
                          </div>
                        )}
                        
                        {alert.reward && (
                          <div className="flex items-center gap-1 text-xs text-green-700">
                            <GiftIcon className="w-3 h-3" />
                            <span className="truncate">{alert.reward}</span>
                          </div>
                        )}
                      </div>
                      
                      {alert.action_url && (
                        <Link 
                          to={alert.action_url}
                          className={`px-2 sm:px-3 py-1 rounded-lg text-xs font-medium transition-all flex-shrink-0 ${
                            alert.urgency === 'critical' 
                              ? 'bg-red-500 hover:bg-red-600 text-white' 
                              : alert.urgency === 'high'
                              ? 'bg-orange-500 hover:bg-orange-600 text-white'
                              : 'bg-yellow-500 hover:bg-yellow-600 text-white'
                          }`}
                        >
                          {alert.action || 'Act'}
                        </Link>
                      )}
                    </div>
                  </div>
                ))
              ) : limitedOffers && limitedOffers.length > 0 ? (
                limitedOffers.slice(0, 2).map((offer, index) => (
                  <div key={offer.id || index} className="bg-white/60 backdrop-blur-sm rounded-lg p-3 border border-orange-200/50">
                    <div className="flex items-center gap-2 mb-2">
                      <GiftIcon className="w-4 h-4 text-purple-500" />
                      <span className="font-semibold text-sm text-gray-900 truncate">{offer.title}</span>
                    </div>
                    <p className="text-xs text-gray-700 mb-2">{offer.description}</p>
                    {offer.expires_at && (
                      <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                        Limited Time
                      </span>
                    )}
                  </div>
                ))
              ) : (
                <div className="bg-white/60 backdrop-blur-sm rounded-lg p-3 sm:p-4 border border-orange-200/50 text-center">
                  <ClockIcon className="w-6 sm:w-8 h-6 sm:h-8 mx-auto mb-2 text-orange-300" />
                  <p className="text-xs sm:text-sm text-orange-600">No urgent alerts right now</p>
                  <p className="text-xs text-orange-500">Keep tracking for opportunities!</p>
                </div>
              )}
            </div>

            {(countdownAlerts?.length > 3 || limitedOffers?.length > 2) && (
              <div className="mt-3 text-center">
                <button 
                  onClick={() => window.location.reload()}
                  className="text-xs text-orange-600 hover:text-orange-700 font-medium"
                >
                  Refresh for more alerts
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Enhanced Engagement Features Section - Real-time Updates */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
          {/* Enhanced Daily Tips with Live Data */}
          <div>
            <DailyTips 
              userId={user?.id} 
              onUpdate={() => fetchData(false)}
              lastUpdate={lastUpdate}
            />
          </div>

          {/* Enhanced Limited Offers with Real-time Updates */}
          <div>
            <LimitedOffers 
              userId={user?.id}
              refreshData={fetchData}
              liveOffers={limitedOffers}
              isRefreshing={refreshing}
            />
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
