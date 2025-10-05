import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { useNavigate } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

const OffersHistory = () => {
  const [offerHistory, setOfferHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total_offers: 0,
    completed_offers: 0,
    active_offers: 0,
    total_rewards: 0
  });
  const navigate = useNavigate();

  useEffect(() => {
    fetchOfferHistory();
    fetchOfferStats();
  }, []);

  const fetchOfferHistory = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/offers/history`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setOfferHistory(data.history || []);
      }
    } catch (error) {
      console.error('Error fetching offer history:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchOfferStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/offers/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data.stats || stats);
      }
    } catch (error) {
      console.error('Error fetching offer stats:', error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'completed': 'bg-green-100 text-green-800',
      'active': 'bg-blue-100 text-blue-800',
      'expired': 'bg-gray-100 text-gray-800',
      'failed': 'bg-red-100 text-red-800'
    };
    return colors[status] || colors['expired'];
  };

  const getOfferTypeIcon = (offerType) => {
    const icons = {
      'challenge': '🎯',
      'premium_unlock': '⭐',
      'referral_bonus': '🤝',
      'early_access': '🚀',
      'limited_time': '⏰'
    };
    return icons[offerType] || '🔥';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map(i => (
              <Card key={i} className="w-full">
                <CardContent className="p-6">
                  <div className="h-8 bg-gray-200 rounded mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded"></div>
                </CardContent>
              </Card>
            ))}
          </div>
          {[1, 2, 3].map(i => (
            <Card key={i} className="w-full">
              <CardContent className="p-6">
                <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-3/4"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center space-x-4 mb-8">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/dashboard')}
          className="flex items-center space-x-2"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-3">
            <span className="text-4xl">🔥</span>
            <span>Offers History</span>
          </h1>
          <p className="text-gray-600 mt-2">Track your participation in limited-time offers and rewards</p>
        </div>
      </div>

      {/* Stats Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-3xl font-bold text-blue-600">{stats.total_offers}</div>
            <div className="text-sm text-gray-600">Total Offers Joined</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-3xl font-bold text-green-600">{stats.completed_offers}</div>
            <div className="text-sm text-gray-600">Completed</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-3xl font-bold text-orange-600">{stats.active_offers}</div>
            <div className="text-sm text-gray-600">Active</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-3xl font-bold text-purple-600">{stats.total_rewards}</div>
            <div className="text-sm text-gray-600">Total Rewards</div>
          </CardContent>
        </Card>
      </div>

      {/* Completion Rate */}
      {stats.total_offers > 0 && (
        <Card className="mb-8">
          <CardHeader>
            <h3 className="font-semibold text-gray-900">Your Success Rate</h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Completion Rate</span>
                  <span>{Math.round((stats.completed_offers / stats.total_offers) * 100)}%</span>
                </div>
                <Progress value={(stats.completed_offers / stats.total_offers) * 100} className="h-3" />
              </div>
              <p className="text-sm text-gray-600">
                You've successfully completed {stats.completed_offers} out of {stats.total_offers} offers you joined.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Offers History List */}
      <div className="space-y-6">
        {offerHistory.length === 0 ? (
          <Card className="w-full">
            <CardContent className="p-8 text-center">
              <div className="text-6xl mb-4">🎯</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Offer History</h3>
              <p className="text-gray-600">You haven't participated in any offers yet. Check the dashboard for active offers!</p>
              <Button 
                className="mt-4" 
                onClick={() => navigate('/dashboard')}
              >
                Browse Active Offers
              </Button>
            </CardContent>
          </Card>
        ) : (
          offerHistory.map((participation) => (
            <Card key={participation.id} className="w-full hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <div className="text-3xl">
                      {getOfferTypeIcon(participation.offer_details?.offer_type)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-xl text-gray-900">
                        {participation.offer_details?.title || 'Limited Offer'}
                      </h3>
                      <p className="text-gray-600 text-sm mt-1">
                        {participation.offer_details?.description}
                      </p>
                      <div className="flex items-center space-x-3 mt-2">
                        <Badge className={getStatusColor(participation.status)}>
                          {participation.status}
                        </Badge>
                        <span className="text-xs text-gray-500">
                          Joined: {formatDate(participation.participated_at)}
                        </span>
                        {participation.offer_details?.offer_type && (
                          <Badge variant="outline" className="text-xs">
                            {participation.offer_details.offer_type.replace('_', ' ').toUpperCase()}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {participation.status === 'completed' && participation.reward_claimed && (
                    <div className="text-right">
                      <div className="text-green-600 font-semibold">✅ Reward Claimed</div>
                      {participation.reward_details && (
                        <div className="text-sm text-gray-600">
                          +{participation.reward_details.value} {participation.reward_details.type}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Offer Details */}
                {participation.offer_details && (
                  <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <h4 className="font-medium text-gray-900 mb-2">Offer Details:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      {participation.offer_details.reward_type && (
                        <div>
                          <span className="text-gray-600">Reward Type:</span>
                          <span className="ml-2 font-medium">{participation.offer_details.reward_type}</span>
                        </div>
                      )}
                      {participation.offer_details.reward_value && (
                        <div>
                          <span className="text-gray-600">Reward Value:</span>
                          <span className="ml-2 font-medium">{participation.offer_details.reward_value}</span>
                        </div>
                      )}
                      {participation.offer_details.urgency_level && (
                        <div>
                          <span className="text-gray-600">Urgency Level:</span>
                          <span className="ml-2 font-medium">
                            {'🔥'.repeat(participation.offer_details.urgency_level)}
                          </span>
                        </div>
                      )}
                      {participation.offer_details.expires_at && (
                        <div>
                          <span className="text-gray-600">Expired:</span>
                          <span className="ml-2 font-medium">
                            {formatDate(participation.offer_details.expires_at)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Progress Information */}
                {participation.progress && (
                  <div className="mb-4">
                    <h4 className="font-medium text-gray-900 mb-2">Progress:</h4>
                    <div className="space-y-2">
                      {Object.entries(participation.progress).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center text-sm">
                          <span className="text-gray-600 capitalize">{key.replace('_', ' ')}:</span>
                          <span className="font-medium">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Timeline */}
                <div className="border-t border-gray-100 pt-4">
                  <h4 className="font-medium text-gray-900 mb-3">Timeline:</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                      <span className="text-gray-600">Joined:</span>
                      <span>{formatDate(participation.participated_at)}</span>
                    </div>
                    {participation.completed_at && (
                      <div className="flex items-center space-x-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        <span className="text-gray-600">Completed:</span>
                        <span>{formatDate(participation.completed_at)}</span>
                      </div>
                    )}
                    {participation.reward_claimed_at && (
                      <div className="flex items-center space-x-2">
                        <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                        <span className="text-gray-600">Reward Claimed:</span>
                        <span>{formatDate(participation.reward_claimed_at)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default OffersHistory;
