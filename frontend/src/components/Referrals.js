import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import {
  ShareIcon,
  CurrencyRupeeIcon,
  UsersIcon,
  GiftIcon,
  ClipboardIcon,
  CheckIcon,
  ArrowUpIcon,
  CalendarIcon,
  TrophyIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Referrals = () => {
  const [referralData, setReferralData] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copying, setCopying] = useState(false);
  const [copied, setCopied] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    fetchReferralData();
  }, []);

  const fetchReferralData = async () => {
    try {
      const [linkResponse, statsResponse] = await Promise.all([
        axios.get(`${API}/referrals/my-link`),
        axios.get(`${API}/referrals/stats`)
      ]);

      setReferralData(linkResponse.data);
      setStats(statsResponse.data);
    } catch (error) {
      console.error('Error fetching referral data:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyReferralLink = async () => {
    if (!referralData?.referral_link) return;
    
    setCopying(true);
    try {
      await navigator.clipboard.writeText(referralData.referral_link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = referralData.referral_link;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } finally {
      setCopying(false);
    }
  };

  const shareViaWhatsApp = () => {
    const message = `Hey! I've been using EarnNest to manage my finances and earn money from side hustles. It's really helpful for students! 🎯💰\n\nJoin using my link and we both get rewards: ${referralData.referral_link}`;
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
  };

  const shareViaTwitter = () => {
    const message = `Managing money as a student just got easier with @EarnNest! 🎯💰 Join me and let's earn together!`;
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(message)}&url=${encodeURIComponent(referralData.referral_link)}`;
    window.open(twitterUrl, '_blank');
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="h-64 bg-gray-200 rounded-xl"></div>
            <div className="h-64 bg-gray-200 rounded-xl"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center mb-4">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
            <GiftIcon className="w-8 h-8 text-white" />
          </div>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Refer Friends & Earn Money! 💰
        </h1>
        <p className="text-lg text-gray-600 mb-4">
          Invite friends to EarnNest and earn real cash rewards when they stay active
        </p>
      </div>

      {/* Earnings Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <CurrencyRupeeIcon className="w-8 h-8 text-green-500" />
            <span className="text-2xl font-bold text-gray-900">
              ₹{referralData?.total_earnings?.toLocaleString() || 0}
            </span>
          </div>
          <h3 className="font-semibold text-gray-700">Total Earned</h3>
          <p className="text-sm text-gray-500">All-time earnings</p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <SparklesIcon className="w-8 h-8 text-yellow-500" />
            <span className="text-2xl font-bold text-gray-900">
              ₹{referralData?.pending_earnings?.toLocaleString() || 0}
            </span>
          </div>
          <h3 className="font-semibold text-gray-700">Pending Earnings</h3>
          <p className="text-sm text-gray-500">Being processed</p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <UsersIcon className="w-8 h-8 text-blue-500" />
            <span className="text-2xl font-bold text-gray-900">
              {stats?.successful_referrals || 0}
            </span>
          </div>
          <h3 className="font-semibold text-gray-700">Active Referrals</h3>
          <p className="text-sm text-gray-500">Friends using EarnNest</p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <TrophyIcon className="w-8 h-8 text-purple-500" />
            <span className="text-2xl font-bold text-gray-900">
              {stats?.conversion_rate || 0}%
            </span>
          </div>
          <h3 className="font-semibold text-gray-700">Success Rate</h3>
          <p className="text-sm text-gray-500">Conversion rate</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Referral Link Section */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Your Referral Link</h2>
            <ShareIcon className="w-6 h-6 text-gray-500" />
          </div>

          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-600 mb-2">Share this link with friends:</p>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={referralData?.referral_link || ''}
                readOnly
                className="flex-1 bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm"
              />
              <button
                onClick={copyReferralLink}
                disabled={copying}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2 ${
                  copied
                    ? 'bg-green-500 text-white'
                    : 'bg-emerald-500 text-white hover:bg-emerald-600'
                }`}
              >
                {copied ? (
                  <>
                    <CheckIcon className="w-4 h-4" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <ClipboardIcon className="w-4 h-4" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Share Buttons */}
          <div className="space-y-3">
            <h3 className="font-semibold text-gray-700 mb-3">Share on Social Media:</h3>
            
            <button
              onClick={shareViaWhatsApp}
              className="w-full flex items-center justify-center space-x-2 bg-green-500 text-white py-3 px-4 rounded-lg hover:bg-green-600 transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893A11.821 11.821 0 0020.885 3.488"/>
              </svg>
              <span>Share on WhatsApp</span>
            </button>

            <button
              onClick={shareViaTwitter}
              className="w-full flex items-center justify-center space-x-2 bg-blue-500 text-white py-3 px-4 rounded-lg hover:bg-blue-600 transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
              </svg>
              <span>Share on Twitter</span>
            </button>
          </div>
        </div>

        {/* Earnings Breakdown */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">How You Earn</h2>

          <div className="space-y-4">
            <div className="flex items-center space-x-4 p-4 bg-green-50 rounded-lg">
              <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">₹50</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Friend Signs Up</h3>
                <p className="text-sm text-gray-600">Instant reward when someone registers using your link</p>
              </div>
            </div>

            <div className="flex items-center space-x-4 p-4 bg-blue-50 rounded-lg">
              <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">₹200</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">30-Day Activity Bonus</h3>
                <p className="text-sm text-gray-600">When your friend stays active for 30 days</p>
              </div>
            </div>

            <div className="flex items-center space-x-4 p-4 bg-purple-50 rounded-lg">
              <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">₹500</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Milestone Bonus</h3>
                <p className="text-sm text-gray-600">Extra rewards for every 5 successful referrals</p>
              </div>
            </div>
          </div>

          {/* Recent Referrals */}
          {stats?.recent_referrals?.length > 0 && (
            <div className="mt-6">
              <h3 className="font-semibold text-gray-900 mb-4">Recent Successful Referrals</h3>
              <div className="space-y-2">
                {stats.recent_referrals.slice(0, 3).map((referral, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900">{referral.user_name}</div>
                      <div className="text-sm text-gray-500">
                        Joined {new Date(referral.joined_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="text-green-600 font-bold">
                      +₹{referral.earnings}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Call to Action */}
      <div className="mt-8 bg-gradient-to-r from-emerald-500 to-green-600 rounded-xl p-6 text-center text-white">
        <h3 className="text-2xl font-bold mb-2">Start Earning Today!</h3>
        <p className="text-emerald-100 mb-4">
          Share your link with friends and family. The more people you refer, the more you earn!
        </p>
        <button
          onClick={copyReferralLink}
          className="bg-white text-emerald-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
        >
          Copy My Referral Link
        </button>
      </div>
    </div>
  );
};

export default Referrals;
