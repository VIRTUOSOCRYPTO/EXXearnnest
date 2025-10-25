import React, { useState, useEffect } from 'react';
import { Trophy, Users, Banknote, Flame, RefreshCw } from 'lucide-react';

const PublicCampusBattle = () => {
  const [battleData, setBattleData] = useState([]);
  const [trendingCampus, setTrendingCampus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchBattleData = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/public/campus-battle`);
      const data = await response.json();
      
      if (data.success) {
        setBattleData(data.campus_battle || []);
        setTrendingCampus(data.trending_campus);
        setLastUpdated(new Date());
      }
    } catch (error) {
      console.error('Error fetching battle data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBattleData();
    
    // Auto-refresh every 30 seconds
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchBattleData, 30000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const formatAmount = (amount) => {
    if (amount >= 100000) {
      return `₹${(amount / 100000).toFixed(1)}L`;
    }
    return `₹${amount.toLocaleString()}`;
  };

  const getRankColor = (rank) => {
    switch(rank) {
      case 1: return 'from-yellow-400 to-yellow-600 text-white';
      case 2: return 'from-gray-300 to-gray-500 text-white';
      case 3: return 'from-orange-400 to-orange-600 text-white';
      default: return 'from-blue-500 to-purple-600 text-white';
    }
  };

  const getRankIcon = (rank) => {
    if (rank <= 3) {
      return <Trophy className="w-6 h-6" />;
    }
    return <span className="text-xl font-bold">#{rank}</span>;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-white mx-auto"></div>
          <p className="mt-4 text-xl">Loading Campus Battle...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      {/* Header */}
      <div className="relative overflow-hidden bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 py-12 sm:py-16">
        <div className="absolute inset-0 bg-black opacity-20"></div>
        <div className="relative container mx-auto px-4 sm:px-6 text-center">
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold mb-4 bg-gradient-to-r from-yellow-300 to-pink-300 bg-clip-text text-transparent leading-tight">
            🏆 CAMPUS BATTLE ARENA
          </h1>
          <p className="text-lg sm:text-xl md:text-2xl text-pink-100 max-w-3xl mx-auto mb-6 sm:mb-8 px-4">
            Real-time college vs college savings showdown! See where your campus ranks in India's biggest student finance challenge.
          </p>
          
          {trendingCampus && (
            <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-full px-6 sm:px-8 py-3 inline-flex items-center gap-2 shadow-lg">
              <Flame className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0" />
              <span className="font-semibold text-sm sm:text-base">🔥 Trending: {trendingCampus}</span>
            </div>
          )}
        </div>
      </div>

      {/* Battle Stats */}
      <div className="container mx-auto px-6 py-8">
        {/* Controls */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
            <h2 className="text-2xl font-bold">Live Rankings</h2>
            {lastUpdated && (
              <span className="text-sm text-gray-300">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </div>
          
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 w-full sm:w-auto">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2.5 rounded-lg font-medium transition whitespace-nowrap ${
                autoRefresh 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-gray-600 hover:bg-gray-700'
              }`}
            >
              {autoRefresh ? '🔄 Auto-Refresh ON' : '⏸️ Auto-Refresh OFF'}
            </button>
            
            <button
              onClick={fetchBattleData}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2.5 rounded-lg font-medium transition flex items-center justify-center gap-2 whitespace-nowrap"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh Now
            </button>
          </div>
        </div>

        {/* Battle Leaderboard */}
        <div className="grid gap-4">
          {battleData.map((campus, index) => (
            <div
              key={campus.campus}
              className={`relative overflow-hidden rounded-xl bg-gradient-to-r ${getRankColor(campus.rank)} p-4 sm:p-6 shadow-xl transform hover:scale-105 transition-all duration-300`}
            >
              {/* Rank Badge */}
              <div className="absolute top-4 left-4 flex items-center justify-center w-10 h-10 sm:w-12 sm:h-12 bg-black bg-opacity-20 rounded-full">
                {getRankIcon(campus.rank)}
              </div>

              <div className="ml-12 sm:ml-16">
                <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
                  <div className="flex-1">
                    <h3 className="text-xl sm:text-2xl font-bold mb-3">{campus.campus}</h3>
                    <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 text-xs sm:text-sm">
                      <div className="flex items-center gap-2">
                        <Banknote className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
                        <span className="truncate">Saved: {formatAmount(campus.total_savings)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Users className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
                        <span className="truncate">{campus.active_users}/{campus.total_users} Active</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Banknote className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
                        <span className="truncate">Avg: {formatAmount(campus.average_monthly_savings)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Flame className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
                        <span className="truncate">Activity: {campus.recent_activity_score}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right w-full sm:w-auto flex sm:flex-col justify-between sm:justify-start items-center sm:items-end">
                    <div className="text-2xl sm:text-3xl font-bold">#{campus.rank}</div>
                    <div className="text-xs sm:text-sm opacity-75">
                      {formatAmount(campus.total_earnings)} earned
                    </div>
                  </div>
                </div>
              </div>

              {/* Animated background effect for top 3 */}
              {campus.rank <= 3 && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white via-transparent to-transparent opacity-10 transform -skew-x-12 animate-pulse"></div>
              )}
            </div>
          ))}
        </div>

        {/* Footer Call to Action */}
        <div className="mt-12 sm:mt-16 text-center bg-gradient-to-r from-green-600 to-blue-600 rounded-2xl p-6 sm:p-8">
          <h3 className="text-2xl sm:text-3xl font-bold mb-3 sm:mb-4">Want to boost your campus ranking? 🚀</h3>
          <p className="text-lg sm:text-xl text-green-100 mb-4 sm:mb-6 px-4">
            Join EarnAura and help your college dominate the leaderboard!
          </p>
          <div className="flex flex-col sm:flex-row flex-wrap justify-center gap-3 sm:gap-4">
            <a 
              href="/register" 
              className="bg-white text-blue-600 px-6 sm:px-8 py-3 rounded-full font-bold text-base sm:text-lg hover:bg-gray-100 transition-colors"
            >
              Join the Battle! 🎯
            </a>
            <button className="bg-transparent border-2 border-white text-white px-6 sm:px-8 py-3 rounded-full font-bold text-base sm:text-lg hover:bg-white hover:text-blue-600 transition-colors">
              Share this Battle 📢
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PublicCampusBattle;
