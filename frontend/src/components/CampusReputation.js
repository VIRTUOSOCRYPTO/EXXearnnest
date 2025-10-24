import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Trophy, 
  TrendingUp, 
  Users, 
  DollarSign,
  Activity,
  RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CampusReputation = () => {
  const { user } = useAuth();
  const [campusLeaderboard, setCampusLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const fetchCampusReputation = useCallback(async (showToast = false) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/campus/reputation`);
      setCampusLeaderboard(response.data.campus_leaderboard || []);
      setLastUpdated(new Date());
      if (showToast) {
        toast.success('Rankings refreshed successfully!');
      }
    } catch (error) {
      console.error('Error fetching campus reputation:', error);
      if (showToast) {
        toast.error('Failed to refresh rankings');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCampusReputation();
  }, [fetchCampusReputation]);

  // Auto-refresh every 30 seconds if enabled
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchCampusReputation();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, fetchCampusReputation]);

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: true 
    });
  };

  const formatNumber = (num) => {
    return num?.toLocaleString('en-IN') || '0';
  };

  const getTrendingCampus = () => {
    if (!campusLeaderboard.length) return null;
    return campusLeaderboard[0];
  };

  const getCardColor = (index) => {
    if (index === 0) return 'bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600';
    if (index === 1) return 'bg-gradient-to-r from-gray-300 via-gray-400 to-gray-500';
    if (index === 2) return 'bg-gradient-to-r from-orange-300 via-orange-400 to-orange-500';
    return 'bg-gradient-to-r from-gray-200 via-gray-300 to-gray-400';
  };

  const CampusCard = ({ campus, index }) => {
    const isUserCampus = campus.campus === user?.university;
    const totalSaved = campus.financial_literacy * 1000 || 0; // Convert points back to rupees
    const avgSaved = totalSaved / Math.max(campus.active_students, 1);
    
    return (
      <Card className={`${getCardColor(index)} text-white shadow-2xl hover:shadow-3xl transition-all duration-300 border-none`}>
        <CardContent className="p-8">
          <div className="flex justify-between items-start">
            <div className="flex items-start gap-6 flex-1">
              <div className="bg-white bg-opacity-20 rounded-full p-4 backdrop-blur-sm">
                <Trophy className="w-10 h-10" />
              </div>
              
              <div className="flex-1">
                <h2 className="text-3xl font-bold mb-4 flex items-center gap-3">
                  {campus.campus}
                  {isUserCampus && (
                    <Badge className="bg-white text-blue-600 hover:bg-white">
                      Your Campus
                    </Badge>
                  )}
                </h2>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-5 h-5 opacity-80" />
                    <div>
                      <div className="opacity-80 text-xs">Total Saved</div>
                      <div className="font-bold text-lg">₹{formatNumber(totalSaved)}</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 opacity-80" />
                    <div>
                      <div className="opacity-80 text-xs">Active</div>
                      <div className="font-bold text-lg">
                        {campus.active_students}/{campus.total_students}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-5 h-5 opacity-80" />
                    <div>
                      <div className="opacity-80 text-xs">Avg</div>
                      <div className="font-bold text-lg">₹{formatNumber(Math.round(avgSaved))}</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Activity className="w-5 h-5 opacity-80" />
                    <div>
                      <div className="opacity-80 text-xs">Activity</div>
                      <div className="font-bold text-lg">{campus.competition_wins || 0}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="text-right ml-6">
              <div className="text-6xl font-bold mb-2">#{index + 1}</div>
              <div className="text-2xl font-bold">
                ₹{formatNumber(totalSaved)} earned
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const trendingCampus = getTrendingCampus();

  if (loading && campusLeaderboard.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 via-purple-700 to-blue-800 p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-white text-xl">Loading live rankings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-500 via-purple-600 to-blue-700 p-6">
      {/* Trending Badge */}
      {trendingCampus && (
        <div className="flex justify-center mb-12 animate-pulse">
          <Badge className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-8 py-4 text-xl font-bold rounded-full shadow-2xl border-none">
            <TrendingUp className="w-6 h-6 mr-2" />
            Trending: {trendingCampus.campus}
          </Badge>
        </div>
      )}

      {/* Header Section */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-white">
            <h1 className="text-4xl md:text-5xl font-bold mb-2">Live Rankings</h1>
            <p className="text-lg opacity-90">
              Last updated: {formatTime(lastUpdated)}
            </p>
          </div>
          
          <div className="flex gap-3">
            <Button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`${
                autoRefresh 
                  ? 'bg-green-500 hover:bg-green-600' 
                  : 'bg-gray-500 hover:bg-gray-600'
              } text-white px-6 py-6 text-lg font-semibold rounded-xl shadow-lg`}
            >
              <RefreshCw className={`w-5 h-5 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
              Auto-Refresh {autoRefresh ? 'ON' : 'OFF'}
            </Button>
            
            <Button
              onClick={() => fetchCampusReputation(true)}
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-6 text-lg font-semibold rounded-xl shadow-lg"
            >
              <RefreshCw className={`w-5 h-5 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh Now
            </Button>
          </div>
        </div>
      </div>

      {/* Rankings */}
      <div className="max-w-7xl mx-auto space-y-6">
        {campusLeaderboard.length === 0 ? (
          <Card className="bg-white bg-opacity-10 backdrop-blur-lg border-none">
            <CardContent className="p-12 text-center">
              <Trophy className="w-16 h-16 text-white mx-auto mb-4 opacity-50" />
              <h3 className="text-2xl font-semibold text-white mb-2">No Rankings Yet</h3>
              <p className="text-white opacity-80">Campus rankings will appear as students participate in activities.</p>
            </CardContent>
          </Card>
        ) : (
          campusLeaderboard.map((campus, index) => (
            <CampusCard key={campus.campus} campus={campus} index={index} />
          ))
        )}
      </div>
    </div>
  );
};

export default CampusReputation;
