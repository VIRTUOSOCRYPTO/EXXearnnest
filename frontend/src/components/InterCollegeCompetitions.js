import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Progress } from './ui/progress';
import { Trophy, Users, Calendar, Award, Target, Medal, Star, Edit, Trash2 } from 'lucide-react';

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
  const [editingCompetition, setEditingCompetition] = useState(null);
  const [deleting, setDeleting] = useState(false);

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

  const updateCompetition = async (competitionId, updatedData) => {
    try {
      const response = await axios.put(`${API}/inter-college/competitions/${competitionId}`, updatedData);
      
      // Update the competition in the local state
      setCompetitions(prev => prev.map(comp => 
        comp.id === competitionId 
          ? { ...comp, ...response.data.competition }
          : comp
      ));
      
      alert('Competition updated successfully!');
      setEditingCompetition(null);
    } catch (error) {
      console.error('Update error:', error);
      alert(error.response?.data?.detail || 'Failed to update competition');
    }
  };

  const deleteCompetition = async (competitionId) => {
    if (!window.confirm('Are you sure you want to delete this competition? This action cannot be undone.')) {
      return;
    }

    try {
      setDeleting(true);
      await axios.delete(`${API}/inter-college/competitions/${competitionId}`);
      
      // Remove the competition from local state
      setCompetitions(prev => prev.filter(comp => comp.id !== competitionId));
      
      alert('Competition deleted successfully!');
    } catch (error) {
      console.error('Delete error:', error);
      alert(error.response?.data?.detail || 'Failed to delete competition');
    } finally {
      setDeleting(false);
    }
  };

  // Check if user can edit/delete competition (creator or super admin)
  const canManageCompetition = (competition) => {
    return user && (
      competition.creator_id === user.id || 
      user.is_admin || 
      user.is_super_admin ||
      user.admin_level === 'super_admin'
    );
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
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg sm:text-xl font-bold text-gray-800 mb-3 break-words leading-relaxed">
              {competition.title}
            </CardTitle>
            <p className="text-gray-600 text-sm mb-3 break-words leading-relaxed">{competition.description}</p>
            <div className="flex flex-wrap gap-2">
              {getCompetitionStatusBadge(competition)}
              {competition.is_registered && (
                <Badge variant="default" className="bg-emerald-500 flex-shrink-0">
                  <Users className="w-3 h-3 mr-1" />
                  <span className="whitespace-nowrap">Registered</span>
                </Badge>
              )}
              {!competition.is_eligible && (
                <Badge variant="destructive" className="whitespace-nowrap">Not Eligible</Badge>
              )}
            </div>
          </div>
          <div className="text-left sm:text-right flex-shrink-0">
            <div className="text-xl sm:text-2xl font-bold text-blue-600 break-words">
              ₹{(competition.prize_pool || 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500 whitespace-nowrap">Prize Pool</div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3 mb-4">
          <div className="text-center p-2 sm:p-3 bg-gray-50 rounded-lg">
            <Calendar className="w-4 h-4 sm:w-5 sm:h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-xs sm:text-sm font-medium mb-1">Duration</div>
            <div className="text-xs text-gray-600 break-words leading-tight">{competition.duration_days} days</div>
          </div>
          <div className="text-center p-2 sm:p-3 bg-gray-50 rounded-lg">
            <Users className="w-4 h-4 sm:w-5 sm:h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-xs sm:text-sm font-medium mb-1">Campus Rank</div>
            <div className="text-xs text-gray-600 break-words leading-tight">#{competition.campus_rank || 'N/A'}</div>
          </div>
          <div className="text-center p-2 sm:p-3 bg-gray-50 rounded-lg">
            <Target className="w-4 h-4 sm:w-5 sm:h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-xs sm:text-sm font-medium mb-1">Target</div>
            <div className="text-xs text-gray-600 break-words leading-tight">{competition.target_metric}</div>
          </div>
          <div className="text-center p-2 sm:p-3 bg-gray-50 rounded-lg">
            <Trophy className="w-4 h-4 sm:w-5 sm:h-5 mx-auto mb-1 text-gray-600" />
            <div className="text-xs sm:text-sm font-medium mb-1">Participants</div>
            <div className="text-xs text-gray-600 break-words leading-tight">{competition.campus_participants || 0}</div>
          </div>
        </div>

        <div className="space-y-2 mb-4">
          <div className="flex flex-col sm:flex-row sm:justify-between text-xs sm:text-sm gap-1">
            <span className="break-words">Registration: {new Date(competition.registration_start).toLocaleDateString()}</span>
            <span className="break-words">Ends: {new Date(competition.registration_end).toLocaleDateString()}</span>
          </div>
          <div className="flex flex-col sm:flex-row sm:justify-between text-xs sm:text-sm gap-1">
            <span className="break-words">Competition: {new Date(competition.start_date).toLocaleDateString()}</span>
            <span className="break-words">Ends: {new Date(competition.end_date).toLocaleDateString()}</span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-2">
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                className="w-full sm:flex-1"
                onClick={() => {
                  setSelectedCompetition(competition);
                  fetchLeaderboard(competition.id);
                }}
              >
                <Trophy className="w-4 h-4 mr-2 flex-shrink-0" />
                <span className="whitespace-nowrap">View Leaderboard</span>
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2 flex-wrap break-words leading-relaxed pr-8">
                  <Trophy className="w-5 h-5 flex-shrink-0" />
                  <span className="break-words">{selectedCompetition?.title} - Leaderboard</span>
                </DialogTitle>
              </DialogHeader>
              {leaderboard && <LeaderboardContent leaderboard={leaderboard} />}
            </DialogContent>
          </Dialog>

          {!competition.is_registered && competition.is_eligible && competition.registration_open && (
            <Button
              onClick={() => registerForCompetition(competition.id)}
              disabled={registering}
              className="w-full sm:flex-1 bg-blue-600 hover:bg-blue-700"
            >
              <Users className="w-4 h-4 mr-2 flex-shrink-0" />
              <span className="whitespace-nowrap">{registering ? 'Registering...' : 'Register Now'}</span>
            </Button>
          )}

          {/* Edit/Delete buttons for creators and super admins */}
          {canManageCompetition(competition) && (
            <>
              <Button
                variant="outline"
                onClick={() => setEditingCompetition(competition)}
                className="flex-shrink-0"
                title="Edit Competition"
              >
                <Edit className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                onClick={() => deleteCompetition(competition.id)}
                disabled={deleting}
                className="flex-shrink-0 border-red-200 text-red-600 hover:bg-red-50"
                title="Delete Competition"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const EditCompetitionDialog = ({ competition, onSave, onCancel }) => {
    const [formData, setFormData] = useState({
      title: competition.title || '',
      description: competition.description || '',
      prize_pool: competition.prize_pool || 0,
      duration_days: competition.duration_days || 7,
      target_metric: competition.target_metric || 'Savings Amount'
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      onSave(competition.id, formData);
    };

    return (
      <Dialog open={true} onOpenChange={onCancel}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Edit className="w-5 h-5" />
              Edit Competition
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Competition Title</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Prize Pool (₹)</label>
                <input
                  type="number"
                  value={formData.prize_pool}
                  onChange={(e) => setFormData({ ...formData, prize_pool: parseInt(e.target.value) || 0 })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Duration (Days)</label>
                <input
                  type="number"
                  value={formData.duration_days}
                  onChange={(e) => setFormData({ ...formData, duration_days: parseInt(e.target.value) || 7 })}
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  min="1"
                  max="365"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Target Metric</label>
              <select
                value={formData.target_metric}
                onChange={(e) => setFormData({ ...formData, target_metric: e.target.value })}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="Savings Amount">Savings Amount</option>
                <option value="Transaction Count">Transaction Count</option>
                <option value="Budget Adherence">Budget Adherence</option>
                <option value="Goal Completion">Goal Completion</option>
              </select>
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700">
                Save Changes
              </Button>
              <Button type="button" variant="outline" onClick={onCancel} className="flex-1">
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    );
  };

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
      {/* Edit Competition Dialog */}
      {editingCompetition && (
        <EditCompetitionDialog 
          competition={editingCompetition}
          onSave={updateCompetition}
          onCancel={() => setEditingCompetition(null)}
        />
      )}

      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4 flex-wrap">
          <Trophy className="w-6 h-6 sm:w-8 sm:h-8 text-blue-600 flex-shrink-0" />
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 break-words leading-tight">Inter-College Competitions</h1>
        </div>
        <p className="text-gray-600 text-base sm:text-lg break-words leading-relaxed mb-3">
          Compete with students from other universities and showcase your campus pride!
        </p>
        {user?.university && (
          <div className="mt-2">
            <Badge variant="outline" className="bg-blue-50 border-blue-200 inline-flex items-center gap-1 break-words max-w-full">
              <Users className="w-3 h-3 flex-shrink-0" />
              <span className="break-words">Representing: {user.university}</span>
            </Badge>
          </div>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <div className="overflow-x-auto scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0">
          <TabsList className="inline-flex w-auto min-w-full sm:w-auto gap-2">
            <TabsTrigger value="all" className="text-xs sm:text-sm whitespace-nowrap flex-shrink-0">All Competitions</TabsTrigger>
            <TabsTrigger value="eligible" className="text-xs sm:text-sm whitespace-nowrap flex-shrink-0">Eligible</TabsTrigger>
            <TabsTrigger value="registered" className="text-xs sm:text-sm whitespace-nowrap flex-shrink-0">My Competitions</TabsTrigger>
            <TabsTrigger value="active" className="text-xs sm:text-sm whitespace-nowrap flex-shrink-0">Active Now</TabsTrigger>
          </TabsList>
        </div>

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
