import React, { useState, useEffect } from 'react';
import { Users, TrendingUp, TrendingDown, Equal, Share } from 'lucide-react';

const FriendComparisons = () => {
  const [comparisons, setComparisons] = useState([]);
  const [friendCount, setFriendCount] = useState(0);
  const [hasFriends, setHasFriends] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchFriendComparisons();
  }, []);

  const fetchFriendComparisons = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/insights/friend-comparison`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        setComparisons(data.comparisons || []);
        setFriendCount(data.friend_count || 0);
        setHasFriends(data.has_friends);
        setMessage(data.message || '');
      }
    } catch (error) {
      console.error('Error fetching friend comparisons:', error);
    } finally {
      setLoading(false);
    }
  };

  const shareComparison = async (comparison) => {
    const shareText = `${comparison.comparison_text} ${comparison.emoji} Check out EarnAura to compare your spending with friends! #EarnAura #StudentFinance`;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Friend Spending Comparison',
          text: shareText,
          url: window.location.origin
        });
      } catch (error) {
        console.log('Share cancelled');
      }
    } else {
      navigator.clipboard.writeText(shareText);
      alert('Comparison copied to clipboard! Share it with your friends 😄');
    }
  };

  const getTrendIcon = (trend) => {
    switch(trend) {
      case 'higher': return <TrendingUp className="w-5 h-5 text-red-500" />;
      case 'lower': return <TrendingDown className="w-5 h-5 text-green-500" />;
      default: return <Equal className="w-5 h-5 text-blue-500" />;
    }
  };

  const getTrendColor = (trend, category) => {
    if (category === 'total') {
      return trend === 'lower' ? 'from-green-500 to-emerald-600' : 'from-red-500 to-pink-600';
    }
    
    const colorMap = {
      'Food': trend === 'lower' ? 'from-green-500 to-teal-500' : 'from-orange-500 to-red-500',
      'Entertainment': trend === 'lower' ? 'from-green-500 to-blue-500' : 'from-purple-500 to-pink-500',
      'Shopping': trend === 'lower' ? 'from-green-500 to-cyan-500' : 'from-blue-500 to-indigo-600'
    };
    
    return colorMap[category] || 'from-gray-500 to-gray-600';
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
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-gray-300 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!hasFriends) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-12">
          <Users className="w-16 h-16 mx-auto mb-6 text-gray-400" />
          <h2 className="text-3xl font-bold text-gray-800 mb-4">
            Connect with Friends! 👥
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-md mx-auto">
            {message || "Add friends to see anonymous spending comparisons and discover insights about your financial habits!"}
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <button 
              onClick={() => window.location.href = '/friends'}
              className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-8 py-3 rounded-full font-semibold text-lg hover:shadow-lg transition-all duration-300"
            >
              Add Friends Now 🚀
            </button>
            <button className="bg-transparent border-2 border-blue-500 text-blue-500 px-8 py-3 rounded-full font-semibold text-lg hover:bg-blue-50 transition-all duration-300">
              Share Invite Link 📲
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (comparisons.length === 0) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-12">
          <TrendingUp className="w-16 h-16 mx-auto mb-6 text-gray-400" />
          <h2 className="text-3xl font-bold text-gray-800 mb-4">
            Start Tracking for Comparisons! 📊
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-md mx-auto">
            {message || `You and your ${friendCount} friends need to record more expenses to see spending comparisons!`}
          </p>
          <button className="bg-gradient-to-r from-green-500 to-blue-500 text-white px-8 py-3 rounded-full font-semibold text-lg hover:shadow-lg transition-all duration-300">
            Add Your First Expense 💰
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-extrabold text-gray-800 mb-4 flex items-center justify-center gap-3">
          <Users className="w-10 h-10 text-blue-600" />
          Friend Comparisons 👥
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-6">
          Anonymous insights into how your spending compares with your {friendCount} friends
        </p>
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full px-6 py-2 inline-block">
          <span className="text-sm font-medium">🔒 100% Anonymous • Last 30 Days</span>
        </div>
      </div>

      {/* Comparison Cards */}
      <div className="grid gap-6">
        {comparisons.map((comparison, index) => (
          <div
            key={comparison.category}
            className={`relative overflow-hidden rounded-xl bg-gradient-to-r ${getTrendColor(comparison.trend, comparison.category)} p-6 text-white shadow-xl transform hover:scale-105 transition-all duration-300`}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-4 mb-4">
                  <span className="text-4xl">{comparison.emoji}</span>
                  <div>
                    <h3 className="text-2xl font-bold capitalize">
                      {comparison.category === 'total' ? 'Total Spending' : `${comparison.category} Spending`}
                    </h3>
                    <div className="flex items-center gap-2 text-white/80">
                      {getTrendIcon(comparison.trend)}
                      <span className="text-sm">vs Friends Average</span>
                    </div>
                  </div>
                </div>
                
                <p className="text-lg mb-6 text-white/90">
                  {comparison.comparison_text}
                </p>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm text-white/70">Your Amount</div>
                    <div className="text-xl font-bold">{formatAmount(comparison.user_amount)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-white/70">Friends Average</div>
                    <div className="text-xl font-bold">{formatAmount(comparison.friend_average)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-white/70">Difference</div>
                    <div className="text-xl font-bold">
                      {comparison.percentage_difference > 0 ? '+' : ''}{comparison.percentage_difference.toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="ml-6">
                <button
                  onClick={() => shareComparison(comparison)}
                  className="bg-white/20 backdrop-blur-sm border border-white/30 text-white px-4 py-3 rounded-full font-medium hover:bg-white/30 transition-all duration-300 flex items-center gap-2"
                >
                  <Share className="w-4 h-4" />
                  Share
                </button>
              </div>
            </div>
            
            {/* Progress bar showing relative position */}
            <div className="mt-6">
              <div className="text-sm text-white/70 mb-2">Your spending vs friends</div>
              <div className="bg-white/20 rounded-full h-3 overflow-hidden">
                <div 
                  className="bg-white h-full transition-all duration-1000 ease-out flex items-center justify-end pr-2"
                  style={{ 
                    width: `${Math.min(Math.max(50 + (comparison.percentage_difference / 2), 10), 90)}%`
                  }}
                >
                  <div className="w-2 h-2 bg-yellow-300 rounded-full"></div>
                </div>
              </div>
              <div className="flex justify-between text-xs text-white/60 mt-1">
                <span>Spends Less</span>
                <span>You</span>
                <span>Spends More</span>
              </div>
            </div>

            {/* Background decoration */}
            <div className="absolute top-0 right-0 transform translate-x-12 -translate-y-12">
              <div className="w-40 h-40 bg-white/5 rounded-full"></div>
            </div>
          </div>
        ))}
      </div>

      {/* Insights Summary */}
      <div className="mt-12 bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl p-8">
        <h3 className="text-2xl font-bold text-gray-800 mb-4 text-center">
          💡 Your Spending Personality
        </h3>
        
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg p-6 shadow-md">
            <h4 className="font-bold text-gray-800 mb-3">Spending Insights</h4>
            <ul className="space-y-2 text-gray-600">
              {comparisons.filter(c => c.trend === 'lower').length > 0 && (
                <li className="flex items-center gap-2">
                  <TrendingDown className="w-4 h-4 text-green-500" />
                  You're saving in {comparisons.filter(c => c.trend === 'lower').length} categories
                </li>
              )}
              {comparisons.filter(c => c.trend === 'higher').length > 0 && (
                <li className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-orange-500" />
                  Room to optimize in {comparisons.filter(c => c.trend === 'higher').length} areas
                </li>
              )}
              <li className="flex items-center gap-2">
                <Users className="w-4 h-4 text-blue-500" />
                Compared with {friendCount} friends anonymously
              </li>
            </ul>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow-md">
            <h4 className="font-bold text-gray-800 mb-3">Keep Going!</h4>
            <p className="text-gray-600 mb-4">
              These anonymous comparisons help you understand your financial habits better. 
              Keep tracking to see how you improve over time!
            </p>
            <button className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white py-2 px-4 rounded-lg font-medium hover:shadow-lg transition-all duration-300">
              Set Budget Goals 🎯
            </button>
          </div>
        </div>
      </div>

      {/* Add More Friends CTA */}
      <div className="mt-12 text-center bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl p-8">
        <h3 className="text-2xl font-bold mb-4">Get Better Insights! 📈</h3>
        <p className="text-lg text-purple-100 mb-6">
          Add more friends to get more accurate spending comparisons and discover new insights!
        </p>
        <button 
          onClick={() => window.location.href = '/friends'}
          className="bg-white text-purple-600 px-8 py-3 rounded-full font-bold text-lg hover:bg-gray-100 transition-colors"
        >
          Invite More Friends 👫
        </button>
      </div>
    </div>
  );
};

export default FriendComparisons;
