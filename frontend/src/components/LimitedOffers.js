import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';

const LimitedOffers = ({ userId }) => {
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [participatingOffer, setParticipatingOffer] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [offerHistory, setOfferHistory] = useState([]);

  useEffect(() => {
    fetchActiveOffers();
  }, [userId]);

  useEffect(() => {
    // Update countdown timers every second
    const interval = setInterval(() => {
      setOffers(prevOffers => 
        prevOffers.map(offer => ({
          ...offer,
          time_remaining: calculateTimeRemaining(offer.expires_at)
        }))
      );
    }, 1000);

    return () => clearInterval(interval);
  }, [offers.length]);

  const fetchActiveOffers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/offers`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setOffers(data.offers.map(offer => ({
          ...offer,
          time_remaining: calculateTimeRemaining(offer.expires_at)
        })));
      } else {
        console.error('Failed to fetch offers');
      }
    } catch (error) {
      console.error('Error fetching offers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchOfferHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/offers/history`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setOfferHistory(data.history);
      }
    } catch (error) {
      console.error('Error fetching offer history:', error);
    }
  };

  const participateInOffer = async (offerId) => {
    try {
      setParticipatingOffer(offerId);
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/offers/${offerId}/participate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();
      
      if (result.success) {
        alert(result.message);
        // Update the offer in state to reflect participation
        setOffers(prevOffers => 
          prevOffers.map(offer => 
            offer.id === offerId 
              ? { 
                  ...offer, 
                  spots_claimed: offer.spots_claimed + 1,
                  user_participated: true
                }
              : offer
          )
        );
      } else {
        alert(result.message);
      }
    } catch (error) {
      console.error('Error participating in offer:', error);
      alert('Failed to join offer. Please try again.');
    } finally {
      setParticipatingOffer(null);
    }
  };

  const calculateTimeRemaining = (expiresAt) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diff = expiry - now;

    if (diff <= 0) {
      return { expired: true, display: 'Expired' };
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    let display;
    if (days > 0) {
      display = `${days}d ${hours}h`;
    } else if (hours > 0) {
      display = `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      display = `${minutes}m ${seconds}s`;
    } else {
      display = `${seconds}s`;
    }

    return {
      expired: false,
      days,
      hours,
      minutes,
      seconds,
      display,
      total_seconds: Math.floor(diff / 1000)
    };
  };

  const getUrgencyColor = (urgencyLevel, timeRemaining) => {
    if (timeRemaining?.expired) return 'bg-gray-500';
    if (urgencyLevel >= 4 || (timeRemaining?.hours < 6 && timeRemaining?.days === 0)) return 'bg-red-500';
    if (urgencyLevel >= 3 || timeRemaining?.days <= 1) return 'bg-orange-500';
    return 'bg-blue-500';
  };

  const getOfferIcon = (offerType) => {
    const icons = {
      'challenge': '🎯',
      'premium_unlock': '⭐',
      'referral_bonus': '🤝',
      'early_access': '🚀'
    };
    return icons[offerType] || '🔥';
  };

  const toggleHistory = () => {
    if (!showHistory && offerHistory.length === 0) {
      fetchOfferHistory();
    }
    setShowHistory(!showHistory);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2].map(i => (
          <Card key={i} className="w-full">
            <CardContent className="p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-3/4"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">🔥 Limited-Time Offers</h2>
        <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
          🔄 Refresh
        </Button>
      </div>

      {offers.length === 0 ? (
        <Card className="w-full">
          <CardContent className="p-8 text-center">
            <div className="text-6xl mb-4">🎯</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Offers</h3>
            <p className="text-gray-600">Check back soon for exclusive opportunities!</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {offers.map((offer) => (
            <Card 
              key={offer.id} 
              className={`w-full border-l-4 ${
                offer.time_remaining?.expired ? 'border-l-gray-400 opacity-75' : 
                `border-l-${offer.color_scheme}-500`
              } shadow-lg hover:shadow-xl transition-all duration-300`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-3xl">{offer.icon}</span>
                    <div>
                      <h3 className="font-bold text-lg text-gray-900">{offer.title}</h3>
                      <Badge 
                        variant={offer.offer_type === 'premium_unlock' ? 'default' : 'secondary'}
                        className="mt-1"
                      >
                        {offer.offer_type.replace('_', ' ').toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge 
                      variant="outline" 
                      className={`${getUrgencyColor(offer.urgency_level, offer.time_remaining)} text-white border-transparent`}
                    >
                      {offer.time_remaining?.display || 'Calculating...'}
                    </Badge>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                <p className="text-gray-700">{offer.description}</p>

                {/* FOMO Indicators */}
                <div className="space-y-2">
                  {offer.total_spots && (
                    <div>
                      <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                        <span>Spots Claimed</span>
                        <span>{offer.spots_claimed}/{offer.total_spots}</span>
                      </div>
                      <Progress 
                        value={(offer.spots_claimed / offer.total_spots) * 100} 
                        className="h-2"
                      />
                      <p className="text-sm font-medium text-red-600 mt-1">
                        {offer.spots_remaining !== undefined && offer.spots_remaining <= 10 && 
                          `⚡ Only ${offer.spots_remaining} spots left!`
                        }
                      </p>
                    </div>
                  )}

                  {offer.urgency_message && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <p className="text-sm font-medium text-red-800">
                        {offer.urgency_message}
                      </p>
                    </div>
                  )}
                </div>

                {/* Offer Details */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">What You Get:</h4>
                  <div className="text-sm text-gray-700">
                    <p>🎁 Reward: {offer.reward_type === 'points' ? `${offer.reward_value} Points` : offer.reward_value}</p>
                    {offer.offer_details && (
                      <div className="mt-2 space-y-1">
                        {Object.entries(offer.offer_details).map(([key, value]) => (
                          <p key={key}>
                            • {key.replace('_', ' ')}: {typeof value === 'object' ? JSON.stringify(value) : value}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Action Button */}
                <div className="pt-2">
                  {offer.time_remaining?.expired ? (
                    <Button disabled className="w-full">
                      ⏰ Offer Expired
                    </Button>
                  ) : offer.user_participated ? (
                    <Button disabled className="w-full">
                      ✅ Already Participating
                    </Button>
                  ) : offer.spots_remaining === 0 ? (
                    <Button disabled className="w-full">
                      😞 All Spots Claimed
                    </Button>
                  ) : (
                    <Button
                      onClick={() => participateInOffer(offer.id)}
                      disabled={participatingOffer === offer.id}
                      className={`w-full bg-${offer.color_scheme}-600 hover:bg-${offer.color_scheme}-700 text-white font-medium`}
                    >
                      {participatingOffer === offer.id ? (
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Joining...</span>
                        </div>
                      ) : (
                        <>🚀 Join Now{offer.total_spots && ` (${offer.spots_remaining} left)`}</>
                      )}
                    </Button>
                  )}
                </div>

                {/* Countdown Bar for Urgent Offers */}
                {offer.urgency_level >= 4 && offer.time_remaining && !offer.time_remaining.expired && (
                  <div className="bg-red-100 rounded-lg p-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-red-800">⏰ Time Running Out!</span>
                      <span className="font-mono text-red-700">{offer.time_remaining.display}</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* History Toggle */}
      <div className="flex justify-center pt-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleHistory}
          className="text-gray-600 hover:text-gray-800"
        >
          {showHistory ? '▼ Hide Offer History' : '▶ View Offer History'}
        </Button>
      </div>

      {/* Offer History */}
      {showHistory && (
        <Card className="w-full">
          <CardHeader>
            <h3 className="font-medium text-gray-900">Your Offer History</h3>
          </CardHeader>
          <CardContent>
            {offerHistory.length === 0 ? (
              <p className="text-gray-500 text-sm">No offer history found.</p>
            ) : (
              <div className="space-y-3">
                {offerHistory.map((participation) => (
                  <div key={participation.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h5 className="font-medium text-gray-800">
                        {participation.offer_details?.title || 'Offer'}
                      </h5>
                      <Badge variant={
                        participation.status === 'completed' ? 'default' :
                        participation.status === 'active' ? 'secondary' :
                        'outline'
                      }>
                        {participation.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">
                      Joined: {new Date(participation.participated_at).toLocaleDateString()}
                    </p>
                    {participation.reward_claimed && (
                      <div className="text-sm text-green-600">
                        ✅ Reward claimed
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default LimitedOffers;
