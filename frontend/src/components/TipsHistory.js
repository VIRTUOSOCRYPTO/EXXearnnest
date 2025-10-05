import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { useNavigate } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

const TipsHistory = () => {
  const [tipHistory, setTipHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchTipHistory();
  }, [page]);

  const fetchTipHistory = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/daily-tips/history?limit=20&page=${page}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (page === 1) {
          setTipHistory(data.tips);
        } else {
          setTipHistory(prev => [...prev, ...data.tips]);
        }
        setHasMore(data.tips.length === 20);
      }
    } catch (error) {
      console.error('Error fetching tip history:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMoreTips = () => {
    setPage(prev => prev + 1);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Budgeting': 'bg-blue-100 text-blue-800',
      'Investing': 'bg-green-100 text-green-800',
      'Saving': 'bg-purple-100 text-purple-800',
      'Side Hustle': 'bg-orange-100 text-orange-800',
      'General': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || colors['General'];
  };

  if (loading && page === 1) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          {[1, 2, 3, 4, 5].map(i => (
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
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
            <span className="text-4xl">💡</span>
            <span>Tips History</span>
          </h1>
          <p className="text-gray-600 mt-2">Your complete collection of financial tips and advice</p>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-blue-600">{tipHistory.length}</div>
            <div className="text-sm text-gray-600">Total Tips Received</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-green-600">
              {tipHistory.filter(tip => tip.viewed_at).length}
            </div>
            <div className="text-sm text-gray-600">Tips Read</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-purple-600">
              {tipHistory.filter(tip => tip.interaction_type === 'saved').length}
            </div>
            <div className="text-sm text-gray-600">Favorites</div>
          </CardContent>
        </Card>
      </div>

      {/* Tips List */}
      <div className="space-y-6">
        {tipHistory.length === 0 ? (
          <Card className="w-full">
            <CardContent className="p-8 text-center">
              <div className="text-6xl mb-4">💡</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Tips Found</h3>
              <p className="text-gray-600">Tips will appear here as you receive them daily.</p>
            </CardContent>
          </Card>
        ) : (
          tipHistory.map((tip, index) => (
            <Card key={tip.tip_id || index} className="w-full hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{tip.icon || '💡'}</span>
                    <div>
                      <h3 className="font-semibold text-lg text-gray-900">{tip.tip_title}</h3>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-sm text-gray-500">{formatDate(tip.sent_at)}</span>
                        {tip.metadata?.category && (
                          <Badge className={getCategoryColor(tip.metadata.category)}>
                            {tip.metadata.category}
                          </Badge>
                        )}
                        {tip.metadata?.generated_by === 'ai' && (
                          <Badge variant="outline" className="text-xs">
                            🤖 AI Generated
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {tip.viewed_at && (
                      <Badge variant="secondary" className="text-xs">
                        ✓ Read
                      </Badge>
                    )}
                    {tip.interaction_type === 'saved' && (
                      <Badge className="bg-yellow-100 text-yellow-800 text-xs">
                        ⭐ Saved
                      </Badge>
                    )}
                  </div>
                </div>

                <div className="mb-4">
                  <p className="text-gray-700 leading-relaxed">{tip.tip_content}</p>
                </div>

                {/* Additional metadata */}
                {tip.metadata && Object.keys(tip.metadata).length > 2 && (
                  <div className="bg-gray-50 rounded-lg p-3 mt-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Additional Info:</h4>
                    <div className="text-xs text-gray-600 space-y-1">
                      {Object.entries(tip.metadata).map(([key, value]) => {
                        if (key === 'category' || key === 'generated_by') return null;
                        return (
                          <div key={key} className="flex justify-between">
                            <span className="capitalize">{key.replace('_', ' ')}:</span>
                            <span>{typeof value === 'object' ? JSON.stringify(value) : value}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Interactions */}
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    {tip.viewed_at && (
                      <span>👁️ Viewed {new Date(tip.viewed_at).toLocaleDateString()}</span>
                    )}
                    {tip.interaction_count > 0 && (
                      <span>⚡ {tip.interaction_count} interactions</span>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        const tipText = `${tip.tip_title}\n\n${tip.tip_content}\n\n- EarnNest Daily Tips`;
                        navigator.clipboard.writeText(tipText);
                        alert('Tip copied to clipboard!');
                      }}
                    >
                      📤 Share
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Load More Button */}
      {hasMore && tipHistory.length > 0 && (
        <div className="flex justify-center mt-8">
          <Button
            onClick={loadMoreTips}
            disabled={loading}
            variant="outline"
            className="px-8"
          >
            {loading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                <span>Loading...</span>
              </div>
            ) : (
              'Load More Tips'
            )}
          </Button>
        </div>
      )}
    </div>
  );
};

export default TipsHistory;
