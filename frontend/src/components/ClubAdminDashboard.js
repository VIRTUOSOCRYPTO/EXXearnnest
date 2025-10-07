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
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      // For now, show basic info since backend endpoints for club admin need to be created
      setDashboardData({
        club_name: user?.club_name || "Club Admin",
        events_created: 0,
        participants_managed: 0,
        pending_approvals: 0
      });
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
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

  if (!user?.admin_level || user.admin_level !== 'club_admin') {
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

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Club Admin Dashboard</h1>
            <p className="text-purple-100">
              Welcome back! Manage your club events and activities.
            </p>
          </div>
          <Shield className="w-16 h-16 opacity-50" />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Events Created
            </CardTitle>
            <Calendar className="w-5 h-5 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {dashboardData?.events_created || 0}
            </div>
            <p className="text-xs text-gray-500 mt-1">Total club events</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Participants
            </CardTitle>
            <Users className="w-5 h-5 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {dashboardData?.participants_managed || 0}
            </div>
            <p className="text-xs text-gray-500 mt-1">Managed successfully</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Pending Approvals
            </CardTitle>
            <AlertCircle className="w-5 h-5 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {dashboardData?.pending_approvals || 0}
            </div>
            <p className="text-xs text-gray-500 mt-1">Awaiting action</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Quick Actions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-gray-600 mb-4">
            Manage your club events and activities from here.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button className="bg-purple-600 hover:bg-purple-700">
              <Calendar className="w-4 h-4 mr-2" />
              Create Club Event
            </Button>
            <Button variant="outline" className="border-purple-600 text-purple-600 hover:bg-purple-50">
              <Users className="w-4 h-4 mr-2" />
              Manage Participants
            </Button>
            <Button variant="outline" className="border-purple-600 text-purple-600 hover:bg-purple-50">
              <Trophy className="w-4 h-4 mr-2" />
              View Competitions
            </Button>
            <Button variant="outline" className="border-purple-600 text-purple-600 hover:bg-purple-50">
              <TrendingUp className="w-4 h-4 mr-2" />
              Analytics
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No recent activities to display</p>
            <p className="text-sm mt-2">Start creating events to see activity here</p>
          </div>
        </CardContent>
      </Card>

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
                You can now create and manage club events, competitions, and activities within your college.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ClubAdminDashboard;
