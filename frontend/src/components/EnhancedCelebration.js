import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import SocialSharing from './SocialSharing';
import {
  TrophyIcon,
  StarIcon,
  FireIcon,
  SparklesIcon,
  XMarkIcon,
  ShareIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EnhancedCelebration = ({ celebration, onClose, onNext }) => {
  const [showSocialSharing, setShowSocialSharing] = useState(false);
  const [confettiElements, setConfettiElements] = useState([]);
  const [celebrationStep, setCelebrationStep] = useState('main'); // main, share, completed
  const { user } = useAuth();

  useEffect(() => {
    // Generate confetti elements for animation
    const confetti = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      emoji: ['🎉', '⭐', '💫', '✨', '🎊', '🥳', '🎈'][Math.floor(Math.random() * 7)],
      left: Math.random() * 100,
      animationDelay: Math.random() * 3,
      animationDuration: 2 + Math.random() * 3,
      size: 0.8 + Math.random() * 0.4
    }));
    setConfettiElements(confetti);

    // Play celebration sound (optional)
    if ('vibrate' in navigator) {
      navigator.vibrate([200, 100, 200]);
    }
  }, [celebration]);

  if (!celebration) return null;

  const getCelebrationType = (type) => {
    switch (type) {
      case 'streak_milestone':
      case 'streak':
        return {
          icon: '🔥',
          gradient: 'from-orange-500 via-red-500 to-pink-500',
          title: 'Streak Milestone!',
          subtitle: 'You\'re on fire!'
        };
      case 'badge_earned':
      case 'badge':
        return {
          icon: '🏆',
          gradient: 'from-yellow-500 via-amber-500 to-orange-500',
          title: 'Badge Earned!',
          subtitle: 'Achievement unlocked!'
        };
      case 'savings_milestone':
        return {
          icon: '💰',
          gradient: 'from-emerald-500 via-green-500 to-teal-500',
          title: 'Savings Milestone!',
          subtitle: 'Money master!'
        };
      case 'goal_completed':
        return {
          icon: '🎯',
          gradient: 'from-purple-500 via-violet-500 to-indigo-500',
          title: 'Goal Achieved!',
          subtitle: 'Dream realized!'
        };
      default:
        return {
          icon: celebration.icon || '🎉',
          gradient: 'from-blue-500 via-indigo-500 to-purple-500',
          title: celebration.title || 'Achievement Unlocked!',
          subtitle: 'Great job!'
        };
    }
  };

  const celebrationInfo = getCelebrationType(celebration.type || celebration.celebration_type);

  const handleShare = () => {
    const shareData = {
      title: celebration.title,
      description: celebration.message,
      type: celebration.type || 'achievement',
      icon: celebration.icon || celebrationInfo.icon,
      amount: celebration.data?.threshold || celebration.data?.points_earned
    };
    
    setShowSocialSharing(true);
  };

  const handleNext = () => {
    if (onNext) {
      onNext();
    } else {
      onClose();
    }
  };

  const handleSkip = () => {
    onClose();
  };

  if (showSocialSharing) {
    return (
      <SocialSharing
        achievement={{
          title: celebration.title,
          description: celebration.message,
          type: celebration.type || 'achievement',
          icon: celebration.icon || celebrationInfo.icon,
          amount: celebration.data?.threshold || celebration.data?.points_earned
        }}
        onClose={() => {
          setShowSocialSharing(false);
          setCelebrationStep('completed');
        }}
      />
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
      {/* Confetti Animation */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        {confettiElements.map((confetti) => (
          <div
            key={confetti.id}
            className="absolute animate-bounce"
            style={{
              left: `${confetti.left}%`,
              top: '-10%',
              animationDelay: `${confetti.animationDelay}s`,
              animationDuration: `${confetti.animationDuration}s`,
              fontSize: `${confetti.size}rem`,
              transform: 'translateY(100vh)'
            }}
          >
            {confetti.emoji}
          </div>
        ))}
      </div>

      {/* Main Celebration Modal */}
      <div className="bg-white rounded-3xl max-w-md w-full overflow-hidden shadow-2xl transform transition-all duration-500 scale-110">
        {/* Animated Header */}
        <div className={`bg-gradient-to-r ${celebrationInfo.gradient} p-8 relative overflow-hidden`}>
          {/* Animated Background Elements */}
          <div className="absolute inset-0 opacity-20">
            <div className="absolute top-2 left-4 w-4 h-4 bg-white rounded-full animate-ping"></div>
            <div className="absolute top-8 right-6 w-2 h-2 bg-yellow-300 rounded-full animate-pulse delay-150"></div>
            <div className="absolute bottom-4 left-8 w-3 h-3 bg-pink-300 rounded-full animate-bounce delay-300"></div>
            <div className="absolute bottom-8 right-4 w-6 h-6 bg-white opacity-50 rounded-full animate-ping delay-500"></div>
          </div>

          {/* Close Button */}
          <button
            onClick={handleSkip}
            className="absolute top-4 right-4 p-2 text-white text-opacity-80 hover:text-opacity-100 transition-all rounded-full hover:bg-white hover:bg-opacity-20"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>

          {/* Celebration Icon */}
          <div className="text-center relative z-10">
            <div className="text-8xl mb-4 animate-bounce filter drop-shadow-lg">
              {celebrationInfo.icon}
            </div>
            <h2 className="text-3xl font-bold text-white mb-1 animate-pulse">
              {celebrationInfo.title}
            </h2>
            <p className="text-white text-opacity-90 text-lg font-medium">
              {celebrationInfo.subtitle}
            </p>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Achievement Details */}
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              {celebration.title}
            </h3>
            <p className="text-gray-600 text-lg leading-relaxed">
              {celebration.message}
            </p>
            
            {/* Special Details */}
            {celebration.data && (
              <div className="mt-4 bg-gray-50 rounded-xl p-4">
                {celebration.data.threshold && (
                  <div className="flex items-center justify-center space-x-2">
                    <FireIcon className="w-5 h-5 text-orange-500" />
                    <span className="font-semibold text-gray-700">
                      {celebration.data.threshold} Days Streak!
                    </span>
                  </div>
                )}
                
                {celebration.data.points_earned && (
                  <div className="flex items-center justify-center space-x-2 mt-2">
                    <StarIcon className="w-5 h-5 text-yellow-500" />
                    <span className="font-semibold text-gray-700">
                      +{celebration.data.points_earned} XP
                    </span>
                  </div>
                )}

                {celebration.data.special_perks && celebration.data.special_perks.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm font-medium text-gray-700 mb-2">Special Perks Unlocked:</p>
                    <div className="flex flex-wrap gap-2 justify-center">
                      {celebration.data.special_perks.map((perk, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium"
                        >
                          {perk.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col space-y-3">
            <button
              onClick={handleShare}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-4 px-6 rounded-xl font-semibold text-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 transform hover:scale-105 flex items-center justify-center space-x-2 shadow-lg"
            >
              <ShareIcon className="w-5 h-5" />
              <span>Share Achievement</span>
            </button>
            
            <button
              onClick={handleNext}
              className="w-full bg-emerald-500 text-white py-3 px-6 rounded-xl font-semibold hover:bg-emerald-600 transition-all duration-200 flex items-center justify-center space-x-2"
            >
              <CheckIcon className="w-5 h-5" />
              <span>Continue</span>
            </button>
            
            <button
              onClick={handleSkip}
              className="w-full text-gray-500 py-2 px-6 rounded-xl hover:text-gray-700 transition-all duration-200 text-center"
            >
              Skip for now
            </button>
          </div>
        </div>

        {/* Progress Indicator (if multiple celebrations) */}
        {celebration.celebrationIndex !== undefined && celebration.totalCelebrations > 1 && (
          <div className="px-6 pb-4">
            <div className="flex justify-center space-x-2">
              {Array.from({ length: celebration.totalCelebrations }, (_, i) => (
                <div
                  key={i}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    i === celebration.celebrationIndex 
                      ? 'bg-blue-500' 
                      : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>
            <p className="text-center text-sm text-gray-500 mt-2">
              {celebration.celebrationIndex + 1} of {celebration.totalCelebrations} achievements
            </p>
          </div>
        )}
      </div>

      {/* Background Pattern */}
      <div className="fixed inset-0 pointer-events-none opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23000000' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }}></div>
      </div>
    </div>
  );
};

export default EnhancedCelebration;
