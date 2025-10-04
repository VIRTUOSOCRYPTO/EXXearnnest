import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Progress } from './ui/progress';
import { Trophy, Users, Calendar, Award, Target, Medal, Star } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const InterCollegeCompetitions = () => {
  const { user } = useAuth();
  const [competitions, setCompetitions] = useState([]);
  const [selectedCompetition, setSelectedCompetition] = useState(null);
  const [leaderboard, setLeaderboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [registering, setRegistering] = useState(false);
  const [activeTab, setActiveTab] = useState("all");

  useEffect(() => {
    fetchCompetitions();
  }, []);

  const fetchCompetitions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/inter-college/competitions`);
      setCompetitions(response.data.competitions || []);
    } catch (error) {
      console.error('Error fetching competitions:', error);
    } finally {
      setLoading(false);
    }
  };

  const registerForCompetition = async (competitionId) => {
    try {
      setRegistering(true);
      const response = await axios.post(`${API}/inter-college/competitions/${competitionId}/register`);
      
      // Update the competition status locally
      setCompetitions(prev => prev.map(comp => 
        comp.id === competitionId 
          ? { ...comp, is_registered: true, campus_participants: response.data.campus_participants }
          : comp
      ));

      alert(`Successfully registered! ${response.data.message}`);
    } catch (error) {
      console.error('Registration error:', error);
      alert(error.response?.data?.detail || 'Failed to register for competition');
    } finally {
      setRegistering(false);
    }
  };

  const fetchLeaderboard = async (competitionId) => {
    try {
      const response = await axios.get(`${API}/inter-college/competitions/${competitionId}/leaderboard`);
      setLeaderboard(response.data);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    }
  };

  const getCompetitionStatusBadge = (competition) => {
    const now = new Date();
    const startDate = new Date(competition.start_date);
    const endDate = new Date(competition.end_date);
    const regStart = new Date(competition.registration_start);
    const regEnd = new Date(competition.registration_end);

    if (now < regStart) {
      return <Badge variant="outline" className="bg-gray-100">Registration Opens Soon</Badge>;
    } else if (now >= regStart && now <= regEnd) {
      return <Badge variant="default" className="bg-green-500">Registration Open</Badge>;
    } else if (now > regEnd && now < startDate) {
      return <Badge variant="secondary">Registration Closed</Badge>;
    } else if (now >= startDate && now <= endDate) {
      return <Badge variant="default" className="bg-blue-500">Active Competition</Badge>;
    } else {
      return <Badge variant="outline" className="bg-red-100">Ended</Badge>;
    }
  };

  const getTimeRemaining = (targetDate) => {
    const now = new Date();
    const target = new Date(targetDate);
    const diff = target - now;
    
    if (diff <= 0) return "Ended";
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    
    if (days > 0) return `${days} days ${hours}h remaining`;
    return `${hours}h remaining`;
  };

  const filteredCompetitions = competitions.filter(competition => {
    switch (activeTab) {
      case "registered":
        return competition.is_registered;
      case "eligible":
        return competition.is_eligible && !competition.is_registered;
      case "active":
        return competition.status === "active";
      default:
        return true;
    }
  });

  const CompetitionCard = ({ competition }) => (
    <Card className="hover:shadow-lg transition-shadow duration-200 border-l-4 border-l-blue-500">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <CardTitle className="text-xl font-bold text-gray-800 mb-2">
              {competition.title}
            </CardTitle>
            <p className="text-gray-600 text-sm mb-3">{competition.description}</p>
            <div className="flex flex-wrap gap-2">
              {getCompetitionStatusBadge(competition)}
              {competition.is_registered && (
                <Badge variant="default" className="bg-emerald-500">
                  <Users className="w-3 h-3 mr-1" />
                  Registered
                </Badge>
              )}
              {!competition.is_eligible && (
                <Badge variant="destructive">Not Eligible</Badge>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-600">
              ₹{(competition.prize_pool || 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">Prize Pool</div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <Calendar className="w-5 h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-sm font-medium">Duration</div>
            <div className="text-xs text-gray-600">{competition.duration_days} days</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <Users className="w-5 h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-sm font-medium">Campus Rank</div>
            <div className="text-xs text-gray-600">#{competition.campus_rank || 'N/A'}</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <Target className="w-5 h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-sm font-medium">Target</div>
            <div className="text-xs text-gray-600">{competition.target_metric}</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <Trophy className="w-5 h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-sm font-medium">Participants</div>
            <div className="text-xs text-gray-600">{competition.campus_participants || 0}</div>
          </div>
        </div>

        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-sm">
            <span>Registration: {new Date(competition.registration_start).toLocaleDateString()}</span>
            <span>Ends: {new Date(competition.registration_end).toLocaleDateString()}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Competition: {new Date(competition.start_date).toLocaleDateString()}</span>
            <span>Ends: {new Date(competition.end_date).toLocaleDateString()}</span>
          </div>
        </div>

        <div className="flex gap-2">
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => {
                  setSelectedCompetition(competition);
                  fetchLeaderboard(competition.id);
                }}
              >
                <Trophy className="w-4 h-4 mr-2" />
                View Leaderboard
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Trophy className="w-5 h-5" />
                  {selectedCompetition?.title} - Leaderboard
                </DialogTitle>
              </DialogHeader>
              {leaderboard && <LeaderboardContent leaderboard={leaderboard} />}
            </DialogContent>
          </Dialog>

          {!competition.is_registered && competition.is_eligible && competition.registration_open && (
            <Button
              onClick={() => registerForCompetition(competition.id)}
              disabled={registering}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
            >
              <Users className="w-4 h-4 mr-2" />
              {registering ? 'Registering...' : 'Register Now'}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const LeaderboardContent = ({ leaderboard }) => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Campus Leaderboard */}
        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-yellow-500" />
            Campus Rankings
          </h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {leaderboard.campus_leaderboard?.map((campus, index) => (
              <div
                key={campus.campus}
                className={`p-3 rounded-lg border ${
                  campus.campus === user?.university 
                    ? 'bg-blue-50 border-blue-200' 
                    : 'bg-gray-50'
                }`}
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      index === 0 ? 'bg-yellow-400' : 
                      index === 1 ? 'bg-gray-300' : 
                      index === 2 ? 'bg-orange-300' : 'bg-gray-200'
                    }`}>
                      {index + 1}
                    </div>
                    <div>
                      <div className="font-medium">{campus.campus}</div>
                      <div className="text-sm text-gray-600">
                        {campus.total_participants} participants
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-blue-600">
                      {campus.campus_total_score || 0}
                    </div>
                    <div className="text-xs text-gray-500">points</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Individual Performers */}
        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Star className="w-5 h-5 text-purple-500" />
            Top Performers
          </h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {leaderboard.top_individuals?.map((participant, index) => (
              <div
                key={participant.user_id}
                className={`p-3 rounded-lg border ${
                  participant.user_id === user?.id 
                    ? 'bg-purple-50 border-purple-200' 
                    : 'bg-gray-50'
                }`}
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      index === 0 ? 'bg-yellow-400' : 
                      index === 1 ? 'bg-gray-300' : 
                      index === 2 ? 'bg-orange-300' : 'bg-gray-200'
                    }`}>
                      {index + 1}
                    </div>
                    <div>
                      <div className="font-medium">{participant.user_name}</div>
                      <div className="text-sm text-gray-600">{participant.campus}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-purple-600">
                      {participant.individual_score || 0}
                    </div>
                    <div className="text-xs text-gray-500">points</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* User Stats */}
      {leaderboard.user_stats?.is_registered && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border">
          <h4 className="font-semibold mb-2">Your Performance</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-600">Campus Rank</div>
              <div className="font-bold text-blue-600">
                #{leaderboard.user_stats.campus_rank || 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Individual Score</div>
              <div className="font-bold text-purple-600">
                {leaderboard.user_stats.individual_participation?.individual_score || 0}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading competitions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <Trophy className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-800">Inter-College Competitions</h1>
        </div>
        <p className="text-gray-600 text-lg">
          Compete with students from other universities and showcase your campus pride!
        </p>
        {user?.university && (
          <div className="mt-2">
            <Badge variant="outline" className="bg-blue-50 border-blue-200">
              <Users className="w-3 h-3 mr-1" />
              Representing: {user.university}
            </Badge>
          </div>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:grid-cols-4">
          <TabsTrigger value="all">All Competitions</TabsTrigger>
          <TabsTrigger value="eligible">Eligible</TabsTrigger>
          <TabsTrigger value="registered">My Competitions</TabsTrigger>
          <TabsTrigger value="active">Active Now</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4 mt-6">
          {filteredCompetitions.length === 0 ? (
            <div className="text-center py-12">
              <Trophy className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No competitions available</h3>
              <p className="text-gray-500">Check back later for new inter-college competitions!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredCompetitions.map((competition) => (
                <CompetitionCard key={competition.id} competition={competition} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="eligible" className="space-y-4 mt-6">
          {filteredCompetitions.length === 0 ? (
            <div className="text-center py-12">
              <Award className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No eligible competitions</h3>
              <p className="text-gray-500">Complete more achievements to unlock competition eligibility!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredCompetitions.map((competition) => (
                <CompetitionCard key={competition.id} competition={competition} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="registered" className="space-y-4 mt-6">
          {filteredCompetitions.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No registered competitions</h3>
              <p className="text-gray-500">Register for competitions to represent your campus!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredCompetitions.map((competition) => (
                <CompetitionCard key={competition.id} competition={competition} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="active" className="space-y-4 mt-6">
          {filteredCompetitions.length === 0 ? (
            <div className="text-center py-12">
              <Medal className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No active competitions</h3>
              <p className="text-gray-500">Stay tuned for upcoming active competitions!</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
              {filteredCompetitions.map((competition) => (
                <CompetitionCard key={competition.id} competition={competition} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default InterCollegeCompetitions;
