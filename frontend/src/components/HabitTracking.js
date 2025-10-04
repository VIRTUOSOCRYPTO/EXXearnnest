import React, { useState, useEffect } from 'react';
import axios from 'axios';

const HabitTracking = () => {
  const [habitData, setHabitData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHabitData();
  }, []);

  const fetchHabitData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/retention/habit-tracking`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setHabitData(response.data);
    } catch (error) {
      console.error('Habit tracking error:', error);
      setError('Failed to load habit tracking data');
    } finally {
      setLoading(false);
    }
  };

  const getHabitProgressColor = (progress) => {
    if (progress >= 80) return 'bg-green-500';
    if (progress >= 60) return 'bg-blue-500';
    if (progress >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getStreakColor = (streak) => {
    if (streak >= 15) return 'text-purple-600';
    if (streak >= 7) return 'text-blue-600';
    if (streak >= 3) return 'text-green-600';
    return 'text-orange-600';
  };

  const getRankingColor = (ranking, total) => {
    const percentile = (ranking / total) * 100;
    if (percentile <= 25) return 'text-green-600'; // Top 25%
    if (percentile <= 50) return 'text-blue-600';  // Top 50%
    if (percentile <= 75) return 'text-yellow-600'; // Top 75%
    return 'text-red-600'; // Bottom 25%
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-4">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-gray-200 h-48 rounded-lg"></div>
            ))}
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

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Habit Tracking</h1>
        <p className="text-gray-600">Build consistent financial habits with social accountability</p>
      </div>

      {/* Monthly Summary Card */}
      <div className="bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">This Month's Progress</h2>
          <div className="text-2xl font-bold">
            {habitData.user_habit_score}/{habitData.monthly_summary.month_target}
          </div>
        </div>
        
        <div className="w-full bg-white bg-opacity-20 rounded-full h-3 mb-4">
          <div
            className="bg-white h-3 rounded-full transition-all duration-500"
            style={{ width: `${habitData.monthly_summary.progress}%` }}
          ></div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold">{habitData.monthly_summary.check_in_days}</div>
            <div className="text-sm opacity-80">Check-in Days</div>
          </div>
          <div>
            <div className="text-2xl font-bold">{habitData.monthly_summary.transaction_days}</div>
            <div className="text-sm opacity-80">Active Days</div>
          </div>
          <div>
            <div className="text-2xl font-bold">{habitData.monthly_summary.budget_awareness_days}</div>
            <div className="text-sm opacity-80">Budget Mindful</div>
          </div>
          <div>
            <div className="text-2xl font-bold">
              {habitData.social_comparison.user_ranking}/{habitData.social_comparison.total_participants}
            </div>
            <div className="text-sm opacity-80">Friend Ranking</div>
          </div>
        </div>
      </div>

      {/* Social Pressure Messages */}
      {habitData.social_pressure_messages.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">Social Challenges</h3>
          {habitData.social_pressure_messages.map((message, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border-l-4 ${
                message.urgency === 'high' ? 'bg-red-50 border-red-500' :
                message.urgency === 'medium' ? 'bg-yellow-50 border-yellow-500' :
                'bg-blue-50 border-blue-500'
              }`}
            >
              <p className="font-semibold text-gray-900">{message.message}</p>
              <p className="text-sm text-gray-600 mt-1">{message.action}</p>
            </div>
          ))}
        </div>
      )}

      {/* Individual Habits */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Financial Habits</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {habitData.habits.map((habit, index) => (
            <div key={index} className="bg-white rounded-lg shadow-lg p-6 border">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">{habit.icon}</span>
                  <h4 className="font-semibold text-gray-900">{habit.name}</h4>
                </div>
                {habit.social_ranking !== "N/A" && (
                  <div className={`text-sm font-bold ${getRankingColor(habit.social_ranking, habit.total_friends)}`}>
                    #{habit.social_ranking}
                  </div>
                )}
              </div>

              <p className="text-gray-600 text-sm mb-4">{habit.description}</p>

              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1">
                  <span>Progress</span>
                  <span>{habit.progress.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${getHabitProgressColor(habit.progress)}`}
                    style={{ width: `${habit.progress}%` }}
                  ></div>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <div className={`text-xl font-bold ${getStreakColor(habit.current_streak)}`}>
                    {habit.current_streak}
                  </div>
                  <div className="text-xs text-gray-500">Current Streak</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-gray-900">
                    {habit.days_this_month}/{habit.target_days}
                  </div>
                  <div className="text-xs text-gray-500">This Month</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Friends Leaderboard */}
      {habitData.social_comparison.friends_performance.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Friends Leaderboard</h3>
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b">
              <h4 className="font-semibold text-gray-900">Top Performers This Month</h4>
            </div>
            <div className="divide-y divide-gray-200">
              {habitData.social_comparison.friends_performance.map((friend, index) => (
                <div key={friend.friend_id} className="px-6 py-4 flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      index === 0 ? 'bg-yellow-100 text-yellow-800' :
                      index === 1 ? 'bg-gray-100 text-gray-800' :
                      index === 2 ? 'bg-orange-100 text-orange-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {index + 1}
                    </div>
                    <div className="ml-4">
                      <div className="font-semibold text-gray-900">{friend.name}</div>
                      <div className="text-sm text-gray-500">
                        {friend.checkin_days} check-ins • {friend.transaction_days} active days
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-900">{friend.total_habit_score}</div>
                    <div className="text-xs text-gray-500">Total Score</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HabitTracking;
