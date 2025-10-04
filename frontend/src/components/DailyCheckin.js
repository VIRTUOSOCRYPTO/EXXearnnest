import React, { useState, useEffect } from 'react';
import axios from 'axios';

const DailyCheckin = () => {
  const [checkinStatus, setCheckinStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [canCheckin, setCanCheckin] = useState(true);
  const [dailyTip, setDailyTip] = useState(null);

  useEffect(() => {
    fetchDailyTip();
    checkTodayStatus();
  }, []);

  const fetchDailyTip = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/engagement/daily-tip`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setDailyTip(response.data);
    } catch (error) {
      console.error('Daily tip error:', error);
    }
  };

  const checkTodayStatus = () => {
    const lastCheckin = localStorage.getItem('lastCheckin');
    const today = new Date().toDateString();
    if (lastCheckin === today) {
      setCanCheckin(false);
    }
  };

  const handleCheckin = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/retention/daily-checkin`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        setCheckinStatus(response.data);
        setCanCheckin(false);
        localStorage.setItem('lastCheckin', new Date().toDateString());
        
        // Show celebration
        setTimeout(() => {
          setCheckinStatus(null);
        }, 5000);
      }
    } catch (error) {
      console.error('Check-in error:', error);
      if (error.response?.data?.message) {
        alert(error.response.data.message);
        setCanCheckin(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const getStreakColor = (streak) => {
    if (streak >= 30) return 'text-purple-600';
    if (streak >= 14) return 'text-blue-600';
    if (streak >= 7) return 'text-green-600';
    return 'text-orange-600';
  };

  const getStreakEmoji = (streak) => {
    if (streak >= 100) return '👑';
    if (streak >= 30) return '🔥';
    if (streak >= 14) return '⚡';
    if (streak >= 7) return '🎯';
    return '⭐';
  };

  return (
    <div className="max-w-md mx-auto">
      {/* Daily Check-in Card */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="text-center">
          <div className="text-4xl mb-3">📅</div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">Daily Check-in</h3>
          
          {canCheckin ? (
            <div>
              <p className="text-gray-600 mb-4">Start your day right with EarnAura!</p>
              <button
                onClick={handleCheckin}
                disabled={loading}
                className="w-full bg-gradient-to-r from-green-500 to-blue-500 text-white font-bold py-3 px-6 rounded-lg hover:from-green-600 hover:to-blue-600 transition-all duration-200 transform hover:scale-105 disabled:opacity-50"
              >
                {loading ? 'Checking in...' : 'Check In Now! ✨'}
              </button>
              <p className="text-sm text-gray-500 mt-2">Earn daily points and build your streak!</p>
            </div>
          ) : (
            <div className="bg-gray-100 rounded-lg p-4">
              <div className="text-2xl mb-2">✅</div>
              <p className="text-gray-600 font-medium">Already checked in today!</p>
              <p className="text-sm text-gray-500 mt-1">Come back tomorrow for more points</p>
            </div>
          )}
        </div>
      </div>

      {/* Enhanced Check-in Success Modal */}
      {checkinStatus && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full text-center animate-bounce">
            <div className="text-6xl mb-4">{getStreakEmoji(checkinStatus.streak)}</div>
            
            {/* Streak Tier Badge */}
            <div className={`inline-block px-3 py-1 rounded-full text-sm font-bold mb-3 ${
              checkinStatus.streak_tier === 'legend' ? 'bg-purple-100 text-purple-800' :
              checkinStatus.streak_tier === 'champion' ? 'bg-gold-100 text-gold-800' :
              checkinStatus.streak_tier === 'warrior' ? 'bg-blue-100 text-blue-800' :
              'bg-green-100 text-green-800'
            }`}>
              {checkinStatus.streak_tier?.toUpperCase()} STATUS
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Check-in Complete!</h3>
            
            <div className="space-y-2 mb-4">
              <div className={`text-2xl font-bold ${getStreakColor(checkinStatus.streak)}`}>
                {checkinStatus.streak} Day Streak!
              </div>
              <div className="text-lg text-green-600 font-semibold">
                +{checkinStatus.points_earned} Points Earned
              </div>
            </div>

            {checkinStatus.milestone_message && (
              <div className="bg-yellow-100 border border-yellow-300 rounded-lg p-3 mb-4">
                <p className="text-yellow-800 font-medium">{checkinStatus.milestone_message}</p>
              </div>
            )}

            <div className="text-sm text-gray-600 space-y-1">
              <div>Base Points: +{checkinStatus.base_points}</div>
              <div>Streak Bonus: +{checkinStatus.streak_bonus}</div>
              {checkinStatus.weekly_multiplier_bonus > 0 && (
                <div className="text-blue-600 font-semibold">
                  Weekly Multiplier: +{checkinStatus.weekly_multiplier_bonus} 🎉
                </div>
              )}
              {checkinStatus.milestone_bonus > 0 && (
                <div className="text-purple-600 font-semibold">
                  Milestone Bonus: +{checkinStatus.milestone_bonus}
                </div>
              )}
            </div>
            
            {checkinStatus.is_weekly_multiplier && (
              <div className="bg-blue-100 border border-blue-300 rounded-lg p-3 mt-3">
                <p className="text-blue-800 font-medium text-sm">
                  🔥 7-Day Streak Achieved! Double points earned!
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Daily Tip Card */}
      {dailyTip && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center mb-3">
            <span className="text-2xl mr-3">{dailyTip.tip.icon}</span>
            <h3 className="text-lg font-bold text-gray-900">
              {dailyTip.tip.type === 'tip' ? 'Daily Tip' : 'Daily Quote'}
            </h3>
            {dailyTip.is_new && (
              <span className="ml-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">NEW</span>
            )}
          </div>
          
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-2">{dailyTip.tip.title}</h4>
            <p className="text-gray-700 text-sm leading-relaxed">{dailyTip.tip.content}</p>
          </div>
          
          <div className="mt-3 text-center">
            <p className="text-xs text-gray-500">{dailyTip.streak_info}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DailyCheckin;
