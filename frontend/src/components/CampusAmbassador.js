import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import {
  TrophyIcon,
  UserGroupIcon,
  ChartBarIcon,
  StarIcon,
  GiftIcon,
  AcademicCapIcon,
  SparklesIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CampusAmbassador = () => {
  const [ambassadorData, setAmbassadorData] = useState(null);
  const [rewards, setRewards] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [applicationData, setApplicationData] = useState({
    motivation: '',
    social_media_experience: '',
    current_followers: 0,
    leadership_experience: '',
    availability_hours: 5
  });
  const [showApplication, setShowApplication] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    fetchAmbassadorData();
  }, []);

  const fetchAmbassadorData = async () => {
    try {
      const response = await axios.get(`${API}/campus/ambassador/dashboard`);
      setAmbassadorData(response.data);
      
      const rewardsResponse = await axios.get(`${API}/campus/ambassador/rewards`);
      setRewards(rewardsResponse.data);
    } catch (error) {
      if (error.response?.status === 403) {
        // User is not an ambassador, show application form
        setShowApplication(true);
      }
      console.error('Error fetching ambassador data:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitApplication = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/campus/ambassador/apply`, applicationData);
      
      alert('Application submitted successfully! You will be notified once reviewed.');
      setShowApplication(false);
      fetchAmbassadorData();
    } catch (error) {
      console.error('Error submitting application:', error);
      alert(error.response?.data?.detail || 'Failed to submit application');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <SparklesIcon className="w-8 h-8 text-emerald-500 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600">Loading ambassador dashboard...</p>
        </div>
      </div>
    );
  }

  // Application Form for Non-Ambassadors
  if (showApplication) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <div className="p-4 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-full inline-block mb-4">
              <AcademicCapIcon className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Become a Campus Ambassador</h1>
            <p className="text-gray-600">Lead the financial revolution at your university</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="text-center p-4 bg-emerald-50 rounded-xl">
              <UserGroupIcon className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
              <h3 className="font-semibold text-gray-900">Build Community</h3>
              <p className="text-sm text-gray-600">Help students achieve financial goals</p>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-xl">
              <GiftIcon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <h3 className="font-semibold text-gray-900">Exclusive Rewards</h3>
              <p className="text-sm text-gray-600">Unlimited invites & beta access</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-xl">
              <TrophyIcon className="w-8 h-8 text-purple-600 mx-auto mb-2" />
              <h3 className="font-semibold text-gray-900">Recognition</h3>
              <p className="text-sm text-gray-600">Leadership & achievement badges</p>
            </div>
          </div>

          <form className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Why do you want to be a campus ambassador?
              </label>
              <textarea
                value={applicationData.motivation}
                onChange={(e) => setApplicationData({...applicationData, motivation: e.target.value})}
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="Share your motivation and vision for helping fellow students..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Social Media Experience
              </label>
              <textarea
                value={applicationData.social_media_experience}
                onChange={(e) => setApplicationData({...applicationData, social_media_experience: e.target.value})}
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="Describe your experience with social media marketing, content creation, etc."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Social Media Followers (Total)
                </label>
                <input
                  type="number"
                  value={applicationData.current_followers}
                  onChange={(e) => setApplicationData({...applicationData, current_followers: parseInt(e.target.value) || 0})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Weekly Availability (Hours)
                </label>
                <select
                  value={applicationData.availability_hours}
                  onChange={(e) => setApplicationData({...applicationData, availability_hours: parseInt(e.target.value)})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value={5}>5-10 hours</option>
                  <option value={10}>10-15 hours</option>
                  <option value={15}>15-20 hours</option>
                  <option value={20}>20+ hours</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Leadership Experience
              </label>
              <textarea
                value={applicationData.leadership_experience}
                onChange={(e) => setApplicationData({...applicationData, leadership_experience: e.target.value})}
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="Any leadership roles, club activities, volunteer work, etc."
              />
            </div>

            <div className="flex items-center justify-center space-x-4 pt-6">
              <button
                type="button"
                onClick={() => setShowApplication(false)}
                className="px-6 py-3 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={submitApplication}
                disabled={!applicationData.motivation.trim()}
                className="px-8 py-3 bg-gradient-to-r from-emerald-500 to-blue-500 text-white rounded-lg hover:from-emerald-600 hover:to-blue-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Submit Application
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // Ambassador Dashboard
  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Campus Ambassador Dashboard</h1>
            <p className="text-gray-600 mt-1">Leading financial literacy at {ambassadorData?.ambassador_info?.university}</p>
          </div>
          <div className="flex items-center space-x-3">
            <div className="px-4 py-2 bg-emerald-100 text-emerald-800 rounded-full text-sm font-medium">
              {rewards?.current_tier || 'New Ambassador'}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="flex space-x-8">
          {['dashboard', 'performance', 'rewards'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-emerald-500 text-emerald-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && (
        <div className="space-y-8">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-2xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-emerald-100 text-sm">Total Referrals</p>
                  <p className="text-3xl font-bold">{ambassadorData?.referral_stats?.total_referrals || 0}</p>
                </div>
                <UserGroupIcon className="w-8 h-8 text-emerald-200" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm">This Month</p>
                  <p className="text-3xl font-bold">{ambassadorData?.referral_stats?.monthly_referrals || 0}</p>
                </div>
                <ChartBarIcon className="w-8 h-8 text-blue-200" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-2xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">University Rank</p>
                  <p className="text-3xl font-bold">#{ambassadorData?.performance?.university_rank || 'N/A'}</p>
                </div>
                <TrophyIcon className="w-8 h-8 text-purple-200" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-orange-100 text-sm">Monthly Earnings</p>
                  <p className="text-3xl font-bold">₹{ambassadorData?.referral_stats?.earnings_this_month || 0}</p>
                </div>
                <GiftIcon className="w-8 h-8 text-orange-200" />
              </div>
            </div>
          </div>

          {/* Performance Progress */}
          <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-200">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Monthly Progress</h3>
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Referrals Target (10)</span>
                <span className="text-sm text-gray-600">
                  {ambassadorData?.referral_stats?.monthly_referrals || 0} / 10
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-emerald-500 to-emerald-600 h-2 rounded-full"
                  style={{ width: `${Math.min((ambassadorData?.performance?.monthly_progress || 0), 100)}%` }}
                />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Special Features</h4>
                <div className="space-y-2">
                  {Object.entries(ambassadorData?.special_features || {}).map(([feature, enabled]) => (
                    <div key={feature} className="flex items-center space-x-2">
                      {enabled ? (
                        <CheckCircleIcon className="w-5 h-5 text-emerald-500" />
                      ) : (
                        <XCircleIcon className="w-5 h-5 text-gray-400" />
                      )}
                      <span className={`text-sm ${enabled ? 'text-gray-900' : 'text-gray-500'}`}>
                        {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-3">University Leaderboard</h4>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {ambassadorData?.monthly_leaderboard?.slice(0, 5).map((ambassador, index) => (
                    <div 
                      key={index}
                      className={`flex items-center justify-between p-2 rounded-lg ${
                        ambassador.is_you ? 'bg-emerald-50 border border-emerald-200' : 'bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          index === 0 ? 'bg-yellow-400 text-yellow-900' :
                          index === 1 ? 'bg-gray-300 text-gray-700' :
                          index === 2 ? 'bg-orange-400 text-orange-900' :
                          'bg-gray-200 text-gray-600'
                        }`}>
                          {index + 1}
                        </span>
                        <span className={`text-sm ${ambassador.is_you ? 'font-semibold text-emerald-900' : 'text-gray-700'}`}>
                          {ambassador.is_you ? 'You' : ambassador.name}
                        </span>
                      </div>
                      <span className="text-sm text-gray-600">{ambassador.referrals} referrals</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <div className="space-y-8">
          <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-200">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Performance Analytics</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-6 bg-gradient-to-b from-emerald-50 to-emerald-100 rounded-xl">
                <div className="w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-white">
                    {Math.round(ambassadorData?.performance?.score || 0)}
                  </span>
                </div>
                <h4 className="font-semibold text-gray-900">Performance Score</h4>
                <p className="text-sm text-gray-600">Overall rating</p>
              </div>

              <div className="text-center p-6 bg-gradient-to-b from-blue-50 to-blue-100 rounded-xl">
                <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-white">
                    {ambassadorData?.referral_stats?.conversion_rate || 85}%
                  </span>
                </div>
                <h4 className="font-semibold text-gray-900">Conversion Rate</h4>
                <p className="text-sm text-gray-600">Referral success</p>
              </div>

              <div className="text-center p-6 bg-gradient-to-b from-purple-50 to-purple-100 rounded-xl">
                <div className="w-16 h-16 bg-purple-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-lg font-bold text-white">
                    #{ambassadorData?.performance?.university_rank}
                  </span>
                </div>
                <h4 className="font-semibold text-gray-900">Campus Rank</h4>
                <p className="text-sm text-gray-600">Out of {ambassadorData?.performance?.total_ambassadors}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Rewards Tab */}
      {activeTab === 'rewards' && (
        <div className="space-y-8">
          <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-200">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Reward Tiers & Achievements</h3>
            
            <div className="space-y-6">
              {rewards?.reward_tiers?.map((tier, index) => (
                <div 
                  key={tier.tier}
                  className={`border rounded-xl p-6 ${
                    tier.unlocked 
                      ? 'border-emerald-200 bg-emerald-50' 
                      : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      {tier.unlocked ? (
                        <CheckCircleIcon className="w-6 h-6 text-emerald-500" />
                      ) : (
                        <ClockIcon className="w-6 h-6 text-gray-400" />
                      )}
                      <h4 className="font-semibold text-gray-900">{tier.tier}</h4>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      tier.unlocked 
                        ? 'bg-emerald-100 text-emerald-800' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {tier.unlocked ? 'Unlocked' : 'Locked'}
                    </span>
                  </div>

                  <p className="text-gray-600 mb-4">{tier.requirement}</p>

                  <div className="mb-4">
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span>Progress</span>
                      <span>{tier.current_progress} / {tier.target}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          tier.unlocked ? 'bg-emerald-500' : 'bg-blue-500'
                        }`}
                        style={{ width: `${Math.min((tier.current_progress / tier.target) * 100, 100)}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {tier.rewards.map((reward, idx) => (
                      <span key={idx} className="px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full">
                        {reward}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Achievements */}
            <div className="mt-8">
              <h4 className="font-semibold text-gray-900 mb-4">Your Achievements</h4>
              <div className="flex flex-wrap gap-3">
                {rewards?.achievements_earned?.map((achievement, index) => (
                  <div key={index} className="flex items-center space-x-2 px-4 py-2 bg-yellow-100 text-yellow-800 rounded-full">
                    <StarIcon className="w-4 h-4" />
                    <span className="text-sm font-medium">{achievement}</span>
                  </div>
                ))}
                {(!rewards?.achievements_earned || rewards.achievements_earned.length === 0) && (
                  <p className="text-gray-600 italic">No achievements yet. Start referring friends to earn your first badge!</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CampusAmbassador;
