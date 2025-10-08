import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alret';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Trophy, Calendar, Users, Target, Award, DollarSign, ArrowLeft, Plus, X } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CreateCompetition = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form data state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    competition_type: '',
    start_date: '',
    end_date: '',
    registration_start: '',
    registration_end: '',
    min_participants_per_campus: 10,
    max_participants_per_campus: 100,
    eligible_universities: [],
    min_user_level: 1,
    scoring_method: 'total',
    target_metric: '',
    target_value: '',
    prize_pool: '',
    prize_distribution: {
      first: 50,
      second: 30,
      third: 20
    },
    campus_reputation_points: {
      first: 100,
      second: 75,
      third: 50
    },
    participation_rewards: {
      points: 10,
      badge: 'Participant'
    }
  });

  const [newUniversity, setNewUniversity] = useState('');

  const competitionTypes = [
    'savings_challenge',
    'expense_reduction',
    'budgeting_mastery',
    'financial_literacy',
    'investment_simulation',
    'emergency_fund_building',
    'goal_achievement',
    'habit_tracking'
  ];

  const targetMetrics = [
    'total_savings',
    'expense_reduction',
    'budget_adherence',
    'goal_completion',
    'transaction_count',
    'streak_days',
    'points_earned',
    'badges_collected'
  ];

  const scoringMethods = [
    { value: 'total', label: 'Total Amount/Count' },
    { value: 'average', label: 'Average per Participant' },
    { value: 'percentage', label: 'Percentage Achievement' },
    { value: 'points', label: 'Points-based' }
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    setError('');
  };

  const handleNestedChange = (parent, field, value) => {
    setFormData(prev => ({
      ...prev,
      [parent]: {
        ...prev[parent],
        [field]: value
      }
    }));
  };

  const addUniversity = () => {
    if (newUniversity.trim() && !formData.eligible_universities.includes(newUniversity.trim())) {
      setFormData(prev => ({
        ...prev,
        eligible_universities: [...prev.eligible_universities, newUniversity.trim()]
      }));
      setNewUniversity('');
    }
  };

  const removeUniversity = (university) => {
    setFormData(prev => ({
      ...prev,
      eligible_universities: prev.eligible_universities.filter(u => u !== university)
    }));
  };

  const validateForm = () => {
    const required = ['title', 'description', 'competition_type', 'start_date', 'end_date', 'registration_start', 'registration_end', 'target_metric', 'prize_pool'];
    
    for (const field of required) {
      if (!formData[field]) {
        setError(`${field.replace('_', ' ').toUpperCase()} is required`);
        return false;
      }
    }

    // Date validations
    const now = new Date();
    const regStart = new Date(formData.registration_start);
    const regEnd = new Date(formData.registration_end);
    const compStart = new Date(formData.start_date);
    const compEnd = new Date(formData.end_date);

    if (regStart < now) {
      setError('Registration start date must be in the future');
      return false;
    }

    if (regEnd <= regStart) {
      setError('Registration end date must be after start date');
      return false;
    }

    if (compStart <= regEnd) {
      setError('Competition start date must be after registration end date');
      return false;
    }

    if (compEnd <= compStart) {
      setError('Competition end date must be after start date');
      return false;
    }

    // Numeric validations
    if (formData.min_participants_per_campus >= formData.max_participants_per_campus) {
      setError('Maximum participants must be greater than minimum participants');
      return false;
    }

    if (parseFloat(formData.prize_pool) <= 0) {
      setError('Prize pool must be greater than 0');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      setError('');

      const submitData = {
        ...formData,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString(),
        registration_start: new Date(formData.registration_start).toISOString(),
        registration_end: new Date(formData.registration_end).toISOString(),
        prize_pool: parseFloat(formData.prize_pool),
        target_value: formData.target_value ? parseFloat(formData.target_value) : null,
        min_participants_per_campus: parseInt(formData.min_participants_per_campus),
        max_participants_per_campus: parseInt(formData.max_participants_per_campus),
        min_user_level: parseInt(formData.min_user_level)
      };

      const response = await axios.post(`${API}/inter-college/competitions`, submitData);
      
      setSuccess('Competition created successfully!');
      setTimeout(() => {
        navigate('/inter-college-competitions');
      }, 2000);
      
    } catch (error) {
      console.error('Error creating competition:', error);
      setError(error.response?.data?.detail || 'Failed to create competition');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button
          variant="outline"
          onClick={() => navigate(-1)}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>
        <div className="flex items-center gap-2">
          <Trophy className="w-6 h-6 text-blue-600" />
          <h1 className="text-2xl font-bold">Create Inter-College Competition</h1>
        </div>
      </div>

      {error && (
        <Alert className="mb-6 border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="mb-6 border-green-200 bg-green-50">
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Tabs defaultValue="basic" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="basic">Basic Info</TabsTrigger>
            <TabsTrigger value="dates">Dates & Timing</TabsTrigger>
            <TabsTrigger value="participants">Participants</TabsTrigger>
            <TabsTrigger value="rewards">Rewards & Prizes</TabsTrigger>
          </TabsList>

          {/* Basic Information */}
          <TabsContent value="basic">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="w-5 h-5" />
                  Competition Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="title">Competition Title *</Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => handleInputChange('title', e.target.value)}
                    placeholder="e.g., Winter Savings Championship"
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="description">Description *</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Describe the competition objectives, rules, and what participants need to do..."
                    rows={4}
                    className="mt-1"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="competition_type">Competition Type *</Label>
                    <Select onValueChange={(value) => handleInputChange('competition_type', value)}>
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        {competitionTypes.map((type) => (
                          <SelectItem key={type} value={type}>
                            {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="target_metric">Target Metric *</Label>
                    <Select onValueChange={(value) => handleInputChange('target_metric', value)}>
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Select metric" />
                      </SelectTrigger>
                      <SelectContent>
                        {targetMetrics.map((metric) => (
                          <SelectItem key={metric} value={metric}>
                            {metric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="target_value">Target Value (optional)</Label>
                    <Input
                      id="target_value"
                      type="number"
                      value={formData.target_value}
                      onChange={(e) => handleInputChange('target_value', e.target.value)}
                      placeholder="e.g., 10000"
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="scoring_method">Scoring Method</Label>
                    <Select 
                      value={formData.scoring_method}
                      onValueChange={(value) => handleInputChange('scoring_method', value)}
                    >
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {scoringMethods.map((method) => (
                          <SelectItem key={method.value} value={method.value}>
                            {method.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Dates & Timing */}
          <TabsContent value="dates">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Schedule & Timing
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="registration_start">Registration Start *</Label>
                    <Input
                      id="registration_start"
                      type="datetime-local"
                      value={formData.registration_start}
                      onChange={(e) => handleInputChange('registration_start', e.target.value)}
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="registration_end">Registration End *</Label>
                    <Input
                      id="registration_end"
                      type="datetime-local"
                      value={formData.registration_end}
                      onChange={(e) => handleInputChange('registration_end', e.target.value)}
                      className="mt-1"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="start_date">Competition Start *</Label>
                    <Input
                      id="start_date"
                      type="datetime-local"
                      value={formData.start_date}
                      onChange={(e) => handleInputChange('start_date', e.target.value)}
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="end_date">Competition End *</Label>
                    <Input
                      id="end_date"
                      type="datetime-local"
                      value={formData.end_date}
                      onChange={(e) => handleInputChange('end_date', e.target.value)}
                      className="mt-1"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Participants */}
          <TabsContent value="participants">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Participant Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="min_participants">Min Participants per Campus</Label>
                    <Input
                      id="min_participants"
                      type="number"
                      value={formData.min_participants_per_campus}
                      onChange={(e) => handleInputChange('min_participants_per_campus', e.target.value)}
                      min="1"
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="max_participants">Max Participants per Campus</Label>
                    <Input
                      id="max_participants"
                      type="number"
                      value={formData.max_participants_per_campus}
                      onChange={(e) => handleInputChange('max_participants_per_campus', e.target.value)}
                      min="1"
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="min_user_level">Min User Level</Label>
                    <Input
                      id="min_user_level"
                      type="number"
                      value={formData.min_user_level}
                      onChange={(e) => handleInputChange('min_user_level', e.target.value)}
                      min="1"
                      className="mt-1"
                    />
                  </div>
                </div>

                <div>
                  <Label>Eligible Universities (optional)</Label>
                  <div className="flex gap-2 mt-1">
                    <Input
                      value={newUniversity}
                      onChange={(e) => setNewUniversity(e.target.value)}
                      placeholder="Enter university name"
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addUniversity())}
                    />
                    <Button type="button" onClick={addUniversity} variant="outline">
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                  
                  {formData.eligible_universities.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {formData.eligible_universities.map((university) => (
                        <Badge key={university} variant="secondary" className="flex items-center gap-1">
                          {university}
                          <button
                            type="button"
                            onClick={() => removeUniversity(university)}
                            className="ml-1 hover:text-red-500"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                  <p className="text-sm text-gray-500 mt-1">
                    Leave empty to allow all universities
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Rewards & Prizes */}
          <TabsContent value="rewards">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="w-5 h-5" />
                  Rewards & Prizes
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="prize_pool">Total Prize Pool (₹) *</Label>
                  <Input
                    id="prize_pool"
                    type="number"
                    value={formData.prize_pool}
                    onChange={(e) => handleInputChange('prize_pool', e.target.value)}
                    placeholder="e.g., 50000"
                    min="0"
                    step="100"
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label>Prize Distribution (%)</Label>
                  <div className="grid grid-cols-3 gap-4 mt-1">
                    <div>
                      <Label htmlFor="first_prize" className="text-sm">1st Place</Label>
                      <Input
                        id="first_prize"
                        type="number"
                        value={formData.prize_distribution.first}
                        onChange={(e) => handleNestedChange('prize_distribution', 'first', parseInt(e.target.value))}
                        min="0"
                        max="100"
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="second_prize" className="text-sm">2nd Place</Label>
                      <Input
                        id="second_prize"
                        type="number"
                        value={formData.prize_distribution.second}
                        onChange={(e) => handleNestedChange('prize_distribution', 'second', parseInt(e.target.value))}
                        min="0"
                        max="100"
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="third_prize" className="text-sm">3rd Place</Label>
                      <Input
                        id="third_prize"
                        type="number"
                        value={formData.prize_distribution.third}
                        onChange={(e) => handleNestedChange('prize_distribution', 'third', parseInt(e.target.value))}
                        min="0"
                        max="100"
                        className="mt-1"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <Label>Campus Reputation Points</Label>
                  <div className="grid grid-cols-3 gap-4 mt-1">
                    <div>
                      <Label htmlFor="first_points" className="text-sm">1st Place</Label>
                      <Input
                        id="first_points"
                        type="number"
                        value={formData.campus_reputation_points.first}
                        onChange={(e) => handleNestedChange('campus_reputation_points', 'first', parseInt(e.target.value))}
                        min="0"
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="second_points" className="text-sm">2nd Place</Label>
                      <Input
                        id="second_points"
                        type="number"
                        value={formData.campus_reputation_points.second}
                        onChange={(e) => handleNestedChange('campus_reputation_points', 'second', parseInt(e.target.value))}
                        min="0"
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="third_points" className="text-sm">3rd Place</Label>
                      <Input
                        id="third_points"
                        type="number"
                        value={formData.campus_reputation_points.third}
                        onChange={(e) => handleNestedChange('campus_reputation_points', 'third', parseInt(e.target.value))}
                        min="0"
                        className="mt-1"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <Label>Participation Rewards</Label>
                  <div className="grid grid-cols-2 gap-4 mt-1">
                    <div>
                      <Label htmlFor="participation_points" className="text-sm">Points</Label>
                      <Input
                        id="participation_points"
                        type="number"
                        value={formData.participation_rewards.points}
                        onChange={(e) => handleNestedChange('participation_rewards', 'points', parseInt(e.target.value))}
                        min="0"
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="participation_badge" className="text-sm">Badge Name</Label>
                      <Input
                        id="participation_badge"
                        value={formData.participation_rewards.badge}
                        onChange={(e) => handleNestedChange('participation_rewards', 'badge', e.target.value)}
                        className="mt-1"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Submit Button */}
        <div className="flex justify-end gap-4 mt-8">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate(-1)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {loading ? 'Creating...' : 'Create Competition'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default CreateCompetition;
