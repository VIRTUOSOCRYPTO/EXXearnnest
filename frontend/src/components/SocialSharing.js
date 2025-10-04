import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import {
  ShareIcon,
  PhotoIcon,
  SparklesIcon,
  XMarkIcon,
  CheckCircleIcon,
  ClipboardDocumentIcon,
  LinkIcon,
  ChartBarIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SocialSharing = ({ achievement, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [imageGenerated, setImageGenerated] = useState(false);
  const [imageUrl, setImageUrl] = useState(null);
  const [shareContent, setShareContent] = useState({});
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [copied, setCopied] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    if (achievement) {
      generateAchievementImage();
    }
  }, [achievement]);

  const generateAchievementImage = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/social/generate-achievement-image`, {
        achievement_type: achievement.type || 'badge_earned',
        milestone_text: achievement.title || achievement.milestone_text,
        amount: achievement.amount || null
      });

      setImageUrl(`${BACKEND_URL}${response.data.image_url}`);
      setImageGenerated(true);
    } catch (error) {
      console.error('Error generating achievement image:', error);
      alert('Failed to generate achievement image. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const generateShareContent = async (platform) => {
    try {
      const response = await axios.post(`${API}/social/share/${platform}`, {
        achievement_type: achievement.type || 'badge_earned',
        milestone_text: achievement.title || achievement.milestone_text,
        image_filename: imageUrl.split('/').pop(),
        amount: achievement.amount || null
      });

      setShareContent(response.data);
      setSelectedPlatform(platform);
    } catch (error) {
      console.error('Error generating share content:', error);
      alert('Failed to generate share content. Please try again.');
    }
  };

  const handleInstagramShare = async () => {
    await generateShareContent('instagram');
  };

  const handleWhatsAppShare = async () => {
    await generateShareContent('whatsapp');
    
    // Open WhatsApp share URL if available
    if (shareContent.share_url) {
      window.open(shareContent.share_url, '_blank');
    }
  };

  const handleLinkedInShare = async () => {
    await generateShareContent('linkedin');
  };

  const handleTwitterShare = async () => {
    await generateShareContent('twitter');
  };

  const handleFacebookShare = async () => {
    await generateShareContent('facebook');
  };

  const handleMultiPlatformShare = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/social/multi-platform-share`, {
        achievement_type: achievement.type || 'badge_earned',
        milestone_text: achievement.title || achievement.milestone_text,
        amount: achievement.amount || null
      });

      setShareContent(response.data);
      setSelectedPlatform('multi-platform');
    } catch (error) {
      console.error('Error generating multi-platform content:', error);
      alert('Failed to generate multi-platform content. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const createViralReferralLink = async (platform) => {
    try {
      const response = await axios.post(`${API}/social/viral-referral-link`, {
        platform_source: platform
      });
      
      return response.data;
    } catch (error) {
      console.error('Error creating viral referral link:', error);
      return null;
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy text:', error);
    }
  };

  const downloadImage = () => {
    if (imageUrl) {
      const link = document.createElement('a');
      link.href = imageUrl;
      link.download = `achievement-${Date.now()}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg">
              <ShareIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Share Achievement</h2>
              <p className="text-sm text-gray-600">Celebrate your success with friends!</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Achievement Info */}
          <div className="mb-6 p-4 bg-gradient-to-r from-emerald-50 to-blue-50 rounded-xl border border-emerald-200">
            <h3 className="font-semibold text-gray-900 mb-1">{achievement.title}</h3>
            <p className="text-sm text-gray-600">{achievement.description}</p>
            {achievement.amount && (
              <p className="text-lg font-bold text-emerald-600 mt-2">₹{achievement.amount.toLocaleString()}</p>
            )}
          </div>

          {/* Image Preview */}
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
              <PhotoIcon className="w-5 h-5 mr-2" />
              Achievement Image
            </h4>
            
            {loading ? (
              <div className="bg-gray-100 rounded-xl p-8 text-center">
                <SparklesIcon className="w-8 h-8 text-gray-400 mx-auto mb-2 animate-spin" />
                <p className="text-gray-600">Creating your personalized achievement image...</p>
              </div>
            ) : imageGenerated && imageUrl ? (
              <div className="relative">
                <img 
                  src={imageUrl} 
                  alt="Achievement"
                  className="w-full max-w-md mx-auto rounded-xl shadow-lg"
                />
                <button
                  onClick={downloadImage}
                  className="absolute top-2 right-2 p-2 bg-white rounded-lg shadow-md hover:bg-gray-50 transition-colors"
                  title="Download image"
                >
                  <PhotoIcon className="w-5 h-5 text-gray-600" />
                </button>
              </div>
            ) : (
              <div className="bg-gray-100 rounded-xl p-8 text-center">
                <PhotoIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600">Failed to generate image</p>
                <button
                  onClick={generateAchievementImage}
                  className="mt-2 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors"
                >
                  Try Again
                </button>
              </div>
            )}
          </div>

          {/* Sharing Platforms */}
          {imageGenerated && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-gray-900">Share On</h4>
                <button
                  onClick={handleMultiPlatformShare}
                  className="flex items-center space-x-2 px-3 py-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all text-sm"
                >
                  <GlobeAltIcon className="w-4 h-4" />
                  <span>All Platforms</span>
                </button>
              </div>
              
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {/* Instagram */}
                <button
                  onClick={handleInstagramShare}
                  className="p-4 border border-gray-200 rounded-xl hover:border-purple-300 hover:bg-purple-50 transition-colors group"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-xs">IG</span>
                    </div>
                    <div className="text-left">
                      <p className="font-semibold text-gray-900 text-sm">Instagram</p>
                      <p className="text-xs text-gray-600">Share to Stories</p>
                    </div>
                  </div>
                </button>

                {/* WhatsApp */}
                <button
                  onClick={handleWhatsAppShare}
                  className="p-4 border border-gray-200 rounded-xl hover:border-green-300 hover:bg-green-50 transition-colors group"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-xs">WA</span>
                    </div>
                    <div className="text-left">
                      <p className="font-semibold text-gray-900 text-sm">WhatsApp</p>
                      <p className="text-xs text-gray-600">Share to Status</p>
                    </div>
                  </div>
                </button>

                {/* LinkedIn */}
                <button
                  onClick={handleLinkedInShare}
                  className="p-4 border border-gray-200 rounded-xl hover:border-blue-300 hover:bg-blue-50 transition-colors group"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-xs">Li</span>
                    </div>
                    <div className="text-left">
                      <p className="font-semibold text-gray-900 text-sm">LinkedIn</p>
                      <p className="text-xs text-gray-600">Professional</p>
                    </div>
                  </div>
                </button>

                {/* Twitter */}
                <button
                  onClick={handleTwitterShare}
                  className="p-4 border border-gray-200 rounded-xl hover:border-sky-300 hover:bg-sky-50 transition-colors group"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-sky-500 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-xs">X</span>
                    </div>
                    <div className="text-left">
                      <p className="font-semibold text-gray-900 text-sm">Twitter</p>
                      <p className="text-xs text-gray-600">Share Tweet</p>
                    </div>
                  </div>
                </button>

                {/* Facebook */}
                <button
                  onClick={handleFacebookShare}
                  className="p-4 border border-gray-200 rounded-xl hover:border-blue-300 hover:bg-blue-50 transition-colors group"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-700 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-xs">FB</span>
                    </div>
                    <div className="text-left">
                      <p className="font-semibold text-gray-900 text-sm">Facebook</p>
                      <p className="text-xs text-gray-600">Share Post</p>
                    </div>
                  </div>
                </button>

                {/* Viral Referral Link */}
                <button
                  onClick={async () => {
                    const viralLink = await createViralReferralLink('achievement_share');
                    if (viralLink) {
                      await copyToClipboard(viralLink.viral_link);
                      alert('Viral referral link copied! Share it anywhere to get credit for referrals.');
                    }
                  }}
                  className="p-4 border border-gray-200 rounded-xl hover:border-orange-300 hover:bg-orange-50 transition-colors group"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center">
                      <LinkIcon className="w-5 h-5 text-white" />
                    </div>
                    <div className="text-left">
                      <p className="font-semibold text-gray-900 text-sm">Viral Link</p>
                      <p className="text-xs text-gray-600">Trackable</p>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          )}

          {/* Share Content Display */}
          {selectedPlatform && shareContent && (
            <div className="border border-gray-200 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-gray-900 capitalize">
                  {selectedPlatform} Share Content
                </h4>
                {copied ? (
                  <div className="flex items-center text-green-600">
                    <CheckCircleIcon className="w-4 h-4 mr-1" />
                    <span className="text-sm">Copied!</span>
                  </div>
                ) : null}
              </div>
              
              {selectedPlatform === 'instagram' && (
                <div>
                  <div className="mb-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Caption Text (Copy this)
                    </label>
                    <div className="relative">
                      <textarea
                        value={shareContent.story_text || shareContent.text}
                        readOnly
                        className="w-full p-3 border border-gray-200 rounded-lg text-sm bg-gray-50 resize-none"
                        rows={4}
                      />
                      <button
                        onClick={() => copyToClipboard(shareContent.story_text || shareContent.text)}
                        className="absolute top-2 right-2 p-1 text-gray-500 hover:text-gray-700"
                      >
                        <ClipboardDocumentIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
                    <p className="font-medium mb-1">Instructions:</p>
                    <p>{shareContent.instructions || "Copy the text above, then share the image on your Instagram story with this caption."}</p>
                  </div>
                </div>
              )}

              {selectedPlatform === 'whatsapp' && (
                <div>
                  <p className="text-sm text-gray-600 mb-3">{shareContent.action_text}</p>
                  <div className="p-3 bg-gray-50 rounded-lg border text-sm">
                    {shareContent.text}
                  </div>
                  {shareContent.share_url && (
                    <button
                      onClick={() => window.open(shareContent.share_url, '_blank')}
                      className="mt-3 w-full py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                    >
                      Open WhatsApp to Share
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <p className="text-sm text-gray-600">
            Powered by <span className="font-semibold text-emerald-600">EarnAura</span>
          </p>
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default SocialSharing;
