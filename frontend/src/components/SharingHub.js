import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SharingHub = () => {
  const [activeTab, setActiveTab] = useState('linkedin');
  const [shareContent, setShareContent] = useState(null);
  const [multiPlatformContent, setMultiPlatformContent] = useState(null);
  const [viralLink, setViralLink] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateLinkedInPost = async (achievementType, details) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/sharing/linkedin-post`,
        {
          achievement_type: achievementType,
          details: details
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setShareContent(response.data);
    } catch (error) {
      console.error('LinkedIn post generation error:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateMultiPlatform = async (achievementData, platforms) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/sharing/multi-platform`,
        {
          achievement: achievementData,
          platforms: platforms
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setMultiPlatformContent(response.data);
    } catch (error) {
      console.error('Multi-platform sharing error:', error);
    } finally {
      setLoading(false);
    }
  };

  const createViralLink = async (campaignType, customMessage) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/sharing/create-viral-link`,
        {
          campaign_type: campaignType,
          custom_message: customMessage
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setViralLink(response.data);
    } catch (error) {
      console.error('Viral link creation error:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard! 📋');
  };

  const handleQuickShare = (type) => {
    switch (type) {
      case 'savings_milestone':
        generateLinkedInPost('savings_milestone', { amount: 5000 });
        break;
      case 'streak_achievement':
        generateLinkedInPost('streak_achievement', { days: 30 });
        break;
      case 'income_milestone':
        generateLinkedInPost('income_milestone', { amount: 10000 });
        break;
    }
  };

  const handleMultiPlatformShare = () => {
    generateMultiPlatform(
      {
        type: 'milestone',
        amount: 5000,
        message: 'Just hit my savings goal!'
      },
      ['instagram', 'whatsapp', 'twitter', 'facebook']
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            📱 Sharing Hub
          </h2>
          <p className="text-gray-600 mt-2">Share your achievements and inspire others!</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'linkedin', name: 'LinkedIn Posts', icon: '💼' },
              { id: 'multiplatform', name: 'Multi-Platform', icon: '🌐' },
              { id: 'viral', name: 'Viral Links', icon: '🚀' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-2 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.icon} {tab.name}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* LinkedIn Tab */}
          {activeTab === 'linkedin' && (
            <div className="space-y-6">
              <div className="grid md:grid-cols-3 gap-4">
                <button
                  onClick={() => handleQuickShare('savings_milestone')}
                  className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-400 hover:bg-green-50 transition-all"
                >
                  <div className="text-2xl mb-2">💰</div>
                  <div className="font-medium text-gray-900">Savings Milestone</div>
                  <div className="text-sm text-gray-500">Share your savings achievement</div>
                </button>

                <button
                  onClick={() => handleQuickShare('streak_achievement')}
                  className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all"
                >
                  <div className="text-2xl mb-2">🔥</div>
                  <div className="font-medium text-gray-900">Streak Achievement</div>
                  <div className="text-sm text-gray-500">Show your consistency</div>
                </button>

                <button
                  onClick={() => handleQuickShare('income_milestone')}
                  className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-all"
                >
                  <div className="text-2xl mb-2">🚀</div>
                  <div className="font-medium text-gray-900">Income Milestone</div>
                  <div className="text-sm text-gray-500">Share your earning success</div>
                </button>
              </div>

              {shareContent && (
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-bold text-gray-900">LinkedIn Post Ready!</h3>
                    <button
                      onClick={() => copyToClipboard(shareContent.post_content)}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Copy Post
                    </button>
                  </div>
                  <div className="bg-white rounded-lg p-4 border">
                    <div className="whitespace-pre-line text-gray-800 mb-4">
                      {shareContent.post_content}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {shareContent.hashtags.map((hashtag, index) => (
                        <span key={index} className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm">
                          {hashtag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="mt-4 bg-blue-50 rounded-lg p-3">
                    <p className="text-blue-800 text-sm">💡 {shareContent.engagement_tip}</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Multi-Platform Tab */}
          {activeTab === 'multiplatform' && (
            <div className="space-y-6">
              <div className="text-center">
                <button
                  onClick={handleMultiPlatformShare}
                  disabled={loading}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold py-3 px-8 rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50"
                >
                  {loading ? 'Generating...' : '🌐 Generate Multi-Platform Content'}
                </button>
                <p className="text-gray-500 text-sm mt-2">Create content for all major platforms at once</p>
              </div>

              {multiPlatformContent && (
                <div className="grid md:grid-cols-2 gap-6">
                  {Object.entries(multiPlatformContent.platforms).map(([platform, content]) => (
                    <div key={platform} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex justify-between items-center mb-3">
                        <h3 className="font-bold text-gray-900 capitalize flex items-center">
                          {platform === 'instagram' && '📷'}
                          {platform === 'whatsapp' && '💬'}
                          {platform === 'twitter' && '🐦'}
                          {platform === 'facebook' && '👥'}
                          <span className="ml-2">{platform}</span>
                        </h3>
                        <button
                          onClick={() => copyToClipboard(content.message || content.caption || content.tweet || content.post)}
                          className="text-sm bg-white border border-gray-300 px-3 py-1 rounded hover:bg-gray-100"
                        >
                          Copy
                        </button>
                      </div>
                      <div className="bg-white rounded p-3 text-sm">
                        {content.message || content.caption || content.tweet || content.post}
                      </div>
                      <p className="text-xs text-gray-500 mt-2">{content.instructions}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Viral Links Tab */}
          {activeTab === 'viral' && (
            <div className="space-y-6">
              <div className="grid md:grid-cols-3 gap-4">
                <button
                  onClick={() => createViralLink('achievement_viral', '')}
                  className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-400 hover:bg-green-50 transition-all"
                >
                  <div className="text-2xl mb-2">🎯</div>
                  <div className="font-medium text-gray-900">Achievement Share</div>
                  <div className="text-sm text-gray-500">Share your success story</div>
                </button>

                <button
                  onClick={() => createViralLink('challenge_viral', '')}
                  className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all"
                >
                  <div className="text-2xl mb-2">🏆</div>
                  <div className="font-medium text-gray-900">Challenge Invite</div>
                  <div className="text-sm text-gray-500">Invite friends to compete</div>
                </button>

                <button
                  onClick={() => createViralLink('milestone_viral', '')}
                  className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-all"
                >
                  <div className="text-2xl mb-2">📊</div>
                  <div className="font-medium text-gray-900">Milestone Story</div>
                  <div className="text-sm text-gray-500">Share your journey</div>
                </button>
              </div>

              {viralLink && (
                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">Viral Link Created! 🚀</h3>
                  
                  <div className="bg-white rounded-lg p-4 border mb-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-sm font-medium text-gray-700">Tracking Link:</span>
                      <button
                        onClick={() => copyToClipboard(viralLink.referral_url)}
                        className="text-green-600 hover:text-green-700 text-sm font-medium"
                      >
                        📋 Copy Link
                      </button>
                    </div>
                    <div className="bg-gray-100 rounded p-2 text-sm font-mono text-gray-800 break-all">
                      {viralLink.referral_url}
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-4 border">
                    <h4 className="font-medium text-gray-900 mb-2">{viralLink.sharing_template.title}</h4>
                    <div className="text-sm text-gray-700 whitespace-pre-line mb-3">
                      {viralLink.sharing_template.message}
                    </div>
                    <div className="flex items-center space-x-4 text-xs">
                      <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full">
                        {viralLink.sharing_template.urgency}
                      </span>
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full">
                        {viralLink.sharing_template.incentive}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 bg-yellow-50 rounded-lg p-3">
                    <h5 className="font-medium text-yellow-800 mb-2">🔥 Viral Tips:</h5>
                    <ul className="text-sm text-yellow-700 space-y-1">
                      {viralLink.viral_tips.map((tip, index) => (
                        <li key={index}>• {tip}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SharingHub;
