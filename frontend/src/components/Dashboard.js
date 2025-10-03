import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { useAuth, formatCurrency } from '../App';
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
  GiftIcon
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        const headers = { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        };

        const [summaryRes, transactionsRes, leaderboardRes, insightsRes, gamificationRes, dailyTipRes, countdownRes] = await Promise.all([
          axios.get(`${API}/transactions/summary`, { headers }),
          axios.get(`${API}/transactions?limit=5`, { headers }),
          axios.get(`${API}/analytics/leaderboard`, { headers }),
          axios.get(`${API}/analytics/insights`, { headers }),
          axios.get(`${API}/gamification/profile`, { headers }).catch(() => ({ data: null })),
          axios.get(`${API}/engagement/daily-tip`, { headers }).catch(() => ({ data: null })),
          axios.get(`${API}/engagement/countdown-alerts`, { headers }).catch(() => ({ data: [] }))
        ]);

        setSummary(summaryRes.data);
        setRecentTransactions(transactionsRes.data);
        setLeaderboard(leaderboardRes.data);
        setInsights(insightsRes.data);
        setGamificationProfile(gamificationRes.data);
        setDailyTip(dailyTipRes.data);
        setCountdownAlerts(countdownRes.data || []);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-gray-200 rounded-xl"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="h-96 bg-gray-200 rounded-xl"></div>
            <div className="h-96 bg-gray-200 rounded-xl"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Enhanced Welcome Section with Visual Polish */}
      <div className="mb-8 relative overflow-hidden">
        {/* Background Illustrations */}
        <div 
          className="absolute top-0 right-0 w-1/3 h-full opacity-5 bg-cover bg-center"
          style={{
            backgroundImage: "url('https://images.unsplash.com/photo-1660020619062-70b16c44bf0f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwyfHxmaW5hbmNlJTIwYXBwfGVufDB8fHxibHVlfDE3NTk0ODgwOTJ8MA&ixlib=rb-4.1.0&q=85')"
          }}
        />
        
        <div className="relative bg-gradient-to-br from-emerald-50 via-green-50 to-blue-50 rounded-2xl p-6 border border-emerald-100/60 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-4 mb-4">
                <div className="relative">
                  <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 via-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg">
                    <span className="text-white font-bold text-xl">₹</span>
                  </div>
                  <div className="absolute -inset-1 bg-gradient-to-br from-emerald-400 to-green-400 rounded-xl opacity-20 blur"></div>
                </div>
                <div>
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-600 via-green-600 to-emerald-700 bg-clip-text text-transparent mb-1">
                    Welcome back, {user?.full_name?.split(' ')[0]}! 👋
                  </h1>
                  <p className="text-gray-600 font-medium">Your EarnAura financial overview</p>
                </div>
              </div>
              
              {gamificationProfile && (
                <div className="flex flex-wrap items-center gap-4 p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-white/40">
                  <div className="flex items-center gap-2 px-3 py-2 bg-yellow-50 rounded-lg border border-yellow-200">
                    <TrophyIcon className="w-5 h-5 text-yellow-600" />
                    <span className="text-sm font-semibold text-yellow-800">
                      Level {gamificationProfile.level}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-2 bg-orange-50 rounded-lg border border-orange-200">
                    <FireIcon className="w-5 h-5 text-orange-600" />
                    <span className="text-sm font-semibold text-orange-800">
                      {gamificationProfile.current_streak} day streak
                    </span>
                  </div>
                  <div className="px-3 py-2 bg-emerald-50 rounded-lg border border-emerald-200">
                    <span className="text-sm font-semibold text-emerald-800">
                      {gamificationProfile.experience_points} XP
                    </span>
                  </div>
                </div>
              )}
            </div>
            
            <div className="hidden lg:flex items-center gap-3">
              <Link 
                to="/transactions" 
                className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-white rounded-xl hover:from-emerald-600 hover:to-green-600 transition-all font-medium flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                <PlusIcon className="w-5 h-5" />
                Add Transaction
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="stat-card card-hover slide-up">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Monthly Income</p>
              <p className="stat-value">{formatCurrency(summary.income)}</p>
              <p className="text-sm text-emerald-600 font-medium">
                +{summary.income_count} transactions
              </p>
            </div>
            <div className="p-3 bg-emerald-100 rounded-full">
              <ArrowTrendingUpIcon className="w-6 h-6 text-emerald-600" />
            </div>
          </div>
        </div>

        <div className="stat-card card-hover slide-up" style={{ animationDelay: '0.1s' }}>
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Monthly Expenses</p>
              <p className="stat-value text-red-500">{formatCurrency(summary.expense)}</p>
              <p className="text-sm text-red-500 font-medium">
                -{summary.expense_count} transactions
              </p>
            </div>
            <div className="p-3 bg-red-100 rounded-full">
              <ArrowTrendingDownIcon className="w-6 h-6 text-red-500" />
            </div>
          </div>
        </div>

        <div className="stat-card card-hover slide-up" style={{ animationDelay: '0.2s' }}>
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Net Savings</p>
              <p className={`stat-value ${summary.net_savings >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                {formatCurrency(summary.net_savings)}
              </p>
              <p className="text-sm text-gray-500 font-medium">
                {summary.net_savings >= 0 ? 'Great progress!' : 'Need to save more'}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <BanknotesIcon className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Gamification Status Widget */}
      {gamificationProfile && (
        <div className="bg-gradient-to-r from-emerald-500 to-green-600 rounded-xl shadow-lg p-6 mb-8 text-white slide-up">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-3 mb-3">
                <TrophyIcon className="w-8 h-8 text-yellow-300" />
                <div>
                  <h2 className="text-xl font-bold">{gamificationProfile.title} • Level {gamificationProfile.level}</h2>
                  <p className="text-emerald-100">{gamificationProfile.experience_points} XP</p>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold">{gamificationProfile.total_badges}</div>
                  <div className="text-sm text-emerald-100">Badges</div>
                </div>
                <div>
                  <div className="text-2xl font-bold flex items-center justify-center">
                    <FireIcon className="w-6 h-6 mr-1 text-orange-300" />
                    {gamificationProfile.current_streak}
                  </div>
                  <div className="text-sm text-emerald-100">Day Streak</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">
                    #{gamificationProfile.ranks?.savings || '--'}
                  </div>
                  <div className="text-sm text-emerald-100">Savings Rank</div>
                </div>
              </div>
            </div>
            
            <div className="text-right">
              <Link 
                to="/gamification" 
                className="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg transition-all flex items-center space-x-2"
              >
                <span>View Progress</span>
                <TrophyIcon className="w-4 h-4" />
              </Link>
              
              {gamificationProfile.recent_achievements?.length > 0 && (
                <div className="mt-3 text-sm">
                  <p className="text-emerald-100 mb-1">Latest Achievement:</p>
                  <div className="flex items-center">
                    <span className="mr-1">{gamificationProfile.recent_achievements[0]?.icon}</span>
                    <span className="font-semibold">{gamificationProfile.recent_achievements[0]?.title}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Transactions */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 slide-up" style={{ animationDelay: '0.3s' }}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">Recent Transactions</h2>
            <Link to="/transactions" className="btn-secondary text-sm">
              View All
            </Link>
          </div>

          <div className="space-y-3">
            {recentTransactions.length > 0 ? (
              recentTransactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className={`transaction-item ${
                    transaction.type === 'income' ? 'transaction-income' : 'transaction-expense'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-gray-900">{transaction.description}</p>
                      <p className="text-sm text-gray-500">
                        {transaction.category} • {formatDate(transaction.date)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`font-bold ${
                        transaction.type === 'income' ? 'text-emerald-600' : 'text-red-500'
                      }`}>
                        {transaction.type === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
                      </p>
                      {transaction.is_hustle_related && (
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                          Side Hustle
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <BanknotesIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No transactions yet</p>
                <p className="text-sm">Start tracking your finances!</p>
              </div>
            )}
          </div>
        </div>

        {/* Leaderboard & Achievements */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 slide-up" style={{ animationDelay: '0.4s' }}>
          <div className="flex items-center gap-2 mb-6">
            <TrophyIcon className="w-6 h-6 text-yellow-500" />
            <h2 className="text-xl font-bold text-gray-900">Top Earners This Month</h2>
          </div>

          <div className="space-y-3 mb-6">
            {leaderboard.slice(0, 5).map((user, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
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
                      className="w-8 h-8 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center">
                      <span className="text-emerald-600 font-semibold text-sm">
                        {user.user_name.charAt(0)}
                      </span>
                    </div>
                  )}
                  <p className="font-medium">{user.user_name}</p>
                </div>
                <p className="font-bold text-emerald-600">{formatCurrency(user.total_earnings)}</p>
              </div>
            ))}
          </div>

          {/* User Stats */}
          <div className="border-t pt-6">
            <div className="flex items-center gap-3 mb-4">
              <FireIcon className="w-5 h-5 text-orange-500" />
              <h3 className="font-semibold text-gray-900">Your Progress</h3>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-emerald-50 rounded-lg">
                <p className="text-2xl font-bold text-emerald-600">{insights?.income_streak || 0}</p>
                <p className="text-sm text-emerald-700">Income Streak</p>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">{user?.achievements?.length || 0}</p>
                <p className="text-sm text-purple-700">Achievements</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Daily Tips & Countdown Alerts Section - Bottom Placement */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        {/* Daily Tips Widget */}
        {dailyTip && (
          <div className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl border border-blue-200 p-6 slide-up">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-blue-500 rounded-lg">
                <LightBulbIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-blue-900">💡 Daily Financial Tip</h3>
                <p className="text-sm text-blue-600">
                  {dailyTip.is_new ? 'New tip today!' : 'Today\'s tip'}
                </p>
              </div>
            </div>
            
            <div className="bg-white/60 backdrop-blur-sm rounded-lg p-4 border border-blue-200/50">
              <div className="flex items-start gap-3">
                <span className="text-2xl">{dailyTip.tip.icon}</span>
                <div>
                  <h4 className="font-semibold text-blue-900 mb-2">{dailyTip.tip.title}</h4>
                  <p className="text-blue-800 text-sm leading-relaxed">{dailyTip.tip.content}</p>
                  <div className="flex items-center gap-2 mt-3 text-xs text-blue-600">
                    <SparklesIcon className="w-4 h-4" />
                    <span>{dailyTip.streak_info}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Countdown Alerts Widget */}
        <div className="bg-gradient-to-br from-orange-50 to-red-100 rounded-xl border border-orange-200 p-6 slide-up">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-orange-500 rounded-lg">
              <ClockIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-orange-900">⏰ Active Alerts</h3>
              <p className="text-sm text-orange-600">Time-sensitive opportunities</p>
            </div>
          </div>

          <div className="space-y-3">
            {countdownAlerts && countdownAlerts.length > 0 ? (
              countdownAlerts.slice(0, 2).map((alert) => (
                <div key={alert.id} className="bg-white/60 backdrop-blur-sm rounded-lg p-4 border border-orange-200/50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {alert.urgency === 'critical' && <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />}
                        {alert.urgency === 'high' && <BoltIcon className="w-4 h-4 text-orange-500" />}
                        {alert.urgency === 'medium' && <ClockIcon className="w-4 h-4 text-yellow-500" />}
                        <span className="font-semibold text-sm text-gray-900">{alert.title}</span>
                      </div>
                      <p className="text-xs text-gray-700 mb-2">{alert.message}</p>
                      
                      {alert.seconds_remaining && (
                        <div className="flex items-center gap-2 text-xs">
                          <ClockIcon className="w-3 h-3 text-orange-500" />
                          <span className="font-mono bg-orange-100 px-2 py-0.5 rounded text-orange-800">
                            {Math.floor(alert.seconds_remaining / 3600)}h {Math.floor((alert.seconds_remaining % 3600) / 60)}m left
                          </span>
                        </div>
                      )}
                      
                      {alert.reward && (
                        <div className="flex items-center gap-1 mt-1 text-xs text-green-700">
                          <GiftIcon className="w-3 h-3" />
                          <span>{alert.reward}</span>
                        </div>
                      )}
                    </div>
                    
                    {alert.action_url && (
                      <Link 
                        to={alert.action_url}
                        className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                          alert.urgency === 'critical' 
                            ? 'bg-red-500 hover:bg-red-600 text-white' 
                            : alert.urgency === 'high'
                            ? 'bg-orange-500 hover:bg-orange-600 text-white'
                            : 'bg-yellow-500 hover:bg-yellow-600 text-white'
                        }`}
                      >
                        {alert.action}
                      </Link>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-white/60 backdrop-blur-sm rounded-lg p-4 border border-orange-200/50 text-center">
                <ClockIcon className="w-8 h-8 mx-auto mb-2 text-orange-300" />
                <p className="text-sm text-orange-600">No urgent alerts right now</p>
                <p className="text-xs text-orange-500">Keep checking for opportunities!</p>
              </div>
            )}
          </div>

          {countdownAlerts && countdownAlerts.length > 2 && (
            <div className="mt-3 text-center">
              <button className="text-xs text-orange-600 hover:text-orange-700 font-medium">
                View {countdownAlerts.length - 2} more alerts
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
