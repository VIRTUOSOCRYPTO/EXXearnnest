import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import {
  UserPlusIcon,
  SparklesIcon,
  ChartBarIcon,
  GiftIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  RocketLaunchIcon,
  CubeIcon,
  LightBulbIcon,
  LinkIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const GrowthMechanics = () => {
  const [inviteQuota, setInviteQuota] = useState(null);
  const [betaAccess, setBetaAccess] = useState(null);
  const [waitlistFeatures, setWaitlistFeatures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('invites');
  const { user } = useAuth();

  useEffect(() => {
    fetchGrowthData();
  }, []);

  const fetchGrowthData = async () => {
    try {
      const [quotaResponse, betaResponse] = await Promise.all([
        axios.get(`${API}/growth/invite-quota`),
        axios.get(`${API}/growth/beta-access`)
      ]);

      setInviteQuota(quotaResponse.data);
      setBetaAccess(betaResponse.data);
    } catch (error) {
      console.error('Error fetching growth data:', error);
    } finally {
      setLoading(false);
    }
  };

  const joinWaitlist = async (featureName) => {
    try {
      const response = await axios.post(`${API}/growth/waitlist/join?feature_name=${featureName}`);
      alert(`Successfully joined waitlist for ${response.data.feature.name}! Your position: #${response.data.waitlist_position}`);
      fetchGrowthData(); // Refresh data
    } catch (error) {
      console.error('Error joining waitlist:', error);
      alert(error.response?.data?.detail || 'Failed to join waitlist');
    }
  };

  const requestBetaAccess = async (featureId) => {
    try {
      const response = await axios.post(`${API}/growth/beta-access/request/${featureId}`);
      alert(`Beta access granted for ${response.data.feature.name}!`);
      fetchGrowthData(); // Refresh data
    } catch (error) {
      console.error('Error requesting beta access:', error);
      alert(error.response?.data?.detail || 'Failed to request beta access');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <SparklesIcon className="w-8 h-8 text-emerald-500 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600">Loading growth features...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Growth & Exclusive Features</h1>
        <p className="text-gray-600 mt-1">Unlock premium features and expand your network</p>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="flex space-x-8">
          {['invites', 'beta', 'waitlist'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-emerald-500 text-emerald-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab === 'invites' ? 'Invite Quota' : tab === 'beta' ? 'Beta Features' : 'Feature Waitlist'}
            </button>
          ))}
        </nav>
      </div>

      {/* Invite Quota Tab */}
      {activeTab === 'invites' && inviteQuota && (
        <div className="space-y-8">
          {/* Quota Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-2xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-emerald-100 text-sm">Remaining Invites</p>
                  <p className="text-3xl font-bold">{inviteQuota.quota_info.remaining}</p>
                </div>
                <UserPlusIcon className="w-8 h-8 text-emerald-200" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm">Monthly Limit</p>
                  <p className="text-3xl font-bold">{inviteQuota.quota_info.monthly_limit}</p>
                </div>
                <ClockIcon className="w-8 h-8 text-blue-200" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-2xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">Bonus Invites</p>
                  <p className="text-3xl font-bold">{inviteQuota.quota_info.bonus_invites}</p>
                </div>
                <GiftIcon className="w-8 h-8 text-purple-200" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-orange-100 text-sm">Total Earned</p>
                  <p className="text-3xl font-bold">{inviteQuota.quota_info.total_earned}</p>
                </div>
                <ChartBarIcon className="w-8 h-8 text-orange-200" />
              </div>
            </div>
          </div>

          {/* Usage Progress */}
          <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900">Monthly Usage</h3>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                inviteQuota.usage_status.urgency_level === 'high' 
                  ? 'bg-red-100 text-red-800' 
                  : inviteQuota.usage_status.urgency_level === 'medium'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-green-100 text-green-800'
              }`}>
                {inviteQuota.usage_status.urgency_level === 'high' ? 'Critical' : 
                 inviteQuota.usage_status.urgency_level === 'medium' ? 'Moderate' : 'Good'}
              </div>
            </div>
            
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  Used {inviteQuota.quota_info.used_this_month} of {inviteQuota.quota_info.total_available} invites
                </span>
                <span className="text-sm text-gray-600">
                  {Math.round(inviteQuota.usage_status.usage_percentage)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full ${
                    inviteQuota.usage_status.urgency_level === 'high' 
                      ? 'bg-red-500' 
                      : inviteQuota.usage_status.urgency_level === 'medium'
                      ? 'bg-yellow-500'
                      : 'bg-emerald-500'
                  }`}
                  style={{ width: `${inviteQuota.usage_status.usage_percentage}%` }}
                />
              </div>
            </div>

            <div className="text-sm text-gray-600 mb-4">
              Resets on: {new Date(inviteQuota.quota_info.reset_date).toLocaleDateString()}
            </div>

            {inviteQuota.usage_status.urgency_level === 'high' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <ExclamationTriangleIcon className="w-5 h-5 text-red-400 mr-2" />
                  <p className="text-red-700 text-sm">
                    Low on invites! Complete achievements below to earn bonus invites.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Earning Opportunities */}
          <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-200">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Earn More Invites</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {inviteQuota.earning_opportunities.map((opportunity, index) => (
                <div key={index} className="border border-gray-200 rounded-xl p-6 hover:border-emerald-300 hover:bg-emerald-50 transition-colors">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-semibold text-gray-900">{opportunity.action}</h4>
                    <span className="px-3 py-1 bg-emerald-100 text-emerald-800 text-sm rounded-full font-medium">
                      {opportunity.reward}
                    </span>
                  </div>
                  
                  <div className="mb-4">
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-gray-600">Progress</span>
                      <span className="text-gray-600">{opportunity.progress} / {opportunity.max_progress}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-emerald-500 h-2 rounded-full"
                        style={{ width: `${Math.min((opportunity.progress / opportunity.max_progress) * 100, 100)}%` }}
                      />
                    </div>
                  </div>

                  {opportunity.progress >= opportunity.max_progress && (
                    <div className="flex items-center text-emerald-600">
                      <CheckCircleIcon className="w-5 h-5 mr-2" />
                      <span className="text-sm font-medium">Completed! Bonus awarded</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Beta Features Tab */}
      {activeTab === 'beta' && betaAccess && (
        <div className="space-y-8">
          {/* Criteria Overview */}
          <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-200">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Your Beta Access Status</h3>
            
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
              {Object.entries(betaAccess.qualification_tips).map(([criterion, tip]) => (
                <div key={criterion} className="text-center p-4 rounded-xl border border-gray-200">
                  {betaAccess.criteria_met.includes(criterion) ? (
                    <CheckCircleIcon className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                  ) : (
                    <ClockIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  )}
                  <h4 className="font-medium text-sm text-gray-900 mb-1">
                    {criterion.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </h4>
                  <p className="text-xs text-gray-600">{tip}</p>
                </div>
              ))}
            </div>

            <div className="text-center p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-200">
              <div className="flex items-center justify-center space-x-2 mb-2">
                <SparklesIcon className="w-6 h-6 text-purple-600" />
                <span className="text-2xl font-bold text-purple-900">{betaAccess.total_criteria}</span>
                <span className="text-purple-700">/ 6 criteria met</span>
              </div>
              <p className="text-sm text-purple-700">
                {betaAccess.total_criteria >= 4 
                  ? "Excellent! You qualify for premium beta features" 
                  : "Complete more achievements to unlock beta features"}
              </p>
            </div>
          </div>

          {/* Available Beta Features */}
          <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-200">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Beta Features</h3>
            
            <div className="space-y-6">
              {betaAccess.beta_features.map((feature, index) => (
                <div 
                  key={feature.feature_id}
                  className={`border rounded-xl p-6 ${
                    feature.has_access 
                      ? 'border-emerald-200 bg-emerald-50' 
                      : feature.eligible
                      ? 'border-blue-200 bg-blue-50'
                      : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${
                        feature.has_access 
                          ? 'bg-emerald-500 text-white' 
                          : feature.eligible
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-400 text-white'
                      }`}>
                        {feature.feature_id === 'ai_insights_v2' && <LightBulbIcon className="w-5 h-5" />}
                        {feature.feature_id === 'social_investing' && <UserPlusIcon className="w-5 h-5" />}
                        {feature.feature_id === 'premium_budgeting' && <ChartBarIcon className="w-5 h-5" />}
                        {feature.feature_id === 'exclusive_challenges' && <RocketLaunchIcon className="w-5 h-5" />}
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900">{feature.feature_info.name}</h4>
                        <p className="text-sm text-gray-600">{feature.feature_info.description}</p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      {feature.has_access ? (
                        <div>
                          <span className="px-3 py-1 bg-emerald-100 text-emerald-800 text-sm rounded-full font-medium mb-2 block">
                            Active
                          </span>
                          {feature.expires_at && (
                            <p className="text-xs text-gray-600">
                              Expires: {new Date(feature.expires_at).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      ) : feature.eligible ? (
                        <button
                          onClick={() => requestBetaAccess(feature.feature_id)}
                          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
                        >
                          Get Access
                        </button>
                      ) : (
                        <div>
                          <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full font-medium mb-2 block">
                            Locked
                          </span>
                          <p className="text-xs text-gray-600">
                            Missing: {feature.missing_criteria.join(', ')}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                      Expires in {feature.feature_info.expires_in_days} days
                    </span>
                    {feature.feature_info.required_criteria.map((criterion, idx) => (
                      <span 
                        key={idx} 
                        className={`px-2 py-1 text-xs rounded ${
                          betaAccess.criteria_met.includes(criterion)
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {criterion.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Waitlist Tab */}
      {activeTab === 'waitlist' && (
        <div className="space-y-8">
          <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-200">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Exclusive Feature Waitlist</h3>
            
            <p className="text-gray-600 mb-8">
              Join the waitlist for upcoming premium features. Your position is determined by your activity and engagement.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                {
                  id: 'ai_financial_advisor',
                  name: 'AI Financial Advisor',
                  description: 'Personal AI coach for financial decisions',
                  capacity: 100,
                  icon: LightBulbIcon,
                  color: 'emerald'
                },
                {
                  id: 'premium_analytics',
                  name: 'Premium Analytics Dashboard',
                  description: 'Advanced spending insights and predictions',
                  capacity: 200,
                  icon: ChartBarIcon,
                  color: 'blue'
                },
                {
                  id: 'investment_tracker',
                  name: 'Investment Portfolio Tracker',
                  description: 'Track stocks, mutual funds, and crypto',
                  capacity: 150,
                  icon: CubeIcon,
                  color: 'purple'
                },
                {
                  id: 'group_goals',
                  name: 'Collaborative Financial Goals',
                  description: 'Set and achieve goals with friends',
                  capacity: 300,
                  icon: UserPlusIcon,
                  color: 'orange'
                },
                {
                  id: 'merchant_partnerships',
                  name: 'Exclusive Merchant Discounts',
                  description: 'Special discounts at partner stores',
                  capacity: 500,
                  icon: GiftIcon,
                  color: 'pink'
                }
              ].map((feature) => (
                <div key={feature.id} className="border border-gray-200 rounded-xl p-6 hover:border-gray-300 transition-colors">
                  <div className="flex items-start space-x-4">
                    <div className={`p-3 bg-${feature.color}-100 rounded-lg`}>
                      <feature.icon className={`w-6 h-6 text-${feature.color}-600`} />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-2">{feature.name}</h4>
                      <p className="text-sm text-gray-600 mb-4">{feature.description}</p>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500">
                          Limited to {feature.capacity} users
                        </span>
                        <button
                          onClick={() => joinWaitlist(feature.id)}
                          className={`px-4 py-2 bg-${feature.color}-500 text-white rounded-lg hover:bg-${feature.color}-600 transition-colors text-sm`}
                        >
                          Join Waitlist
                        </button>
                      </div>
                    </div>
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

export default GrowthMechanics;
