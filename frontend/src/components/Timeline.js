import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

const Timeline = ({ userId }) => {
  const [timelineData, setTimelineData] = useState([]);
  const [friendActivities, setFriendActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('combined');
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [timelineStats, setTimelineStats] = useState(null);
  const [reactionLoading, setReactionLoading] = useState(null);

  useEffect(() => {
    fetchTimeline(activeTab);
    fetchTimelineStats();
  }, [userId, activeTab]);

  const fetchTimeline = async (type = 'combined', offset = 0) => {
    try {
      if (offset === 0) setLoading(true);
      else setLoadingMore(true);

      const token = localStorage.getItem('token');
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/timeline?timeline_type=${type}&limit=20&offset=${offset}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        
        if (offset === 0) {
          setTimelineData(data.timeline);
        } else {
          setTimelineData(prev => [...prev, ...data.timeline]);
        }
        
        setHasMore(data.timeline.length === 20);
      } else {
        console.error('Failed to fetch timeline');
      }
    } catch (error) {
      console.error('Error fetching timeline:', error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const fetchFriendActivities = async (offset = 0) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/timeline/friends?limit=15&offset=${offset}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setFriendActivities(data.activities);
      }
    } catch (error) {
      console.error('Error fetching friend activities:', error);
    }
  };

  const fetchTimelineStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/timeline/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTimelineStats(data.stats);
      }
    } catch (error) {
      console.error('Error fetching timeline stats:', error);
    }
  };

  const reactToEvent = async (eventId, reactionType) => {
    try {
      setReactionLoading(eventId);
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/timeline/events/${eventId}/react?reaction_type=${reactionType}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        // Update local state to reflect reaction
        setTimelineData(prev => 
          prev.map(event => {
            if (event.id === eventId) {
              const updatedReactions = { ...event.reactions };
              const currentUserReaction = event.user_reaction;
              
              // Remove previous reaction if exists
              if (currentUserReaction) {
                updatedReactions[currentUserReaction] = Math.max(0, (updatedReactions[currentUserReaction] || 1) - 1);
              }
              
              // Add new reaction
              updatedReactions[reactionType] = (updatedReactions[reactionType] || 0) + 1;
              
              return {
                ...event,
                reactions: updatedReactions,
                user_reaction: reactionType
              };
            }
            return event;
          })
        );
      }
    } catch (error) {
      console.error('Error reacting to event:', error);
    } finally {
      setReactionLoading(null);
    }
  };

  const loadMore = () => {
    if (!loadingMore && hasMore) {
      fetchTimeline(activeTab, timelineData.length);
    }
  };

  const getEventIcon = (category, subcategory) => {
    const iconMap = {
      transaction: {
        income: '💰',
        expense: '💳'
      },
      milestone: {
        savings: '🏆',
        streak: '🔥',
        transaction_count: '📊'
      },
      goal: {
        created: '🎯',
        completed: '✅',
        milestone: '📈'
      },
      badge: '🏅',
      friend_activity: '👥',
      challenge: '🎮'
    };
    
    return iconMap[category]?.[subcategory] || iconMap[category] || '📊';
  };

  const getEventColor = (category, color) => {
    if (color) return color;
    
    const colorMap = {
      transaction: '#3B82F6',
      milestone: '#8B5CF6',
      goal: '#F59E0B',
      badge: '#10B981',
      friend_activity: '#6B7280',
      challenge: '#EF4444'
    };
    
    return colorMap[category] || '#6B7280';
  };

  const formatAmount = (amount) => {
    if (!amount) return null;
    return amount >= 1000 ? `₹${(amount / 1000).toFixed(1)}k` : `₹${amount}`;
  };

  const ReactionButtons = ({ event }) => {
    const reactions = [
      { type: 'like', emoji: '👍', label: 'Like' },
      { type: 'celebrate', emoji: '🎉', label: 'Celebrate' },
      { type: 'motivate', emoji: '💪', label: 'Motivate' },
      { type: 'inspire', emoji: '✨', label: 'Inspire' }
    ];

    return (
      <div className="flex items-center space-x-2 pt-2">
        {reactions.map(({ type, emoji, label }) => (
          <Button
            key={type}
            variant="ghost"
            size="sm"
            onClick={() => reactToEvent(event.id, type)}
            disabled={reactionLoading === event.id}
            className={`flex items-center space-x-1 ${
              event.user_reaction === type 
                ? 'bg-blue-100 text-blue-700 border-blue-300' 
                : 'hover:bg-gray-100'
            }`}
          >
            <span>{emoji}</span>
            <span className="text-xs">{event.reactions?.[type] || 0}</span>
          </Button>
        ))}
      </div>
    );
  };

  const TimelineEvent = ({ event, showFriendInfo = false }) => (
    <Card key={event.id} className="w-full hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-4">
        <div className="flex items-start space-x-3">
          {/* Event Icon */}
          <div 
            className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-white font-medium"
            style={{ backgroundColor: getEventColor(event.category, event.color) }}
          >
            {event.icon || getEventIcon(event.category, event.subcategory)}
          </div>

          {/* Event Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center space-x-2">
                <h4 className="font-medium text-gray-900 truncate">
                  {event.title}
                </h4>
                {event.is_featured && (
                  <Badge variant="secondary" className="text-xs">
                    ⭐ Featured
                  </Badge>
                )}
                {event.amount && (
                  <Badge variant="outline" className="text-xs">
                    {formatAmount(event.amount)}
                  </Badge>
                )}
              </div>
              <span className="text-xs text-gray-500 whitespace-nowrap">
                {event.relative_time}
              </span>
            </div>

            <p className="text-sm text-gray-600 mb-2">{event.description}</p>

            {/* Friend Info for Social Events */}
            {showFriendInfo && event.friend_info && (
              <div className="flex items-center space-x-2 mb-2 p-2 bg-gray-50 rounded-lg">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs">
                  👤
                </div>
                <span className="text-xs text-gray-600">
                  {event.friend_info.name}
                  {event.friend_info.university && ` • ${event.friend_info.university}`}
                </span>
              </div>
            )}

            {/* Category Badge */}
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-xs">
                {event.category.replace('_', ' ')}
                {event.subcategory && ` • ${event.subcategory.replace('_', ' ')}`}
              </Badge>
              
              {/* Reaction Count */}
              {event.reaction_count > 0 && (
                <span className="text-xs text-gray-500">
                  {event.reaction_count} reaction{event.reaction_count !== 1 ? 's' : ''}
                </span>
              )}
            </div>

            {/* Reactions */}
            <ReactionButtons event={event} />
          </div>
        </div>

        {/* Event Image */}
        {event.image_url && (
          <div className="mt-3 ml-13">
            <img 
              src={event.image_url} 
              alt="Event" 
              className="w-full max-w-md h-32 object-cover rounded-lg"
            />
          </div>
        )}
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <Card key={i} className="w-full">
            <CardContent className="p-4">
              <div className="animate-pulse flex space-x-3">
                <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Timeline Stats Header */}
      {timelineStats && (
        <Card className="w-full">
          <CardHeader>
            <h2 className="text-2xl font-bold text-gray-900">📖 Your Financial Story</h2>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="space-y-1">
                <div className="text-2xl font-bold text-blue-600">{timelineStats.total_events}</div>
                <div className="text-xs text-gray-600">Total Events</div>
              </div>
              <div className="space-y-1">
                <div className="text-2xl font-bold text-green-600">{timelineStats.featured_events}</div>
                <div className="text-xs text-gray-600">Featured</div>
              </div>
              <div className="space-y-1">
                <div className="text-2xl font-bold text-purple-600">{timelineStats.total_reactions}</div>
                <div className="text-xs text-gray-600">Reactions</div>
              </div>
              <div className="space-y-1">
                <div className="text-2xl font-bold text-orange-600">
                  {Math.round(timelineStats.engagement_score * 100)}%
                </div>
                <div className="text-xs text-gray-600">Engagement</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Timeline Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="combined">📱 Combined</TabsTrigger>
          <TabsTrigger value="personal">👤 Personal</TabsTrigger>
          <TabsTrigger value="social">👥 Social</TabsTrigger>
        </TabsList>

        <TabsContent value="combined" className="space-y-4 mt-6">
          {timelineData.length === 0 ? (
            <Card className="w-full">
              <CardContent className="p-8 text-center">
                <div className="text-6xl mb-4">📖</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Your Story Begins Here</h3>
                <p className="text-gray-600">Start tracking your finances to create your financial journey story!</p>
              </CardContent>
            </Card>
          ) : (
            <>
              {timelineData.map((event) => (
                <TimelineEvent key={event.id} event={event} showFriendInfo={event.event_type === 'social'} />
              ))}
              
              {hasMore && (
                <div className="flex justify-center pt-4">
                  <Button 
                    variant="outline" 
                    onClick={loadMore}
                    disabled={loadingMore}
                  >
                    {loadingMore ? 'Loading...' : 'Load More'}
                  </Button>
                </div>
              )}
            </>
          )}
        </TabsContent>

        <TabsContent value="personal" className="space-y-4 mt-6">
          {timelineData.filter(event => event.event_type === 'personal').length === 0 ? (
            <Card className="w-full">
              <CardContent className="p-8 text-center">
                <div className="text-6xl mb-4">👤</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Your Personal Journey</h3>
                <p className="text-gray-600">Track transactions and achieve milestones to build your personal story!</p>
              </CardContent>
            </Card>
          ) : (
            timelineData
              .filter(event => event.event_type === 'personal')
              .map((event) => <TimelineEvent key={event.id} event={event} />)
          )}
        </TabsContent>

        <TabsContent value="social" className="space-y-4 mt-6">
          {timelineData.filter(event => event.event_type === 'social').length === 0 ? (
            <Card className="w-full">
              <CardContent className="p-8 text-center">
                <div className="text-6xl mb-4">👥</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Friend Activities</h3>
                <p className="text-gray-600">Connect with friends to see their financial achievements and milestones!</p>
                <Button className="mt-4" onClick={() => window.location.href = '/friends'}>
                  Add Friends
                </Button>
              </CardContent>
            </Card>
          ) : (
            timelineData
              .filter(event => event.event_type === 'social')
              .map((event) => <TimelineEvent key={event.id} event={event} showFriendInfo />)
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Timeline;
