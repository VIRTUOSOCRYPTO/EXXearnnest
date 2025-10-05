import React, { useState, useEffect } from 'react';
import { Trophy, Users, Banknote, Share, Sparkles } from 'lucide-react';

const ViralMilestones = () => {
  const [appMilestones, setAppMilestones] = useState([]);
  const [campusMilestones, setCampusMilestones] = useState([]);
  const [celebrationReady, setCelebrationReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [totalStats, setTotalStats] = useState({});

  useEffect(() => {
    fetchViralMilestones();
  }, []);

  const fetchViralMilestones = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/milestones/check`);
      const data = await response.json();
      
      if (data.success) {
        setAppMilestones(data.app_wide_milestones || []);
        setCampusMilestones(data.campus_milestones || []);
        setCelebrationReady(data.celebration_ready);
        setTotalStats({
          totalSavings: data.total_app_savings,
          totalUsers: data.total_app_users
        });
      }
    } catch (error) {
      console.error('Error fetching viral milestones:', error);
    } finally {
      setLoading(false);
    }
  };

  const shareMilestone = async (milestone) => {
    const shareText = `🎉 ${milestone.achievement_text} 💰 Join the movement! #EarnAura #StudentFinance #FinancialFreedom`;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Amazing Financial Milestone!',
          text: shareText,
          url: window.location.origin
        });
      } catch (error) {
        console.log('Share cancelled');
      }
    } else {
      // Fallback to clipboard
      navigator.clipboard.writeText(shareText);
      alert('Milestone copied to clipboard! Share it on social media 🚀');
    }
  };

  const formatAmount = (amount) => {
    if (amount >= 10000000) {
      return `₹${(amount / 10000000).toFixed(1)} crore`;
    } else if (amount >= 100000) {
      return `₹${(amount / 100000).toFixed(1)} lakh`;
    } else if (amount >= 1000) {
      return `₹${(amount / 1000).toFixed(1)}K`;
    }
    return `₹${amount.toLocaleString()}`;
  };

  const getMilestoneColor = (type, level) => {
    if (type === 'app_wide') {
      return level === 'major' 
        ? 'from-yellow-400 via-orange-500 to-red-500' 
        : 'from-blue-500 to-purple-600';
    } else {
      return level === 'major'
        ? 'from-green-500 via-teal-500 to-blue-500'
        : 'from-purple-500 to-pink-500';
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-300 rounded w-1/3 mb-6"></div>
          <div className="grid gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-gray-300 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const allMilestones = [...appMilestones, ...campusMilestones];

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-extrabold text-gray-800 mb-4">
          🎉 Viral Milestone Celebrations
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Celebrating incredible financial achievements across India's student community!
        </p>
        
        {totalStats.totalSavings && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl mx-auto">
            <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl p-6">
              <div className="text-3xl font-bold">{formatAmount(totalStats.totalSavings)}</div>
              <div className="text-green-100">Total Savings Nationwide</div>
            </div>
            <div className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl p-6">
              <div className="text-3xl font-bold">{totalStats.totalUsers.toLocaleString()}</div>
              <div className="text-blue-100">Active Student Savers</div>
            </div>
          </div>
        )}
      </div>

      {allMilestones.length === 0 ? (
        <div className="text-center bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl p-12">
          <Sparkles className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h3 className="text-2xl font-semibold text-gray-700 mb-4">
            Amazing milestones are coming! 🚀
          </h3>
          <p className="text-gray-600 max-w-md mx-auto">
            Keep saving and tracking your finances. The next viral milestone celebration could feature your campus!
          </p>
        </div>
      ) : (
        <div className="grid gap-8">
          {/* App-wide Milestones */}
          {appMilestones.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                <Trophy className="w-8 h-8 text-yellow-500" />
                🇮🇳 Nationwide Achievements
              </h2>
              <div className="grid gap-6">
                {appMilestones.map((milestone, index) => (
                  <div
                    key={index}
                    className={`relative overflow-hidden rounded-2xl bg-gradient-to-r ${getMilestoneColor(milestone.type, milestone.celebration_level)} p-8 text-white shadow-2xl transform hover:scale-105 transition-all duration-300`}
                  >
                    {/* Celebration particles */}
                    <div className="absolute inset-0 overflow-hidden">
                      {[...Array(20)].map((_, i) => (
                        <div
                          key={i}
                          className="absolute animate-bounce text-white text-opacity-60"
                          style={{
                            left: `${Math.random() * 100}%`,
                            top: `${Math.random() * 100}%`,
                            animationDelay: `${Math.random() * 2}s`,
                            fontSize: `${12 + Math.random() * 8}px`
                          }}
                        >
                          {['✨', '🎉', '⭐', '💫', '🎊'][Math.floor(Math.random() * 5)]}
                        </div>
                      ))}
                    </div>

                    <div className="relative z-10">
                      <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-4">
                          <div className="text-6xl">
                            {milestone.celebration_level === 'major' ? '🏆' : '🎯'}
                          </div>
                          <div>
                            <h3 className="text-3xl font-bold mb-2">INCREDIBLE MILESTONE!</h3>
                            <p className="text-xl text-white/90">
                              {milestone.achievement_text}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => shareMilestone(milestone)}
                          className="bg-white/20 backdrop-blur-sm border border-white/30 hover:bg-white/30 px-6 py-3 rounded-full transition-all duration-300 flex items-center gap-2"
                        >
                          <Share className="w-5 h-5" />
                          Share News!
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                          <div className="text-white/70">Milestone Target</div>
                          <div className="text-xl font-bold">{formatAmount(milestone.milestone)}</div>
                        </div>
                        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                          <div className="text-white/70">Current Value</div>
                          <div className="text-xl font-bold">{formatAmount(milestone.current_value)}</div>
                        </div>
                        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                          <div className="text-white/70">Achievement Level</div>
                          <div className="text-xl font-bold capitalize">{milestone.celebration_level}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Campus-specific Milestones */}
          {campusMilestones.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                <Users className="w-8 h-8 text-blue-500" />
                🏛️ Campus Champions
              </h2>
              <div className="grid md:grid-cols-2 gap-6">
                {campusMilestones.map((milestone, index) => (
                  <div
                    key={index}
                    className={`relative overflow-hidden rounded-xl bg-gradient-to-br ${getMilestoneColor(milestone.type, milestone.celebration_level)} p-6 text-white shadow-xl hover:shadow-2xl transition-all duration-300`}
                  >
                    <div className="relative z-10">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="text-xl font-bold mb-1">{milestone.campus}</h3>
                          <p className="text-white/90">{milestone.achievement_text}</p>
                        </div>
                        <div className="text-3xl">
                          {milestone.celebration_level === 'major' ? '🎖️' : '⭐'}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3 mb-4">
                        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3">
                          <div className="text-xs text-white/70">Target</div>
                          <div className="font-bold">{formatAmount(milestone.milestone)}</div>
                        </div>
                        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3">
                          <div className="text-xs text-white/70">Achieved</div>
                          <div className="font-bold">{formatAmount(milestone.current_value)}</div>
                        </div>
                      </div>

                      <button
                        onClick={() => shareMilestone(milestone)}
                        className="w-full bg-white/20 backdrop-blur-sm border border-white/30 hover:bg-white/30 py-2 px-4 rounded-lg transition-all duration-300 flex items-center justify-center gap-2"
                      >
                        <Share className="w-4 h-4" />
                        Share Campus Pride!
                      </button>
                    </div>

                    {/* Background decoration */}
                    <div className="absolute top-0 right-0 transform translate-x-8 -translate-y-8">
                      <div className="w-32 h-32 bg-white/10 rounded-full"></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Call to Action */}
      <div className="mt-16 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 text-center text-white">
        <h3 className="text-3xl font-bold mb-4">Be Part of the Next Milestone! 🚀</h3>
        <p className="text-xl text-indigo-100 mb-6 max-w-2xl mx-auto">
          Every rupee saved, every goal achieved contributes to these incredible celebrations. 
          Your campus could be the next champion!
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <button className="bg-white text-indigo-600 px-8 py-3 rounded-full font-bold text-lg hover:bg-gray-100 transition-colors">
            Start Your Journey 💪
          </button>
          <button 
            onClick={() => window.open('/public/campus-battle', '_blank')}
            className="bg-transparent border-2 border-white text-white px-8 py-3 rounded-full font-bold text-lg hover:bg-white hover:text-indigo-600 transition-colors"
          >
            View Campus Rankings 🏆
          </button>
        </div>
      </div>
    </div>
  );
};

export default ViralMilestones;
