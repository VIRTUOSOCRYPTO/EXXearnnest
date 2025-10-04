import React, { useState, useEffect } from 'react';
import axios from 'axios';

const FeatureUnlock = () => {
  const [unlockStatus, setUnlockStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [inviteQuota, setInviteQuota] = useState(null);

  useEffect(() => {
    fetchUnlockStatus();
    fetchInviteQuota();
  }, []);

  const fetchUnlockStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/retention/unlock-status`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setUnlockStatus(response.data);
    } catch (error) {
      console.error('Unlock status error:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchInviteQuota = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/growth/invite-quota`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setInviteQuota(response.data);
    } catch (error) {
      console.error('Invite quota error:', error);
    }
  };

  const getProgressPercentage = (feature) => {
    if (feature.requirement_met) return 100;
    
    // Estimate progress based on requirement text
    const requirement = feature.requirement.toLowerCase();
    const userStats = unlockStatus?.user_stats;
    
    if (requirement.includes('friend')) {
      const required = parseInt(requirement.match(/(\d+)\s*friend/)?.[1] || 0);
      return Math.min((userStats?.friend_count / required) * 100, 100);
    }
    
    if (requirement.includes('transaction')) {
      const required = parseInt(requirement.match(/\d+/)?.[0] || 0);
      return Math.min((userStats?.transactions / required) * 100, 100);
    }
    
    if (requirement.includes('day')) {
      const required = parseInt(requirement.match(/\d+/)?.[0] || 0);
      return Math.min((userStats?.days_active / required) * 100, 100);
    }
    
    if (requirement.includes('₹')) {
      const required = parseInt(requirement.match(/₹(\d+)/)?.[1] || 0);
      const current = userStats?.total_savings || userStats?.total_income || 0;
      return Math.min((current / required) * 100, 100);
    }
    
    return 0;
  };

  const getFeatureColor = (feature) => {
    if (feature.requirement_met) return 'bg-green-100 border-green-300';
    const progress = getProgressPercentage(feature);
    if (progress >= 75) return 'bg-yellow-100 border-yellow-300';
    if (progress >= 25) return 'bg-blue-100 border-blue-300';
    return 'bg-gray-100 border-gray-300';
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-gray-300 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* User Progress Overview */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
          🔓 Feature Unlocks
        </h2>
        
        {unlockStatus && (
          <div className="grid md:grid-cols-5 gap-4 mb-6">
            <div className="bg-blue-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">{unlockStatus.user_stats.transactions}</div>
              <div className="text-sm text-blue-800">Transactions</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-600">{unlockStatus.user_stats.days_active}</div>
              <div className="text-sm text-green-800">Days Active</div>
            </div>
            <div className="bg-pink-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-pink-600">{unlockStatus.user_stats.friend_count}</div>
              <div className="text-sm text-pink-800">Friends</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-purple-600">₹{unlockStatus.user_stats.total_income.toLocaleString()}</div>
              <div className="text-sm text-purple-800">Total Income</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-orange-600">{unlockStatus.unlocked_count}/{unlockStatus.total_features}</div>
              <div className="text-sm text-orange-800">Features Unlocked</div>
            </div>
          </div>
        )}

        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex justify-between text-sm mb-2">
            <span>Overall Progress</span>
            <span>{unlockStatus?.unlocked_count}/{unlockStatus?.total_features} Features</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="bg-gradient-to-r from-green-400 to-blue-500 h-3 rounded-full transition-all duration-500"
              style={{ width: `${(unlockStatus?.unlocked_count / unlockStatus?.total_features) * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid md:grid-cols-2 gap-6">
        {unlockStatus?.features.map((feature, index) => (
          <div key={index} className={`rounded-lg border-2 p-6 ${getFeatureColor(feature)} relative overflow-hidden`}>
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start space-x-3">
                <span className="text-2xl">{feature.icon}</span>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{feature.name}</h3>
                  <p className="text-sm text-gray-600">{feature.description}</p>
                </div>
              </div>
              
              {feature.requirement_met ? (
                <div className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                  Unlocked! 🎉
                </div>
              ) : (
                <div className="bg-gray-300 text-gray-700 px-3 py-1 rounded-full text-sm font-medium">
                  Locked 🔒
                </div>
              )}
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700">Requirement: {feature.requirement}</span>
                  <span className="text-gray-600">{Math.round(getProgressPercentage(feature))}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-500 ${
                      feature.requirement_met 
                        ? 'bg-green-500' 
                        : getProgressPercentage(feature) >= 75
                        ? 'bg-yellow-500'
                        : 'bg-blue-500'
                    }`}
                    style={{ width: `${getProgressPercentage(feature)}%` }}
                  ></div>
                </div>
              </div>

              {!feature.requirement_met && (
                <div className="bg-white bg-opacity-50 rounded p-3">
                  <div className="text-xs text-gray-600">
                    Keep using the app to unlock this feature!
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Social Features Progress */}
      {unlockStatus?.social_progress && (
        <div className="bg-gradient-to-r from-pink-100 to-blue-100 rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            👥 Social Features Progress
          </h3>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-3">Your Friend Network</h4>
              <div className="text-center">
                <div className="text-4xl font-bold text-pink-600 mb-2">
                  {unlockStatus.user_stats.friend_count}
                </div>
                <div className="text-sm text-gray-600">Friends Connected</div>
              </div>
              
              {unlockStatus.social_progress.next_unlock_at && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <div className="text-sm font-medium text-blue-800">Next Unlock:</div>
                  <div className="text-xs text-blue-600">{unlockStatus.social_progress.next_unlock_at}</div>
                </div>
              )}
            </div>
            
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-3">Social Features</h4>
              <div className="space-y-2">
                {unlockStatus.features
                  .filter(f => f.category === 'social')
                  .slice(0, 4)
                  .map((feature, index) => (
                  <div key={index} className={`flex items-center justify-between p-2 rounded ${
                    feature.requirement_met ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-600'
                  }`}>
                    <div className="flex items-center">
                      <span className="text-sm mr-2">{feature.icon}</span>
                      <span className="text-xs">{feature.name}</span>
                    </div>
                    {feature.requirement_met ? (
                      <span className="text-xs font-medium">✅</span>
                    ) : (
                      <span className="text-xs">🔒</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Invite Quota Section */}
      {inviteQuota && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            📨 Invite Quota System
          </h3>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-gray-900">Monthly Invites</span>
                  <span className="text-sm text-gray-600">
                    {inviteQuota.quota.remaining}/{inviteQuota.quota.total} left
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                  <div 
                    className="bg-gradient-to-r from-blue-400 to-purple-500 h-3 rounded-full"
                    style={{ width: `${(inviteQuota.quota.used / inviteQuota.quota.total) * 100}%` }}
                  ></div>
                </div>
                <div className="text-sm text-gray-600">
                  Resets: {new Date(inviteQuota.quota.resets_at).toLocaleDateString()}
                </div>
              </div>

              {inviteQuota.urgency_message && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <div className="text-red-800 text-sm font-medium">
                    {inviteQuota.urgency_message}
                  </div>
                </div>
              )}

              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-gray-700 font-medium mb-2">Quota Breakdown:</div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Base Quota:</span>
                    <span>{inviteQuota.breakdown.base_quota}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Level Bonus:</span>
                    <span>+{inviteQuota.breakdown.level_bonus}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Achievement Bonus:</span>
                    <span>+{inviteQuota.breakdown.achievement_bonus}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-yellow-50 rounded-lg p-4">
                <h4 className="font-medium text-yellow-800 mb-2">Unlock More Invites:</h4>
                <div className="space-y-2">
                  {inviteQuota.bonus_opportunities.map((opportunity, index) => (
                    <div key={index} className="bg-white rounded p-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-700">{opportunity.action}</span>
                        <span className="text-xs text-green-600 font-medium">{opportunity.reward}</span>
                      </div>
                      <div className="text-xs text-gray-500">{opportunity.progress}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-purple-50 rounded-lg p-4 text-center">
                <div className="text-sm font-medium text-purple-800 mb-2">
                  {inviteQuota.scarcity_marketing}
                </div>
                <button className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium">
                  Invite Friends Now
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FeatureUnlock;
