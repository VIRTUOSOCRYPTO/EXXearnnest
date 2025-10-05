import React, { useState, useEffect } from 'react';
import { PieChart, BarChart3, Share, TrendingUp, Users } from 'lucide-react';

const SpendingInsights = ({ userCampus }) => {
  const [insights, setInsights] = useState([]);
  const [campusData, setCampusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [shareableText, setShareableText] = useState('');

  useEffect(() => {
    if (userCampus) {
      fetchSpendingInsights();
    }
  }, [userCampus]);

  const fetchSpendingInsights = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/insights/campus-spending/${encodeURIComponent(userCampus)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        setInsights(data.insights || []);
        setCampusData({
          campus: data.campus,
          totalUsers: data.total_users,
          totalSpending: data.total_spending,
          period: data.period
        });
        setShareableText(data.shareable_text || '');
      }
    } catch (error) {
      console.error('Error fetching spending insights:', error);
    } finally {
      setLoading(false);
    }
  };

  const shareInsight = async (insight) => {
    const text = insight ? 
      `${insight.insight_text} ${insight.emoji} #EarnAura #StudentFinance` : 
      shareableText;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Campus Spending Insights',
          text: text,
          url: window.location.href
        });
      } catch (error) {
        console.log('Error sharing:', error);
        fallbackShare(text);
      }
    } else {
      fallbackShare(text);
    }
  };

  const fallbackShare = (text) => {
    navigator.clipboard.writeText(text);
    alert('Insight copied to clipboard! Share it on your favorite platform.');
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Food': 'from-orange-500 to-red-500',
      'Entertainment': 'from-purple-500 to-pink-500',
      'Shopping': 'from-blue-500 to-indigo-500',
      'Transportation': 'from-green-500 to-teal-500',
      'Books': 'from-yellow-500 to-orange-500'
    };
    return colors[category] || 'from-gray-500 to-gray-700';
  };

  const formatAmount = (amount) => {
    if (amount >= 100000) {
      return `₹${(amount / 100000).toFixed(1)}L`;
    } else if (amount >= 1000) {
      return `₹${(amount / 1000).toFixed(1)}K`;
    }
    return `₹${amount.toLocaleString()}`;
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-300 rounded w-1/2 mb-6"></div>
          <div className="grid gap-4">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="h-24 bg-gray-300 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!insights.length) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-8">
          <PieChart className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No Spending Data Yet</h3>
          <p className="text-gray-600">
            Your campus needs more expense tracking data to generate insights. 
            Start recording expenses to see how your campus spends!
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-blue-600" />
            Campus Spending Insights
          </h2>
          <button
            onClick={() => shareInsight()}
            className="bg-gradient-to-r from-green-500 to-blue-500 text-white px-6 py-2 rounded-full font-medium hover:shadow-lg transition-all duration-300 flex items-center gap-2"
          >
            <Share className="w-4 h-4" />
            Share Campus Stats
          </button>
        </div>
        
        {campusData && (
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl p-6">
            <h3 className="text-2xl font-bold mb-2">{campusData.campus}</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                <span>{campusData.totalUsers} active students</span>
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                <span>{formatAmount(campusData.totalSpending)} total spending</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-indigo-200">{campusData.period}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Spending Insights */}
      <div className="grid gap-6">
        {insights.map((insight, index) => (
          <div
            key={insight.category}
            className={`relative overflow-hidden rounded-xl bg-gradient-to-r ${getCategoryColor(insight.category)} p-6 text-white shadow-xl transform hover:scale-105 transition-all duration-300`}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-3xl">{insight.emoji}</span>
                  <h3 className="text-2xl font-bold">{insight.category}</h3>
                </div>
                
                <p className="text-lg mb-4 text-white/90">
                  {insight.insight_text}
                </p>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-white/70">Total Amount</div>
                    <div className="text-xl font-bold">{formatAmount(insight.amount)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-white/70">Percentage</div>
                    <div className="text-xl font-bold">{insight.percentage}%</div>
                  </div>
                </div>
              </div>
              
              <div className="ml-6">
                <button
                  onClick={() => shareInsight(insight)}
                  className="bg-white/20 backdrop-blur-sm border border-white/30 text-white px-4 py-2 rounded-full font-medium hover:bg-white/30 transition-all duration-300 flex items-center gap-2"
                >
                  <Share className="w-4 h-4" />
                  Share
                </button>
              </div>
            </div>
            
            {/* Percentage bar */}
            <div className="mt-4">
              <div className="bg-white/20 rounded-full h-2 overflow-hidden">
                <div 
                  className="bg-white h-full transition-all duration-1000 ease-out"
                  style={{ width: `${Math.min(insight.percentage, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Rank indicator */}
            {index === 0 && (
              <div className="absolute top-4 right-4 bg-yellow-400 text-yellow-900 px-3 py-1 rounded-full text-sm font-bold">
                #1 Category
              </div>
            )}
            
            {/* Background decoration */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-50 transform rotate-12 scale-150"></div>
          </div>
        ))}
      </div>

      {/* Call to Action */}
      <div className="mt-12 bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl p-8 text-center">
        <h3 className="text-2xl font-bold text-gray-800 mb-4">
          Want to improve your campus spending habits? 💡
        </h3>
        <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
          Track your expenses, set budgets, and compete with other campuses to build better financial habits together!
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <button className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-8 py-3 rounded-full font-semibold hover:shadow-lg transition-all duration-300">
            Start Budget Challenge 🎯
          </button>
          <button className="bg-transparent border-2 border-blue-500 text-blue-500 px-8 py-3 rounded-full font-semibold hover:bg-blue-50 transition-all duration-300">
            View Campus Battle 🏆
          </button>
        </div>
      </div>
    </div>
  );
};

export default SpendingInsights;
