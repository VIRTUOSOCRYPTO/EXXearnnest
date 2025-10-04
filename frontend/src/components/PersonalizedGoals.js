import React, { useState, useEffect } from 'react';
import axios from 'axios';

const PersonalizedGoals = () => {
  const [goalsData, setGoalsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPersonalizedGoals();
  }, []);

  const fetchPersonalizedGoals = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/retention/personalized-goals`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setGoalsData(response.data);
    } catch (error) {
      console.error('Personalized goals error:', error);
      setError('Failed to load personalized goals');
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
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getGoalTypeColor = (type) => {
    const colors = {
      'savings_catch_up': 'bg-blue-100 border-blue-300 text-blue-700',
      'excellence_goal': 'bg-purple-100 border-purple-300 text-purple-700',
      'activity_boost': 'bg-green-100 border-green-300 text-green-700',
      'income_growth': 'bg-yellow-100 border-yellow-300 text-yellow-700',
    };
    return colors[type] || 'bg-gray-100 border-gray-300 text-gray-700';
  };

  const getGoalIcon = (type) => {
    const icons = {
      'savings_catch_up': '🎯',
      'excellence_goal': '👑',
      'activity_boost': '📈',
      'income_growth': '💰',
    };
    return icons[type] || '🎯';
  };

  const getPercentileColor = (percentile) => {
    if (percentile >= 75) return 'text-green-600 bg-green-100';
    if (percentile >= 50) return 'text-blue-600 bg-blue-100';
    if (percentile >= 25) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-4">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="bg-gray-200 h-48 rounded-lg"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-200 h-64 rounded-lg"></div>
            <div className="bg-gray-200 h-64 rounded-lg"></div>
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Personalized Goals</h1>
        <p className="text-gray-600">AI-powered goals based on your peer performance at {goalsData.peer_benchmarks.university}</p>
      </div>

      {/* Performance Overview */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg shadow-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 className="text-xl font-bold mb-4">Your Performance vs Campus Peers</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="opacity-80">Your Savings:</span>
                <span className="font-bold">{formatCurrency(goalsData.user_performance.savings)}</span>
              </div>
              <div className="flex justify-between">
                <span className="opacity-80">Campus Average:</span>
                <span className="font-bold">{formatCurrency(goalsData.peer_benchmarks.avg_savings)}</span>
              </div>
              <div className="flex justify-between">
                <span className="opacity-80">Monthly Income:</span>
                <span className="font-bold">{formatCurrency(goalsData.user_performance.monthly_income)}</span>
              </div>
              <div className="flex justify-between">
                <span className="opacity-80">Peer Average:</span>
                <span className="font-bold">{formatCurrency(goalsData.peer_benchmarks.avg_monthly_income)}</span>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-4">Your Campus Rankings</h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className={`text-2xl font-bold p-3 rounded-lg ${getPercentileColor(goalsData.percentiles.savings)}`}>
                  {goalsData.percentiles.savings}%
                </div>
                <div className="text-sm opacity-80 mt-1">Savings</div>
              </div>
              <div>
                <div className={`text-2xl font-bold p-3 rounded-lg ${getPercentileColor(goalsData.percentiles.income)}`}>
                  {goalsData.percentiles.income}%
                </div>
                <div className="text-sm opacity-80 mt-1">Income</div>
              </div>
              <div>
                <div className={`text-2xl font-bold p-3 rounded-lg ${getPercentileColor(goalsData.percentiles.activity)}`}>
                  {goalsData.percentiles.activity}%
                </div>
                <div className="text-sm opacity-80 mt-1">Activity</div>
              </div>
            </div>
            
            <div className="mt-4 p-3 bg-white bg-opacity-20 rounded-lg">
              <div className="text-sm font-medium">{goalsData.overall_ranking}</div>
              <div className="text-xs opacity-80">
                Based on {goalsData.peer_benchmarks.peer_count} peers at {goalsData.peer_benchmarks.university}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Personalized Goals */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">🎯 Your Personalized Goals</h2>
        
        {goalsData.personalized_goals.length === 0 ? (
          <div className="bg-green-100 border border-green-300 text-green-700 px-6 py-4 rounded-lg text-center">
            <div className="text-4xl mb-2">🎉</div>
            <h3 className="text-lg font-semibold">You're doing amazing!</h3>
            <p>You're already performing exceptionally well compared to your peers. Keep up the great work!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {goalsData.personalized_goals.map((goal, index) => (
              <div key={index} className={`rounded-lg border-2 p-6 ${getGoalTypeColor(goal.type)}`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start space-x-3">
                    <span className="text-3xl">{getGoalIcon(goal.type)}</span>
                    <div>
                      <h3 className="text-lg font-bold">{goal.title}</h3>
                      <p className="text-sm opacity-80">{goal.description}</p>
                    </div>
                  </div>
                  <div className="bg-white bg-opacity-50 px-3 py-1 rounded-full text-sm font-semibold">
                    +{goal.reward_points} pts
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span>Progress</span>
                    <span>{goal.progress.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-white bg-opacity-30 rounded-full h-3">
                    <div
                      className="bg-white h-3 rounded-full transition-all duration-500"
                      style={{ width: `${goal.progress}%` }}
                    ></div>
                  </div>
                </div>

                {/* Goal Details */}
                <div className="space-y-3">
                  <div className="bg-white bg-opacity-20 rounded-lg p-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="opacity-80">Current:</span>
                        <div className="font-semibold">
                          {goal.type.includes('savings') || goal.type.includes('income') 
                            ? formatCurrency(goal.current_amount)
                            : goal.current_amount
                          }
                        </div>
                      </div>
                      <div>
                        <span className="opacity-80">Target:</span>
                        <div className="font-semibold">
                          {goal.type.includes('savings') || goal.type.includes('income')
                            ? formatCurrency(goal.target_amount)
                            : goal.target_amount
                          }
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="text-sm">
                    <div className="font-medium mb-1">{goal.motivation}</div>
                    <div className="opacity-80">{goal.peer_context}</div>
                  </div>

                  <div className="flex justify-between items-center text-xs">
                    <span className="opacity-80">Deadline: {formatDate(goal.deadline)}</span>
                    <span className={`px-2 py-1 rounded-full font-medium ${
                      goal.category === 'peer_comparison' ? 'bg-blue-200 text-blue-800' :
                      goal.category === 'excellence' ? 'bg-purple-200 text-purple-800' :
                      goal.category === 'activity' ? 'bg-green-200 text-green-800' :
                      'bg-yellow-200 text-yellow-800'
                    }`}>
                      {goal.category.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Peer Benchmark Details */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Campus Benchmarks</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(goalsData.peer_benchmarks.avg_savings)}
            </div>
            <div className="text-sm text-blue-800">Average Savings</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(goalsData.peer_benchmarks.avg_monthly_income)}
            </div>
            <div className="text-sm text-green-800">Average Income</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {goalsData.peer_benchmarks.avg_transactions.toFixed(0)}
            </div>
            <div className="text-sm text-purple-800">Average Transactions</div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {goalsData.peer_benchmarks.peer_count}
            </div>
            <div className="text-sm text-orange-800">Total Peers</div>
          </div>
        </div>
        
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 text-center">
            Goals are dynamically generated based on real peer performance data at {goalsData.peer_benchmarks.university}.
            Complete these goals to earn points and climb the campus leaderboard!
          </p>
        </div>
      </div>
    </div>
  );
};

export default PersonalizedGoals;
