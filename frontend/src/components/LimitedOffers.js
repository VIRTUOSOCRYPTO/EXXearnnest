import React, { useState, useEffect } from 'react';
import axios from 'axios';

const LimitedOffers = () => {
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fomoAlerts, setFomoAlerts] = useState([]);

  useEffect(() => {
    fetchLimitedOffers();
    fetchFomoAlerts();
    
    // Refresh every 5 minutes
    const interval = setInterval(() => {
      fetchLimitedOffers();
      fetchFomoAlerts();
    }, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchLimitedOffers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/engagement/limited-offers`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setOffers(response.data.offers);
    } catch (error) {
      console.error('Limited offers error:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFomoAlerts = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/engagement/fomo-alerts`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setFomoAlerts(response.data.alerts);
    } catch (error) {
      console.error('FOMO alerts error:', error);
    }
  };

  const getUrgencyColor = (urgency) => {
    switch (urgency) {
      case 'high': return 'border-red-500 bg-red-50';
      case 'medium': return 'border-yellow-500 bg-yellow-50';
      case 'low': return 'border-blue-500 bg-blue-50';
      default: return 'border-gray-300 bg-gray-50';
    }
  };

  const getUrgencyTextColor = (urgency) => {
    switch (urgency) {
      case 'high': return 'text-red-700';
      case 'medium': return 'text-yellow-700';
      case 'low': return 'text-blue-700';
      default: return 'text-gray-700';
    }
  };

  const formatTimeRemaining = (offer) => {
    if (offer.hours_remaining) {
      return `${offer.hours_remaining} hours left`;
    }
    if (offer.days_remaining) {
      return `${offer.days_remaining} days left`;
    }
    return 'Ending soon';
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="animate-pulse space-y-4">
          {[1, 2].map(i => (
            <div key={i} className="h-32 bg-gray-300 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Limited Time Offers */}
      <div className="bg-white rounded-lg shadow-lg">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            ⏰ Limited Time Offers
          </h2>
          <p className="text-gray-600 mt-2">Don't miss these exclusive opportunities!</p>
        </div>

        <div className="p-6 space-y-4">
          {offers.map((offer) => (
            <div
              key={offer.id}
              className={`border-2 rounded-lg p-4 ${getUrgencyColor(offer.urgency)} relative overflow-hidden`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <span className="text-3xl">{offer.icon}</span>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{offer.title}</h3>
                    <p className={`text-sm ${getUrgencyTextColor(offer.urgency)} mb-2`}>
                      {offer.description}
                    </p>
                    
                    {offer.type === 'points_multiplier' && (
                      <div className="flex items-center space-x-2">
                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                          {offer.multiplier}x Points
                        </span>
                      </div>
                    )}
                    
                    {offer.type === 'savings_challenge' && (
                      <div className="flex items-center space-x-4">
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                          Target: ₹{offer.target_amount}
                        </span>
                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                          Reward: ₹{offer.reward}
                        </span>
                      </div>
                    )}
                    
                    {offer.type === 'social_challenge' && (
                      <div className="flex items-center space-x-2">
                        <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs font-medium">
                          Invite {offer.target} friends
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="text-right">
                  <div className={`text-sm font-bold ${getUrgencyTextColor(offer.urgency)}`}>
                    {formatTimeRemaining(offer)}
                  </div>
                  <button 
                    className={`mt-2 px-4 py-2 rounded-lg font-medium text-white ${
                      offer.urgency === 'high' 
                        ? 'bg-red-500 hover:bg-red-600' 
                        : offer.urgency === 'medium'
                        ? 'bg-yellow-500 hover:bg-yellow-600'
                        : 'bg-blue-500 hover:bg-blue-600'
                    } transition-colors`}
                  >
                    {offer.participated ? 'Participating' : 'Join Now'}
                  </button>
                </div>
              </div>
              
              {offer.participated && (
                <div className="mt-3 bg-white bg-opacity-50 rounded p-2">
                  <div className="flex justify-between text-xs">
                    <span>Progress:</span>
                    <span>{offer.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                    <div 
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(offer.progress, 100)}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {offers.length === 0 && (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">⏰</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No active offers</h3>
              <p className="text-gray-500">Check back later for new limited-time opportunities!</p>
            </div>
          )}
        </div>
      </div>

      {/* FOMO Alerts */}
      {fomoAlerts.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              🔥 Don't Miss Out!
            </h2>
            <p className="text-gray-600 mt-2">Limited spots and exclusive opportunities</p>
          </div>

          <div className="p-6 space-y-3">
            {fomoAlerts.map((alert, index) => (
              <div
                key={index}
                className={`border-l-4 p-4 ${getUrgencyColor(alert.urgency)} rounded-r-lg`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{alert.icon}</span>
                    <div>
                      <h4 className="font-bold text-gray-900">{alert.title}</h4>
                      <p className="text-sm text-gray-600">{alert.message}</p>
                    </div>
                  </div>
                  <button 
                    className={`px-4 py-2 rounded-lg font-medium text-white ${
                      alert.urgency === 'high' 
                        ? 'bg-red-500 hover:bg-red-600' 
                        : 'bg-blue-500 hover:bg-blue-600'
                    } transition-colors`}
                  >
                    {alert.action}
                  </button>
                </div>
                
                {alert.spots_remaining && (
                  <div className="mt-2 text-xs text-gray-500">
                    Only {alert.spots_remaining} spots remaining
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default LimitedOffers;
