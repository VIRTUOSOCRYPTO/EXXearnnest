import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Progress } from './ui/progress';
import { 
  University, 
  Trophy, 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Star, 
  Award, 
  Calendar,
  Target,
  BookOpen,
  DollarSign,
  UserCheck,
  Activity
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CampusReputation = () => {
  const { user } = useAuth();
  const [campusLeaderboard, setCampusLeaderboard] = useState([]);
  const [userCampusStats, setUserCampusStats] = useState(null);
  const [recentActivities, setRecentActivities] = useState([]);
  const [selectedCampus, setSelectedCampus] = useState(null);
  const [campusDetails, setCampusDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCampusReputation();
  }, []);

  const fetchCampusReputation = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/campus/reputation`);
      setCampusLeaderboard(response.data.campus_leaderboard || []);
      setUserCampusStats(response.data.user_campus_stats);
      setRecentActivities(response.data.recent_activities || []);
    } catch (error) {
      console.error('Error fetching campus reputation:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCampusDetails = async (campusName) => {
    try {
      const response = await axios.get(`${API}/campus/reputation/${encodeURIComponent(campusName)}`);
      setCampusDetails(response.data);
    } catch (error) {
      console.error('Error fetching campus details:', error);
    }
  };

  const getRankChange = (currentRank, previousRank) => {
    if (!previousRank || previousRank === currentRank) return null;
    if (currentRank < previousRank) {
      return { type: 'up', change: previousRank - currentRank };
    }
    return { type: 'down', change: currentRank - previousRank };
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getReputationCategoryIcon = (category) => {
    switch (category) {
      case 'academic_performance': return <BookOpen className="w-4 h-4" />;
      case 'financial_literacy': return <DollarSign className="w-4 h-4" />;
      case 'community_engagement': return <Users className="w-4 h-4" />;
      case 'leadership': return <UserCheck className="w-4 h-4" />;
      case 'innovation': return <Star className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const CampusCard = ({ campus, index }) => {
    const rankChange = getRankChange(campus.current_rank, campus.previous_rank);
    
    return (
      <Card className={`hover:shadow-lg transition-shadow duration-200 ${
        campus.campus === user?.university ? 'border-l-4 border-l-blue-500 bg-blue-50' : ''
      }`}>
        <CardHeader className="pb-3">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold ${
                  index === 0 ? 'bg-yellow-400 text-yellow-900' : 
                  index === 1 ? 'bg-gray-300 text-gray-700' : 
                  index === 2 ? 'bg-orange-300 text-orange-900' : 'bg-gray-200 text-gray-600'
                }`}>
                  {campus.current_rank}
                </div>
                <div>
                  <CardTitle className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <University className="w-5 h-5" />
                    {campus.campus}
                  </CardTitle>
                  {campus.campus === user?.university && (
                    <Badge className="mt-1 bg-blue-500">Your Campus</Badge>
                  )}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-purple-600">
                {(campus.total_reputation_points || 0).toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Reputation Points</div>
              {rankChange && (
                <div className={`flex items-center gap-1 text-sm ${
                  rankChange.type === 'up' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {rankChange.type === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  {rankChange.change} ranks
                </div>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <Calendar className="w-5 h-5 mx-auto mb-1 text-gray-600" />
              <div className="text-sm font-medium">Monthly Points</div>
              <div className="text-xs text-gray-600">{campus.monthly_reputation_points || 0}</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <Users className="w-5 h-5 mx-auto mb-1 text-gray-600" />
              <div className="text-sm font-medium">Active Students</div>
              <div className="text-xs text-gray-600">{campus.total_active_students || 0}</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <Award className="w-5 h-5 mx-auto mb-1 text-gray-600" />
              <div className="text-sm font-medium">Avg Score</div>
              <div className="text-xs text-gray-600">{campus.average_student_score?.toFixed(1) || 0}</div>
            </div>
          </div>

          {/* Reputation Categories */}
          <div className="space-y-2 mb-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium flex items-center gap-1">
                {getReputationCategoryIcon('academic_performance')}
                Academic
              </span>
              <span className="text-sm text-gray-600">{campus.academic_performance || 0} pts</span>
            </div>
            <Progress value={(campus.academic_performance || 0) / 10} className="h-2" />
            
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium flex items-center gap-1">
                {getReputationCategoryIcon('financial_literacy')}
                Financial
              </span>
              <span className="text-sm text-gray-600">{campus.financial_literacy || 0} pts</span>
            </div>
            <Progress value={(campus.financial_literacy || 0) / 10} className="h-2" />
            
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium flex items-center gap-1">
                {getReputationCategoryIcon('community_engagement')}
                Community
              </span>
              <span className="text-sm text-gray-600">{campus.community_engagement || 0} pts</span>
            </div>
            <Progress value={(campus.community_engagement || 0) / 10} className="h-2" />
          </div>

          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  setSelectedCampus(campus);
                  fetchCampusDetails(campus.campus);
                }}
              >
                <Target className="w-4 h-4 mr-2" />
                View Details
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <University className="w-5 h-5" />
                  {selectedCampus?.campus} - Detailed Stats
                </DialogTitle>
              </DialogHeader>
              {campusDetails && <CampusDetailsContent campus={selectedCampus} details={campusDetails} />}
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    );
  };

  const CampusDetailsContent = ({ campus, details }) => (
    <div className="space-y-6">
      {/* Campus Overview */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="font-bold text-blue-600 text-lg">
              {details.campus_info?.total_students || 0}
            </div>
            <div className="text-sm text-gray-600">Total Students</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-green-600 text-lg">
              {details.campus_info?.active_students || 0}
            </div>
            <div className="text-sm text-gray-600">Active Students</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-purple-600 text-lg">
              {details.campus_info?.ambassadors_count || 0}
            </div>
            <div className="text-sm text-gray-600">Ambassadors</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-orange-600 text-lg">
              {details.monthly_stats?.points_earned || 0}
            </div>
            <div className="text-sm text-gray-600">Monthly Points</div>
          </div>
        </div>
      </div>

      {/* Reputation Breakdown */}
      <div>
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Star className="w-5 h-5 text-yellow-500" />
          Reputation Breakdown
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {details.campus_info?.reputation && Object.entries({
            academic_performance: 'Academic Performance',
            financial_literacy: 'Financial Literacy',
            community_engagement: 'Community Engagement',
            leadership: 'Leadership',
            innovation: 'Innovation'
          }).map(([key, label]) => (
            <div key={key} className="p-3 bg-gray-50 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium flex items-center gap-2">
                  {getReputationCategoryIcon(key)}
                  {label}
                </span>
                <span className="text-sm text-gray-600">
                  {details.campus_info.reputation[key] || 0} pts
                </span>
              </div>
              <Progress 
                value={(details.campus_info.reputation[key] || 0) / 10} 
                className="h-2" 
              />
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activities */}
      <div>
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-green-500" />
          Recent Reputation Activities
        </h3>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {details.reputation_history?.slice(0, 10).map((activity, index) => (
            <div key={index} className="p-3 bg-gray-50 rounded-lg border">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                    activity.transaction_type === 'earned' 
                      ? 'bg-green-100 text-green-600' 
                      : 'bg-red-100 text-red-600'
                  }`}>
                    {activity.transaction_type === 'earned' ? '+' : '-'}
                  </div>
                  <div>
                    <div className="font-medium text-sm">{activity.description || activity.source_type}</div>
                    <div className="text-xs text-gray-600">
                      {formatDate(activity.created_at)}
                    </div>
                  </div>
                </div>
                <div className={`text-right font-medium ${
                  activity.transaction_type === 'earned' 
                    ? 'text-green-600' 
                    : 'text-red-600'
                }`}>
                  {activity.transaction_type === 'earned' ? '+' : '-'}{activity.points}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Campus Ambassadors */}
      {details.ambassadors && details.ambassadors.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-purple-500" />
            Campus Ambassadors
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {details.ambassadors.map((ambassador, index) => (
              <div key={index} className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-medium">Ambassador #{index + 1}</div>
                    <div className="text-sm text-gray-600">
                      Score: {ambassador.performance_score || 0}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-purple-600">
                      {ambassador.monthly_referrals || 0}
                    </div>
                    <div className="text-xs text-gray-500">Referrals</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading campus reputation data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <Trophy className="w-8 h-8 text-purple-600" />
          <h1 className="text-3xl font-bold text-gray-800">Campus Reputation Dashboard</h1>
        </div>
        <p className="text-gray-600 text-lg">
          See how your campus ranks among universities based on student achievements and activities.
        </p>
        {user?.university && (
          <div className="mt-4 flex flex-wrap gap-2">
            <Badge variant="outline" className="bg-blue-50 border-blue-200">
              <University className="w-3 h-3 mr-1" />
              Your Campus: {user.university}
            </Badge>
            {userCampusStats && (
              <>
                <Badge variant="outline" className="bg-purple-50 border-purple-200">
                  Rank: #{userCampusStats.current_rank}
                </Badge>
                <Badge variant="outline" className="bg-green-50 border-green-200">
                  Points: {(userCampusStats.total_reputation_points || 0).toLocaleString()}
                </Badge>
              </>
            )}
          </div>
        )}
      </div>

      <Tabs defaultValue="leaderboard" className="mb-6">
        <TabsList className="grid w-full grid-cols-2 lg:w-auto lg:grid-cols-2">
          <TabsTrigger value="leaderboard">Campus Rankings</TabsTrigger>
          <TabsTrigger value="activities">Recent Activities</TabsTrigger>
        </TabsList>

        <TabsContent value="leaderboard" className="space-y-4 mt-6">
          {campusLeaderboard.length === 0 ? (
            <div className="text-center py-12">
              <University className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No campus data available</h3>
              <p className="text-gray-500">Campus reputation data will appear as students earn points.</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
              {campusLeaderboard.map((campus, index) => (
                <CampusCard key={campus.campus} campus={campus} index={index} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="activities" className="space-y-4 mt-6">
          {recentActivities.length === 0 ? (
            <div className="text-center py-12">
              <Activity className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No recent activities</h3>
              <p className="text-gray-500">Recent reputation activities will appear here.</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {recentActivities.map((activity, index) => (
                <Card key={index} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          activity.transaction_type === 'earned' 
                            ? 'bg-green-100 text-green-600' 
                            : 'bg-red-100 text-red-600'
                        }`}>
                          {activity.transaction_type === 'earned' ? '+' : '-'}
                        </div>
                        <div>
                          <div className="font-medium">{activity.campus}</div>
                          <div className="text-sm text-gray-600">
                            {activity.description || activity.source_type}
                          </div>
                          <div className="text-xs text-gray-500">
                            {formatDate(activity.created_at)}
                          </div>
                        </div>
                      </div>
                      <div className={`text-right font-bold text-lg ${
                        activity.transaction_type === 'earned' 
                          ? 'text-green-600' 
                          : 'text-red-600'
                      }`}>
                        {activity.transaction_type === 'earned' ? '+' : '-'}{activity.points}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CampusReputation;
