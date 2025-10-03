import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import {
  TrophyIcon,
  StarIcon,
  FireIcon,
  SparklesIcon,
  XMarkIcon,
  ShareIcon
} from '@heroicons/react/24/outline';
import SocialSharing from './SocialSharing';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MilestoneCelebration = ({ milestone, onClose }) => {
  const [showSocialSharing, setShowSocialSharing] = useState(false);
  const { user } = useAuth();

  if (!milestone) return null;

  const getMilestoneIcon = (type) => {
    switch (type) {
      case 'savings': return '💰';
      case 'streak': return '🔥';
      case 'budget': return '📊';
      case 'goal': return '🎯';
      default: return '🏆';
    }
  };

  const getMilestoneColor = (type) => {
    switch (type) {
      case 'savings': return 'from-emerald-500 to-green-600';
      case 'streak': return 'from-orange-500 to-red-600';
      case 'budget': return 'from-blue-500 to-indigo-600';
      case 'goal': return 'from-purple-500 to-pink-600';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  const handleShare = () => {
    setShowSocialSharing(true);
  };

  const formatAmount = (amount) => {
    if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`;
    if (amount >= 1000) return `₹${(amount / 1000).toFixed(1)}K`;
    return `₹${amount}`;
  };

  return (
    <>
      {/* Celebration Modal */}
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-3xl max-w-md w-full overflow-hidden shadow-2xl">
          {/* Celebration Animation Background */}
          <div className={`bg-gradient-to-r ${getMilestoneColor(milestone.type)} p-8 relative overflow-hidden`}>
            {/* Floating Confetti */}
            <div className="absolute inset-0">
              {[...Array(15)].map((_, i) => (
                <div
                  key={i}
                  className="absolute animate-bounce"
                  style={{
                    left: `${Math.random() * 100}%`,
                    top: `${Math.random() * 100}%`,
                    animationDelay: `${Math.random() * 2}s`,
                    animationDuration: `${2 + Math.random() * 2}s`
                  }}
                >
                  <span className="text-white text-opacity-80">
                    {['✨', '🎉', '⭐', '💫', '🎊'][Math.floor(Math.random() * 5)]}
                  </span>
                </div>
              ))}
            </div>
            
            {/* Close Button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 text-white text-opacity-80 hover:text-opacity-100 transition-all"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
            
            {/* Milestone Icon */}
            <div className="text-center relative z-10">
              <div className="text-8xl mb-4 animate-pulse">
                {getMilestoneIcon(milestone.type)}
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">
                Milestone Achieved!
              </h2>
              <p className="text-white text-opacity-90 text-lg">
                {milestone.title}
              </p>
            </div>
          </div>
          
          {/* Content */}
          <div className="p-6 text-center">
            <div className="mb-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {milestone.message}
              </h3>
              
              {milestone.amount && (
                <div className="text-3xl font-bold text-emerald-600 mb-3">
                  {formatAmount(milestone.amount)}
                </div>
              )}
              
              {milestone.stats && (
                <div className="grid grid-cols-2 gap-4 mb-4">
                  {Object.entries(milestone.stats).map(([key, value]) => (
                    <div key={key} className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-600 capitalize">
                        {key.replace('_', ' ')}
                      </div>
                      <div className="font-semibold text-gray-900">{value}</div>
                    </div>
                  ))}
                </div>
              )}
              
              <p className="text-gray-600 mb-6">
                {milestone.description}
              </p>
            </div>
            
            {/* Action Buttons */}
            <div className="flex space-x-3">
              <button
                onClick={handleShare}
                className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 px-4 rounded-xl font-semibold hover:from-purple-600 hover:to-pink-600 transition-all flex items-center justify-center space-x-2"
              >
                <ShareIcon className="w-5 h-5" />
                <span>Share Success</span>
              </button>
              
              <button
                onClick={onClose}
                className="flex-1 bg-gray-100 text-gray-700 py-3 px-4 rounded-xl font-semibold hover:bg-gray-200 transition-colors"
              >
                Continue
              </button>
            </div>
          </div>
          
          {/* EarnAura Branding */}
          <div className="bg-gray-50 px-6 py-3 text-center">
            <p className="text-sm text-gray-600">
              Keep crushing your goals with <span className="font-semibold text-emerald-600">EarnAura</span>! 💪
            </p>
          </div>
        </div>
      </div>
      
      {/* Social Sharing Modal */}
      {showSocialSharing && (
        <SocialSharing 
          achievement={{
            title: milestone.title,
            description: milestone.message,
            type: `${milestone.type}_milestone`,
            amount: milestone.amount
          }}
          onClose={() => setShowSocialSharing(false)}
        />
      )}
    </>
  );
};

export default MilestoneCelebration;
