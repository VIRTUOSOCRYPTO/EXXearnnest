import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Users, 
  Banknote, 
  Share, 
  Download, 
  ExternalLink,
  Newspaper,
  BarChart3,
  Globe
} from 'lucide-react';

const ImpactStats = () => {
  const [stories, setStories] = useState([]);
  const [summaryStats, setSummaryStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchImpactStats();
  }, []);

  const fetchImpactStats = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/public/impact-stats`);
      const data = await response.json();
      
      if (data.success) {
        setStories(data.impact_stories || []);
        setSummaryStats(data.summary_stats || {});
        setLastUpdated(new Date(data.last_updated));
      }
    } catch (error) {
      console.error('Error fetching impact stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const shareStory = async (story) => {
    const shareText = `📰 ${story.headline} 
    
${story.description}

#EarnNest #StudentFinance #FinTech #IndiaStudents`;

    if (navigator.share) {
      try {
        await navigator.share({
          title: story.headline,
          text: shareText,
          url: window.location.href
        });
      } catch (error) {
        console.log('Share cancelled');
      }
    } else {
      navigator.clipboard.writeText(shareText);
      alert('Impact story copied to clipboard! Perfect for sharing with media 📰');
    }
  };

  const downloadPressKit = (story) => {
    const pressRelease = `
FOR IMMEDIATE RELEASE

${story.headline}

${story.description}

About EarnNest:
EarnNest is India's leading student finance platform, helping students track expenses, save money, and earn through side hustles. Our mission is to empower the next generation with financial literacy and independence.

Press Contact:
Media Team - EarnNest
Email: press@earnnest.com
Website: ${window.location.origin}

###

Generated on: ${new Date().toLocaleDateString()}
Source: EarnNest Impact Analytics
`;

    const blob = new Blob([pressRelease], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = `${story.category}_press_release.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const formatAmount = (amount) => {
    if (amount >= 10000000) {
      return `₹${(amount / 10000000).toFixed(1)} crore`;
    } else if (amount >= 100000) {
      return `₹${(amount / 100000).toFixed(1)} lakh`;
    } else if (amount >= 1000) {
      return `₹${(amount / 1000).toFixed(1)}K`;
    }
    return `₹${amount?.toLocaleString() || 0}`;
  };

  const getCategoryIcon = (category) => {
    const icons = {
      'savings_milestone': '💰',
      'earnings_report': '📈',
      'campus_comparison': '🏛️',
      'activity_report': '⚡'
    };
    return icons[category] || '📊';
  };

  const getCategoryColor = (category) => {
    const colors = {
      'savings_milestone': 'from-green-500 to-emerald-600',
      'earnings_report': 'from-blue-500 to-indigo-600',
      'campus_comparison': 'from-purple-500 to-pink-600',
      'activity_report': 'from-orange-500 to-red-500'
    };
    return colors[category] || 'from-gray-500 to-gray-700';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
        <div className="max-w-6xl mx-auto animate-pulse">
          <div className="h-12 bg-gray-300 rounded w-1/2 mb-8"></div>
          <div className="grid gap-8">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-48 bg-gray-300 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-blue-700 text-white py-16">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <h1 className="text-5xl md:text-6xl font-extrabold mb-6 bg-gradient-to-r from-yellow-300 to-pink-300 bg-clip-text text-transparent">
            📰 Media Impact Center
          </h1>
          <p className="text-2xl text-blue-100 max-w-4xl mx-auto mb-8">
            Press-ready insights and data stories showcasing India's student finance revolution
          </p>
          
          {summaryStats.total_users && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                <div className="text-3xl font-bold">{summaryStats.total_users.toLocaleString()}</div>
                <div className="text-blue-200">Active Students</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                <div className="text-3xl font-bold">{formatAmount(summaryStats.total_savings)}</div>
                <div className="text-blue-200">Total Saved</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                <div className="text-3xl font-bold">{formatAmount(summaryStats.total_earnings)}</div>
                <div className="text-blue-200">Total Earned</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                <div className="text-3xl font-bold">{summaryStats.active_campuses}</div>
                <div className="text-blue-200">Active Campuses</div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Update Info */}
        <div className="text-center mb-12">
          <div className="bg-white rounded-full px-6 py-3 inline-flex items-center gap-2 shadow-md">
            <Globe className="w-5 h-5 text-blue-600" />
            <span className="font-medium text-gray-700">
              Last Updated: {lastUpdated?.toLocaleDateString()} • Weekly Refresh Schedule
            </span>
          </div>
        </div>

        {stories.length === 0 ? (
          <div className="text-center bg-white rounded-2xl p-12 shadow-lg">
            <Newspaper className="w-16 h-16 mx-auto mb-6 text-gray-400" />
            <h3 className="text-2xl font-bold text-gray-800 mb-4">
              Impact Stories Loading...
            </h3>
            <p className="text-gray-600 max-w-md mx-auto">
              Our analytics engine is processing the latest student finance data to generate fresh impact stories.
            </p>
          </div>
        ) : (
          <div className="grid gap-8">
            <h2 className="text-3xl font-bold text-gray-800 text-center mb-8 flex items-center justify-center gap-3">
              <BarChart3 className="w-8 h-8 text-indigo-600" />
              Press-Ready Data Stories
            </h2>

            {stories.map((story, index) => (
              <div
                key={index}
                className={`relative overflow-hidden bg-gradient-to-r ${getCategoryColor(story.category)} rounded-2xl p-8 text-white shadow-2xl`}
              >
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-10">
                  <div className="grid grid-cols-8 gap-4 h-full">
                    {[...Array(64)].map((_, i) => (
                      <div key={i} className="bg-white/20 rounded-full"></div>
                    ))}
                  </div>
                </div>

                <div className="relative z-10">
                  <div className="flex items-start justify-between mb-6">
                    <div className="flex items-center gap-4">
                      <span className="text-6xl">{getCategoryIcon(story.category)}</span>
                      <div>
                        <div className="text-sm text-white/70 uppercase tracking-wide font-medium mb-2">
                          {story.category.replace('_', ' ')}
                        </div>
                        <h3 className="text-3xl md:text-4xl font-bold leading-tight mb-3">
                          {story.headline}
                        </h3>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-4xl font-extrabold">{story.stat}</div>
                      <div className="text-sm text-white/70">Key Metric</div>
                    </div>
                  </div>

                  <p className="text-xl text-white/90 mb-8 leading-relaxed">
                    {story.description}
                  </p>

                  <div className="flex flex-wrap gap-4">
                    <button
                      onClick={() => shareStory(story)}
                      className="bg-white/20 backdrop-blur-sm border border-white/30 hover:bg-white/30 px-6 py-3 rounded-full transition-all duration-300 flex items-center gap-2 font-medium"
                    >
                      <Share className="w-5 h-5" />
                      Share Story
                    </button>

                    <button
                      onClick={() => downloadPressKit(story)}
                      className="bg-white/20 backdrop-blur-sm border border-white/30 hover:bg-white/30 px-6 py-3 rounded-full transition-all duration-300 flex items-center gap-2 font-medium"
                    >
                      <Download className="w-5 h-5" />
                      Press Kit
                    </button>

                    {story.shareable && (
                      <span className="bg-green-500/20 text-green-100 px-4 py-2 rounded-full text-sm flex items-center gap-2">
                        <ExternalLink className="w-4 h-4" />
                        Media Ready
                      </span>
                    )}
                  </div>
                </div>

                {/* Decorative Elements */}
                <div className="absolute top-0 right-0 transform translate-x-16 -translate-y-16">
                  <div className="w-64 h-64 bg-white/5 rounded-full"></div>
                </div>
                <div className="absolute bottom-0 left-0 transform -translate-x-8 translate-y-8">
                  <div className="w-32 h-32 bg-white/5 rounded-full"></div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Media Contact Section */}
        <div className="mt-16 bg-white rounded-2xl p-8 shadow-lg">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-800 mb-4">Media Inquiries</h3>
            <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
              For additional data, interviews, or custom reports about India's student finance trends, 
              contact our media team.
            </p>
            
            <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto">
              <div className="text-center">
                <h4 className="font-semibold text-gray-800 mb-2">Press Contact</h4>
                <p className="text-gray-600">press@earnnest.com</p>
              </div>
              <div className="text-center">
                <h4 className="font-semibold text-gray-800 mb-2">Data Requests</h4>
                <p className="text-gray-600">Analytics team available</p>
              </div>
              <div className="text-center">
                <h4 className="font-semibold text-gray-800 mb-2">Response Time</h4>
                <p className="text-gray-600">Within 24 hours</p>
              </div>
            </div>

            <div className="mt-8 flex flex-wrap justify-center gap-4">
              <button className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-8 py-3 rounded-full font-semibold hover:shadow-lg transition-all duration-300">
                Request Custom Report 📊
              </button>
              <button className="bg-transparent border-2 border-indigo-600 text-indigo-600 px-8 py-3 rounded-full font-semibold hover:bg-indigo-50 transition-all duration-300">
                Schedule Interview 🎤
              </button>
            </div>
          </div>
        </div>

        {/* Footer CTA */}
        <div className="mt-16 bg-gradient-to-r from-green-600 to-blue-600 rounded-2xl p-8 text-center text-white">
          <h3 className="text-3xl font-bold mb-4">Be Part of the Story! 🚀</h3>
          <p className="text-xl text-green-100 mb-6 max-w-2xl mx-auto">
            Every student who joins EarnNest contributes to these incredible impact stories. 
            Help us change India's financial future, one student at a time.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <button 
              onClick={() => window.location.href = '/register'}
              className="bg-white text-green-600 px-8 py-3 rounded-full font-bold text-lg hover:bg-gray-100 transition-colors"
            >
              Join the Movement 💪
            </button>
            <button 
              onClick={() => window.open('/public/campus-battle', '_blank')}
              className="bg-transparent border-2 border-white text-white px-8 py-3 rounded-full font-bold text-lg hover:bg-white hover:text-green-600 transition-colors"
            >
              View Live Data 📈
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImpactStats;
