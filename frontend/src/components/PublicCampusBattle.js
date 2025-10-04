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
      <div className="relative overflow-hidden bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 py-16">
        <div className="absolute inset-0 bg-black opacity-20"></div>
        <div className="relative container mx-auto px-6 text-center">
          <h1 className="text-5xl md:text-7xl font-extrabold mb-4 bg-gradient-to-r from-yellow-300 to-pink-300 bg-clip-text text-transparent">
            🏆 CAMPUS BATTLE ARENA
          </h1>
          <p className="text-xl md:text-2xl text-pink-100 max-w-3xl mx-auto mb-8">
            Real-time college vs college savings showdown! See where your campus ranks in India's biggest student finance challenge.
          </p>
          
          {trendingCampus && (
            <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-full px-8 py-3 inline-flex items-center gap-2 shadow-lg">
              <Flame className="w-5 h-5" />
              <span className="font-semibold">🔥 Trending: {trendingCampus}</span>
            </div>
          )}
        </div>
      </div>

      {/* Battle Stats */}
      <div className="container mx-auto px-6 py-8">
        {/* Controls */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold">Live Rankings</h2>
            {lastUpdated && (
              <span className="text-sm text-gray-300">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-4">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                autoRefresh 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-gray-600 hover:bg-gray-700'
              }`}
            >
              {autoRefresh ? '🔄 Auto-Refresh ON' : '⏸️ Auto-Refresh OFF'}
            </button>
            
            <button
              onClick={fetchBattleData}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg font-medium transition flex items-center gap-2"
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
              className={`relative overflow-hidden rounded-xl bg-gradient-to-r ${getRankColor(campus.rank)} p-6 shadow-xl transform hover:scale-105 transition-all duration-300`}
            >
              {/* Rank Badge */}
              <div className="absolute top-4 left-4 flex items-center justify-center w-12 h-12 bg-black bg-opacity-20 rounded-full">
                {getRankIcon(campus.rank)}
              </div>

              <div className="ml-16">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-2xl font-bold mb-2">{campus.campus}</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        <Banknote className="w-4 h-4" />
                        <span>Total Saved: {formatAmount(campus.total_savings)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4" />
                        <span>{campus.active_users}/{campus.total_users} Active</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Banknote className="w-4 h-4" />
                        <span>Avg: {formatAmount(campus.average_monthly_savings)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Flame className="w-4 h-4" />
                        <span>Activity: {campus.recent_activity_score}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-3xl font-bold">#{campus.rank}</div>
                    <div className="text-sm opacity-75">
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
        <div className="mt-16 text-center bg-gradient-to-r from-green-600 to-blue-600 rounded-2xl p-8">
          <h3 className="text-3xl font-bold mb-4">Want to boost your campus ranking? 🚀</h3>
          <p className="text-xl text-green-100 mb-6">
            Join EarnNest and help your college dominate the leaderboard!
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <a 
              href="/register" 
              className="bg-white text-blue-600 px-8 py-3 rounded-full font-bold text-lg hover:bg-gray-100 transition-colors"
            >
              Join the Battle! 🎯
            </a>
            <button className="bg-transparent border-2 border-white text-white px-8 py-3 rounded-full font-bold text-lg hover:bg-white hover:text-blue-600 transition-colors">
              Share this Battle 📢
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PublicCampusBattle;
