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
  FireIcon
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [summaryRes, transactionsRes, leaderboardRes] = await Promise.all([
          axios.get(`${API}/transactions/summary`),
          axios.get(`${API}/transactions?limit=5`),
          axios.get(`${API}/analytics/leaderboard`)
        ]);

        setSummary(summaryRes.data);
        setRecentTransactions(transactionsRes.data);
        setLeaderboard(leaderboardRes.data);
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
      {/* Welcome Section */}
      <div className="mb-8 fade-in">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome back, {user?.full_name?.split(' ')[0]}! 👋
        </h1>
        <p className="text-gray-600">Here's your financial overview for this month</p>
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
                <p className="text-2xl font-bold text-emerald-600">{user?.current_streak || 0}</p>
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
    </div>
  );
};

export default Dashboard;