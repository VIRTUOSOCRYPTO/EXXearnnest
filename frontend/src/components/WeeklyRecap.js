import React, { useState, useEffect } from 'react';
import axios from 'axios';

const WeeklyRecap = () => {
  const [recapData, setRecapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchWeeklyRecap();
  }, []);

  const fetchWeeklyRecap = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/retention/weekly-recap`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setRecapData(response.data);
    } catch (error) {
      console.error('Weekly recap error:', error);
      setError('Failed to load weekly recap');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      month: 'short',
      day: 'numeric'
    });
  };

  const getRankingBadge = (rank, total) => {
    const percentile = (rank / total) * 100;
    if (percentile <= 20) return { color: 'bg-yellow-100 text-yellow-800', icon: '🏆', text: 'Top 20%' };
    if (percentile <= 40) return { color: 'bg-green-100 text-green-800', icon: '🥈', text: 'Top 40%' };
    if (percentile <= 60) return { color: 'bg-blue-100 text-blue-800', icon: '🥉', text: 'Top 60%' };
    return { color: 'bg-gray-100 text-gray-800', icon: '📊', text: `${rank}/${total}` };
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-4">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="bg-gray-200 h-64 rounded-lg"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-200 h-48 rounded-lg"></div>
            <div className="bg-gray-200 h-48 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto p-4">
        <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  const savingsBadge = getRankingBadge(recapData.social_comparison.rankings.savings_rank, recapData.social_comparison.rankings.total_participants);
  const activityBadge = getRankingBadge(recapData.social_comparison.rankings.activity_rank, recapData.social_comparison.rankings.total_participants);

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Weekly Recap</h1>
        <p className="text-gray-600">
          Week {recapData.week_period.week_number} • {formatDate(recapData.week_period.start)} - {formatDate(recapData.week_period.end)}
        </p>
      </div>

      {/* Main Stats Card */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg shadow-lg overflow-hidden">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6">Your Week in Numbers</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold">{formatCurrency(recapData.user_stats.savings)}</div>
              <div className="text-sm opacity-80">Net Savings</div>
              <div className={`inline-block mt-2 px-2 py-1 rounded text-xs ${savingsBadge.color}`}>
                {savingsBadge.icon} {savingsBadge.text}
              </div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">{formatCurrency(recapData.user_stats.income)}</div>
              <div className="text-sm opacity-80">Total Income</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">{formatCurrency(recapData.user_stats.expenses)}</div>
              <div className="text-sm opacity-80">Total Expenses</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">{recapData.user_stats.checkins}</div>
              <div className="text-sm opacity-80">Check-ins</div>
              <div className={`inline-block mt-2 px-2 py-1 rounded text-xs ${activityBadge.color}`}>
                {activityBadge.icon} {activityBadge.text}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Achievements */}
      {recapData.achievements.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">🏆 Weekly Achievements</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recapData.achievements.map((achievement, index) => (
              <div key={index} className="flex items-center p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border-l-4 border-green-500">
                <span className="text-3xl mr-4">{achievement.icon}</span>
                <div>
                  <h4 className="font-semibold text-gray-900">{achievement.title}</h4>
                  <p className="text-sm text-gray-600">{achievement.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Social Comparison */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">👥 Friend Comparison</h3>
          
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-2">Your Performance vs Friends</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Your Savings:</span>
                  <span className="font-semibold">{formatCurrency(recapData.user_stats.savings)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Friends Average:</span>
                  <span className="font-semibold">{formatCurrency(recapData.social_comparison.friend_averages.savings)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Your Check-ins:</span>
                  <span className="font-semibold">{recapData.user_stats.checkins}/7</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Friends Average:</span>
                  <span className="font-semibold">{recapData.social_comparison.friend_averages.checkins.toFixed(1)}/7</span>
                </div>
              </div>
            </div>

            {/* Rankings */}
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  #{recapData.social_comparison.rankings.savings_rank}
                </div>
                <div className="text-sm text-gray-600">Savings Rank</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  #{recapData.social_comparison.rankings.activity_rank}
                </div>
                <div className="text-sm text-gray-600">Activity Rank</div>
              </div>
            </div>
          </div>

          {/* Top Performers */}
          {recapData.social_comparison.top_performers.savings.length > 0 && (
            <div className="mt-6">
              <h4 className="font-semibold text-gray-900 mb-3">🥇 Top Savers This Week</h4>
              <div className="space-y-2">
                {recapData.social_comparison.top_performers.savings.slice(0, 3).map((friend, index) => (
                  <div key={friend.friend_id} className="flex items-center justify-between p-3 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg">
                    <div className="flex items-center">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mr-3 ${
                        index === 0 ? 'bg-yellow-500 text-white' :
                        index === 1 ? 'bg-gray-400 text-white' :
                        'bg-orange-400 text-white'
                      }`}>
                        {index + 1}
                      </div>
                      <span className="font-medium">{friend.name}</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-700">
                      {formatCurrency(friend.savings)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Insights & Next Week Goals */}
        <div className="space-y-6">
          {/* Insights */}
          {recapData.insights.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">💡 Insights</h3>
              <div className="space-y-3">
                {recapData.insights.map((insight, index) => (
                  <div key={index} className={`p-4 rounded-lg ${
                    insight.type === 'positive' ? 'bg-green-50 border-l-4 border-green-500' :
                    'bg-blue-50 border-l-4 border-blue-500'
                  }`}>
                    <div className="flex items-center">
                      <span className="text-xl mr-3">{insight.icon}</span>
                      <p className="text-sm text-gray-700">{insight.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Next Week Goals */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">🎯 Next Week Goals</h3>
            <div className="space-y-4">
              {recapData.next_week_goals.map((goal, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-900">{goal.title}</h4>
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                      +{goal.reward_points} pts
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{goal.description}</p>
                  {goal.type === 'savings' && (
                    <div className="text-sm text-gray-500">
                      Target: {formatCurrency(goal.target)}
                    </div>
                  )}
                  {goal.type === 'consistency' && (
                    <div className="text-sm text-gray-500">
                      Target: {goal.target} days
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeeklyRecap;
