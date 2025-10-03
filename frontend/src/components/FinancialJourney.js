import React, { useState, useEffect } from 'react';
import axios from 'axios';

const FinancialJourney = () => {
  const [journeyData, setJourneyData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFinancialJourney();
  }, []);

  const fetchFinancialJourney = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/engagement/financial-journey`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setJourneyData(response.data);
    } catch (error) {
      console.error('Financial journey error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEventTypeColor = (type) => {
    switch (type) {
      case 'milestone': return 'bg-blue-500';
      case 'transaction': return 'bg-green-500';
      case 'achievement': return 'bg-yellow-500';
      case 'social': return 'bg-pink-500';
      default: return 'bg-gray-500';
    }
  };

  const getEventIcon = (event) => {
    return event.icon || '📱';
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-300 rounded w-1/3 mb-6"></div>
          <div className="space-y-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="flex space-x-4">
                <div className="w-4 h-4 bg-gray-300 rounded-full mt-2"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-300 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-300 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!journeyData) return null;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center mb-2">
            📖 Your Financial Journey
          </h2>
          <p className="text-gray-600">{journeyData.story_summary}</p>
        </div>

        {/* Journey Stats */}
        <div className="p-6 border-b border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-blue-50 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-blue-600">{journeyData.journey_stats.days_active}</div>
              <div className="text-xs text-blue-800">Days Active</div>
            </div>
            <div className="bg-green-50 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-green-600">₹{journeyData.journey_stats.total_savings.toLocaleString()}</div>
              <div className="text-xs text-green-800">Total Savings</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-purple-600">₹{journeyData.journey_stats.total_income.toLocaleString()}</div>
              <div className="text-xs text-purple-800">Total Income</div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-yellow-600">{journeyData.journey_stats.achievements_earned}</div>
              <div className="text-xs text-yellow-800">Achievements</div>
            </div>
            <div className="bg-pink-50 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-pink-600">{journeyData.journey_stats.milestones_reached}</div>
              <div className="text-xs text-pink-800">Milestones</div>
            </div>
          </div>
        </div>

        {/* Timeline */}
        <div className="p-6">
          <div className="relative">
            {/* Vertical Line */}
            <div className="absolute left-6 top-0 bottom-0 w-px bg-gray-300"></div>
            
            {journeyData.timeline.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">🚀</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Your journey starts here!</h3>
                <p className="text-gray-500">Complete your first transaction to begin building your financial story.</p>
              </div>
            ) : (
              <div className="space-y-8">
                {journeyData.timeline.map((event, index) => (
                  <div key={index} className="relative flex items-start space-x-6">
                    {/* Timeline Dot */}
                    <div className={`relative z-10 flex items-center justify-center w-12 h-12 ${getEventTypeColor(event.type)} rounded-full text-white font-bold shadow-lg`}>
                      <span className="text-lg">{getEventIcon(event)}</span>
                    </div>
                    
                    {/* Event Content */}
                    <div className="flex-1 bg-gray-50 rounded-lg p-4 shadow-sm">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-lg font-bold text-gray-900 mb-1">{event.title}</h3>
                          <p className="text-gray-600 text-sm mb-2">{event.description}</p>
                          
                          {event.amount && (
                            <div className="inline-flex items-center bg-green-100 text-green-800 px-2 py-1 rounded-full text-sm font-medium">
                              ₹{event.amount.toLocaleString()}
                            </div>
                          )}
                        </div>
                        
                        <div className="text-right ml-4">
                          <div className="text-sm font-medium text-gray-900">#{event.story_position}</div>
                          <div className="text-xs text-gray-500">{event.time_text}</div>
                        </div>
                      </div>
                      
                      {/* Event Type Badge */}
                      <div className="mt-3 flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          event.type === 'milestone' ? 'bg-blue-100 text-blue-800' :
                          event.type === 'transaction' ? 'bg-green-100 text-green-800' :
                          event.type === 'achievement' ? 'bg-yellow-100 text-yellow-800' :
                          event.type === 'social' ? 'bg-pink-100 text-pink-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {event.type.charAt(0).toUpperCase() + event.type.slice(1)}
                        </span>
                        
                        {event.days_ago === 0 && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 animate-pulse">
                            New Today!
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Next Steps */}
        <div className="p-6 bg-gray-50 border-t border-gray-200">
          <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4">
            <h4 className="font-bold text-gray-900 mb-2">🎯 What's Next?</h4>
            <p className="text-gray-700 text-sm mb-3">{journeyData.next_milestone}</p>
            <div className="flex flex-wrap gap-2">
              <button className="bg-green-500 text-white px-3 py-1 rounded-full text-sm hover:bg-green-600 transition-colors">
                Add Transaction
              </button>
              <button className="bg-blue-500 text-white px-3 py-1 rounded-full text-sm hover:bg-blue-600 transition-colors">
                Set Goal
              </button>
              <button className="bg-purple-500 text-white px-3 py-1 rounded-full text-sm hover:bg-purple-600 transition-colors">
                Invite Friends
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinancialJourney;
