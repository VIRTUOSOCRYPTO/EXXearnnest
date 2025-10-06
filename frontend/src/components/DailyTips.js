import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

const DailyTips = ({ userId }) => {
  const [todaysTip, setTodaysTip] = useState(null);
  const [tipHistory, setTipHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [interactionLoading, setInteractionLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    fetchTodaysTip();
  }, [userId]);

  const fetchTodaysTip = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/daily-tips`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTodaysTip(data.tip);
      } else {
        console.error('Failed to fetch daily tip');
      }
    } catch (error) {
      console.error('Error fetching daily tip:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTipHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/daily-tips/history?limit=10`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTipHistory(data.tips);
      }
    } catch (error) {
      console.error('Error fetching tip history:', error);
    }
  };

  const recordInteraction = async (interactionType, interactionData = {}) => {
    if (!todaysTip?.tip_id) return;

    try {
      setInteractionLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/daily-tips/${todaysTip.tip_id}/interact?interaction_type=${interactionType}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(interactionData),
      });

      if (response.ok) {
        // Update local state to reflect interaction
        if (interactionType === 'viewed' && !todaysTip.viewed_at) {
          setTodaysTip(prev => ({ ...prev, viewed_at: new Date().toISOString() }));
        }
      }
    } catch (error) {
      console.error('Error recording interaction:', error);
    } finally {
      setInteractionLoading(false);
    }
  };

  const handleTipClick = () => {
    if (todaysTip && !todaysTip.viewed_at) {
      recordInteraction('viewed');
    }
  };

  const handleLike = () => {
    recordInteraction('liked', { tip_rating: 5 });
  };

  const handleShare = () => {
    recordInteraction('shared', { platform: 'clipboard' });
    // Copy tip to clipboard
    const tipText = `${todaysTip.tip_title}\n\n${todaysTip.tip_content}\n\n- EarnNest Daily Tips`;
    navigator.clipboard.writeText(tipText).then(() => {
      alert('Tip copied to clipboard!');
    });
  };

  const handleSave = () => {
    recordInteraction('saved');
    alert('Tip saved to your favorites!');
  };

  const handleDismiss = () => {
    recordInteraction('dismissed');
  };

  const toggleHistory = () => {
    if (!showHistory && tipHistory.length === 0) {
      fetchTipHistory();
    }
    setShowHistory(!showHistory);
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-3/4"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Today's Tip */}
      {todaysTip && (
        <Card className="w-full border-l-4 border-l-blue-500 shadow-lg hover:shadow-xl transition-all duration-300">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">{todaysTip.icon || '💡'}</span>
                <h3 className="font-semibold text-lg text-gray-900">Daily Financial Tip</h3>
                <Badge variant="secondary" className="text-xs">
                  {new Date().toLocaleDateString()}
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDismiss}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0" onClick={handleTipClick}>
            <div className="mb-4">
              <h4 className="font-medium text-gray-900 mb-2 cursor-pointer hover:text-blue-600 transition-colors">
                {todaysTip.tip_title}
              </h4>
              <p className="text-gray-700 leading-relaxed cursor-pointer">
                {todaysTip.tip_content}
              </p>
            </div>

            {/* Tip Metadata */}
            {todaysTip.metadata && (
              <div className="text-xs text-gray-500 mb-4">
                {todaysTip.metadata.generated_by === 'ai' && (
                  <Badge variant="outline" className="mr-2">
                    🤖 AI Personalized
                  </Badge>
                )}
                {todaysTip.metadata.category && (
                  <Badge variant="outline" className="mr-2">
                    {todaysTip.metadata.category}
                  </Badge>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={handleLike}
                disabled={interactionLoading}
                className="flex items-center space-x-1 hover:bg-green-50 hover:border-green-300"
              >
                <span>👍</span>
                <span>Helpful</span>
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleShare}
                disabled={interactionLoading}
                className="flex items-center space-x-1 hover:bg-blue-50 hover:border-blue-300"
              >
                <span>📤</span>
                <span>Share</span>
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleSave}
                disabled={interactionLoading}
                className="flex items-center space-x-1 hover:bg-purple-50 hover:border-purple-300"
              >
                <span>⭐</span>
                <span>Save</span>
              </Button>
            </div>

            {/* View Status */}
            {todaysTip.viewed_at && (
              <div className="text-xs text-gray-400 mt-2">
                ✓ Viewed at {new Date(todaysTip.viewed_at).toLocaleTimeString()}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DailyTips;
