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
import { Gift, Calendar, Users, Target, Award, DollarSign, ArrowLeft, Zap } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CreateChallenge = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form data state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    challenge_type: '',
    challenge_category: '',
    difficulty_level: 'medium',
    target_metric: '',
    target_value: '',
    start_date: '',
    end_date: '',
    duration_hours: 0,
    max_participants: '',
    entry_requirements: {
      min_level: 1,
      min_savings: 0,
      required_badges: []
    },
    prize_type: '',
    total_prize_value: '',
    prize_structure: {
      first: 40,
      second: 30,
      third: 20,
      participation: 10
    }
  });

  const challengeTypes = [
    'daily',
    'weekly',
    'monthly',
    'sprint',
    'endurance',
    'milestone',
    'streak',
    'competition'
  ];

  const challengeCategories = [
    'savings',
    'budgeting',
    'expense_tracking',
    'goal_achievement',
    'habit_building',
    'financial_literacy',
    'investment',
    'emergency_fund'
  ];

  const difficultyLevels = [
    { value: 'easy', label: 'Easy', color: 'bg-green-100 text-green-800' },
    { value: 'medium', label: 'Medium', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'hard', label: 'Hard', color: 'bg-red-100 text-red-800' },
    { value: 'expert', label: 'Expert', color: 'bg-purple-100 text-purple-800' }
  ];

  const targetMetrics = [
    'savings_amount',
    'expense_reduction',
    'transaction_count',
    'streak_days',
    'goal_completion',
    'budget_adherence',
    'points_earned',
    'habit_consistency'
  ];

  const prizeTypes = [
    'cash',
    'voucher',
    'badge',
    'points',
    'merchandise',
    'premium_features',
    'recognition',
    'combo'
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

  const calculateDurationHours = () => {
    if (formData.start_date && formData.end_date) {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      const hours = Math.ceil((end - start) / (1000 * 60 * 60));
      handleInputChange('duration_hours', hours);
    }
  };

  const validateForm = () => {
    const required = ['title', 'description', 'challenge_type', 'challenge_category', 'target_metric', 'target_value', 'start_date', 'end_date', 'prize_type', 'total_prize_value'];
    
    for (const field of required) {
      if (!formData[field]) {
        setError(`${field.replace('_', ' ').toUpperCase()} is required`);
        return false;
      }
    }

    // Date validations
    const now = new Date();
    const start = new Date(formData.start_date);
    const end = new Date(formData.end_date);

    if (start < now) {
      setError('Start date must be in the future');
      return false;
    }

    if (end <= start) {
      setError('End date must be after start date');
      return false;
    }

    // Numeric validations
    if (parseFloat(formData.target_value) <= 0) {
      setError('Target value must be greater than 0');
      return false;
    }

    if (parseFloat(formData.total_prize_value) <= 0) {
      setError('Total prize value must be greater than 0');
      return false;
    }

    if (formData.max_participants && parseInt(formData.max_participants) <= 0) {
      setError('Maximum participants must be greater than 0');
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
        target_value: parseFloat(formData.target_value),
        total_prize_value: parseFloat(formData.total_prize_value),
        max_participants: formData.max_participants ? parseInt(formData.max_participants) : null,
        duration_hours: parseInt(formData.duration_hours),
        entry_requirements: {
          ...formData.entry_requirements,
          min_level: parseInt(formData.entry_requirements.min_level),
          min_savings: parseFloat(formData.entry_requirements.min_savings)
        }
      };

      const response = await axios.post(`${API}/prize-challenges`, submitData);
      
      setSuccess('Challenge created successfully!');
      setTimeout(() => {
        navigate('/prize-challenges');
      }, 2000);
      
    } catch (error) {
      console.error('Error creating challenge:', error);
      setError(error.response?.data?.detail || 'Failed to create challenge');
    } finally {
      setLoading(false);
    }
  };

  // Auto-calculate duration when dates change
  React.useEffect(() => {
    calculateDurationHours();
  }, [formData.start_date, formData.end_date]);

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
          <Gift className="w-6 h-6 text-green-600" />
          <h1 className="text-2xl font-bold">Create Prize Challenge</h1>
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
            <TabsTrigger value="timing">Timing</TabsTrigger>
            <TabsTrigger value="requirements">Requirements</TabsTrigger>
            <TabsTrigger value="prizes">Prizes</TabsTrigger>
          </TabsList>

          {/* Basic Information */}
          <TabsContent value="basic">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  Challenge Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="title">Challenge Title *</Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => handleInputChange('title', e.target.value)}
                    placeholder="e.g., 7-Day Savings Sprint"
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="description">Description *</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Describe the challenge objectives, rules, and what participants need to achieve..."
                    rows={4}
                    className="mt-1"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="challenge_type">Challenge Type *</Label>
                    <Select onValueChange={(value) => handleInputChange('challenge_type', value)}>
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        {challengeTypes.map((type) => (
                          <SelectItem key={type} value={type}>
                            {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="challenge_category">Challenge Category *</Label>
                    <Select onValueChange={(value) => handleInputChange('challenge_category', value)}>
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {challengeCategories.map((category) => (
                          <SelectItem key={category} value={category}>
                            {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="difficulty_level">Difficulty Level</Label>
                    <Select 
                      value={formData.difficulty_level}
                      onValueChange={(value) => handleInputChange('difficulty_level', value)}
                    >
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {difficultyLevels.map((level) => (
                          <SelectItem key={level.value} value={level.value}>
                            <div className="flex items-center gap-2">
                              <Badge className={level.color} variant="secondary">
                                {level.label}
                              </Badge>
                            </div>
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

                <div>
                  <Label htmlFor="target_value">Target Value *</Label>
                  <Input
                    id="target_value"
                    type="number"
                    value={formData.target_value}
                    onChange={(e) => handleInputChange('target_value', e.target.value)}
                    placeholder="e.g., 5000"
                    min="0"
                    step="0.01"
                    className="mt-1"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    The target amount or count participants need to achieve
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Timing */}
          <TabsContent value="timing">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Schedule & Duration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="start_date">Challenge Start *</Label>
                    <Input
                      id="start_date"
                      type="datetime-local"
                      value={formData.start_date}
                      onChange={(e) => handleInputChange('start_date', e.target.value)}
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="end_date">Challenge End *</Label>
                    <Input
                      id="end_date"
                      type="datetime-local"
                      value={formData.end_date}
                      onChange={(e) => handleInputChange('end_date', e.target.value)}
                      className="mt-1"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="duration_hours">Duration (Hours)</Label>
                  <Input
                    id="duration_hours"
                    type="number"
                    value={formData.duration_hours}
                    onChange={(e) => handleInputChange('duration_hours', e.target.value)}
                    min="1"
                    className="mt-1"
                    readOnly
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Automatically calculated from start and end dates
                  </p>
                </div>

                <div>
                  <Label htmlFor="max_participants">Maximum Participants (optional)</Label>
                  <Input
                    id="max_participants"
                    type="number"
                    value={formData.max_participants}
                    onChange={(e) => handleInputChange('max_participants', e.target.value)}
                    placeholder="Leave empty for unlimited"
                    min="1"
                    className="mt-1"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Leave empty to allow unlimited participants
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Requirements */}
          <TabsContent value="requirements">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  Entry Requirements
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="min_level">Minimum User Level</Label>
                    <Input
                      id="min_level"
                      type="number"
                      value={formData.entry_requirements.min_level}
                      onChange={(e) => handleNestedChange('entry_requirements', 'min_level', e.target.value)}
                      min="1"
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="min_savings">Minimum Savings (₹)</Label>
                    <Input
                      id="min_savings"
                      type="number"
                      value={formData.entry_requirements.min_savings}
                      onChange={(e) => handleNestedChange('entry_requirements', 'min_savings', e.target.value)}
                      min="0"
                      step="100"
                      className="mt-1"
                    />
                  </div>
                </div>

                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">Entry Requirements Summary</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Users must be at level {formData.entry_requirements.min_level} or higher</li>
                    <li>• Users must have at least ₹{formData.entry_requirements.min_savings} in savings</li>
                    <li>• Challenge difficulty: {formData.difficulty_level.toUpperCase()}</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Prizes */}
          <TabsContent value="prizes">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="w-5 h-5" />
                  Prizes & Rewards
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="prize_type">Prize Type *</Label>
                    <Select onValueChange={(value) => handleInputChange('prize_type', value)}>
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Select prize type" />
                      </SelectTrigger>
                      <SelectContent>
                        {prizeTypes.map((type) => (
                          <SelectItem key={type} value={type}>
                            {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="total_prize_value">Total Prize Value (₹) *</Label>
                    <Input
                      id="total_prize_value"
                      type="number"
                      value={formData.total_prize_value}
                      onChange={(e) => handleInputChange('total_prize_value', e.target.value)}
                      placeholder="e.g., 10000"
                      min="0"
                      step="100"
                      className="mt-1"
                    />
                  </div>
                </div>

                <div>
                  <Label>Prize Distribution (%)</Label>
                  <div className="grid grid-cols-4 gap-4 mt-1">
                    <div>
                      <Label htmlFor="first_prize" className="text-sm">1st Place</Label>
                      <Input
                        id="first_prize"
                        type="number"
                        value={formData.prize_structure.first}
                        onChange={(e) => handleNestedChange('prize_structure', 'first', parseInt(e.target.value))}
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
                        value={formData.prize_structure.second}
                        onChange={(e) => handleNestedChange('prize_structure', 'second', parseInt(e.target.value))}
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
                        value={formData.prize_structure.third}
                        onChange={(e) => handleNestedChange('prize_structure', 'third', parseInt(e.target.value))}
                        min="0"
                        max="100"
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="participation_prize" className="text-sm">Participation</Label>
                      <Input
                        id="participation_prize"
                        type="number"
                        value={formData.prize_structure.participation}
                        onChange={(e) => handleNestedChange('prize_structure', 'participation', parseInt(e.target.value))}
                        min="0"
                        max="100"
                        className="mt-1"
                      />
                    </div>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Total should equal 100%. Current: {
                      formData.prize_structure.first + 
                      formData.prize_structure.second + 
                      formData.prize_structure.third + 
                      formData.prize_structure.participation
                    }%
                  </p>
                </div>

                <div className="p-4 bg-green-50 rounded-lg">
                  <h4 className="font-medium text-green-900 mb-2">Prize Breakdown</h4>
                  <div className="text-sm text-green-800 space-y-1">
                    <div>• 1st Place: ₹{(formData.total_prize_value * formData.prize_structure.first / 100).toLocaleString()}</div>
                    <div>• 2nd Place: ₹{(formData.total_prize_value * formData.prize_structure.second / 100).toLocaleString()}</div>
                    <div>• 3rd Place: ₹{(formData.total_prize_value * formData.prize_structure.third / 100).toLocaleString()}</div>
                    <div>• Participation: ₹{(formData.total_prize_value * formData.prize_structure.participation / 100).toLocaleString()}</div>
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
            className="bg-green-600 hover:bg-green-700"
          >
            {loading ? 'Creating...' : 'Create Challenge'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default CreateChallenge;
