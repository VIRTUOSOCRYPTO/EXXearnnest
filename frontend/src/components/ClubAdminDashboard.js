import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Trophy, Users, Calendar, Award, Target, Shield, 
  AlertCircle, CheckCircle, Clock, Activity, TrendingUp
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ClubAdminDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [competitions, setCompetitions] = useState([]);
  const [challenges, setChallenges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    fetchCompetitions();
    fetchChallenges();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/club-admin/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      if (error.response?.status === 403) {
        alert('You do not have club admin privileges. Please contact your campus admin for access.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchCompetitions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/club-admin/competitions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setCompetitions(response.data.competitions || []);
    } catch (error) {
      console.error('Error fetching competitions:', error);
    }
  };

  const fetchChallenges = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/club-admin/challenges`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setChallenges(response.data.challenges || []);
    } catch (error) {
      console.error('Error fetching challenges:', error);
    }
  };

  if (loading) {
    return (
      <Card className="w-full max-w-6xl mx-auto">
        <CardContent className="p-8">
          <div className="flex items-center justify-center space-x-4">
            <Clock className="w-6 h-6 animate-spin" />
            <span className="text-gray-600">Loading dashboard...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className="w-full max-w-6xl mx-auto">
        <CardContent className="p-8">
          <div className="flex items-center justify-center space-x-4">
            <Clock className="w-6 h-6 animate-spin" />
            <span className="text-gray-600">Loading club admin dashboard...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!dashboardData) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-8 text-center">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-800 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-4">
            You do not have club admin privileges. Please contact your campus admin for access.
          </p>
        </CardContent>
      </Card>
    );
  }

  const { admin_details, statistics, capabilities } = dashboardData;

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Club Admin Dashboard</h1>
            <p className="text-purple-100">
              {admin_details.club_name} - {admin_details.college_name}
            </p>
          </div>
          <Shield className="w-16 h-16 opacity-50" />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Events
            </CardTitle>
            <Trophy className="w-5 h-5 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {statistics.total_events}
            </div>
            <p className="text-xs text-gray-500 mt-1">Competitions + Challenges</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Competitions
            </CardTitle>
            <Calendar className="w-5 h-5 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {statistics.total_competitions}
            </div>
            <p className="text-xs text-gray-500 mt-1">Inter-college events</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Challenges
            </CardTitle>
            <Award className="w-5 h-5 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {statistics.total_challenges}
            </div>
            <p className="text-xs text-gray-500 mt-1">Prize challenges</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Participants
            </CardTitle>
            <Users className="w-5 h-5 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {statistics.participants_managed}
            </div>
            <p className="text-xs text-gray-500 mt-1">Total managed</p>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Quota Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Target className="w-5 h-5 mr-2" />
            Monthly Event Creation Quota
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">
                Used: {statistics.events_this_month} / {capabilities.max_events_per_month}
              </span>
              <span className="text-sm text-gray-600">
                {statistics.remaining_monthly_quota} remaining
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-purple-600 h-2 rounded-full"
                style={{ width: `${(statistics.events_this_month / capabilities.max_events_per_month) * 100}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Quick Actions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button 
              className="bg-blue-600 hover:bg-blue-700"
              onClick={() => window.location.href = '/create-competition'}
              disabled={!capabilities.can_create_competitions || statistics.remaining_monthly_quota === 0}
            >
              <Trophy className="w-4 h-4 mr-2" />
              Create Inter-College Competition
            </Button>
            <Button 
              className="bg-green-600 hover:bg-green-700"
              onClick={() => window.location.href = '/create-challenge'}
              disabled={!capabilities.can_create_challenges || statistics.remaining_monthly_quota === 0}
            >
              <Award className="w-4 h-4 mr-2" />
              Create Prize Challenge
            </Button>
            <Button 
              variant="outline" 
              className="border-purple-600 text-purple-600 hover:bg-purple-50"
              onClick={() => window.location.href = '/campus-reputation'}
            >
              <TrendingUp className="w-4 h-4 mr-2" />
              View Campus Reputation
            </Button>
            <Button 
              variant="outline" 
              className="border-purple-600 text-purple-600 hover:bg-purple-50"
              onClick={() => window.location.href = '/group-challenges'}
            >
              <Users className="w-4 h-4 mr-2" />
              View Group Challenges
            </Button>
          </div>
          {statistics.remaining_monthly_quota === 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-4">
              <p className="text-sm text-yellow-800">
                <AlertCircle className="w-4 h-4 inline mr-2" />
                You've reached your monthly event creation limit. Limit resets next month.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Competitions */}
      {competitions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="w-5 h-5" />
              Recent Competitions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {competitions.slice(0, 3).map((competition) => (
                <div key={competition.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{competition.title}</p>
                    <p className="text-xs text-gray-600">
                      {competition.current_participants || 0} participants • {new Date(competition.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Badge className={
                    competition.status === 'active' ? 'bg-green-500' :
                    competition.status === 'upcoming' ? 'bg-blue-500' :
                    'bg-gray-500'
                  }>
                    {competition.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Challenges */}
      {challenges.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="w-5 h-5" />
              Recent Challenges
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {challenges.slice(0, 3).map((challenge) => (
                <div key={challenge.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{challenge.title}</p>
                    <p className="text-xs text-gray-600">
                      ₹{challenge.total_prize_value?.toLocaleString()} • {challenge.current_participants || 0} participants
                    </p>
                  </div>
                  <Badge className={
                    challenge.status === 'active' ? 'bg-green-500' :
                    challenge.status === 'upcoming' ? 'bg-blue-500' :
                    'bg-gray-500'
                  }>
                    {challenge.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Banner */}
      <Card className="bg-purple-50 border-purple-200">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <CheckCircle className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-purple-900 mb-1">
                Club Admin Privileges Active
              </h3>
              <p className="text-purple-700 text-sm">
                You have been granted club admin privileges by your campus administrator. 
                You can create and manage competitions and challenges for {admin_details.club_name}.
              </p>
              <p className="text-purple-600 text-xs mt-2">
                Expires: {new Date(admin_details.expires_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ClubAdminDashboard;
