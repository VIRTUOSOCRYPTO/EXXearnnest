import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';
import { 
  EyeIcon, 
  EyeSlashIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  ShieldCheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    role: '', // MANDATORY - will be required
    location: '', // MANDATORY - will be required
    student_level: 'undergraduate',
    university: '', // For campus integration
    skills: [],  // Changed to array for better handling
    availability_hours: 10,
    bio: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({
    score: 0,
    strength: 'Very Weak',
    color: 'red',
    feedback: []
  });
  const [passwordsMatch, setPasswordsMatch] = useState(true);
  const [trendingSkills, setTrendingSkills] = useState([]);
  const [universities, setUniversities] = useState([]);
  const [suggestedUniversities, setSuggestedUniversities] = useState([]);
  const [loadingUniversities, setLoadingUniversities] = useState(false);
  const [customSkill, setCustomSkill] = useState('');
  
  const { login } = useAuth();

  // Fetch trending skills and universities on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const skillsResponse = await axios.get(`${API}/auth/trending-skills`);
        setTrendingSkills(skillsResponse.data.trending_skills || skillsResponse.data);
      } catch (error) {
        console.error('Error fetching skills:', error);
        // Set default skills if API fails
        setTrendingSkills([
          { name: 'Freelancing', category: 'Business' },
          { name: 'Graphic Design', category: 'Creative' },
          { name: 'Coding', category: 'Technical' },
          { name: 'Digital Marketing', category: 'Marketing' },
          { name: 'Content Writing', category: 'Creative' },
          { name: 'Video Editing', category: 'Creative' },
          { name: 'AI Tools & Automation', category: 'Technical' },
          { name: 'Social Media Management', category: 'Marketing' }
        ]);
      }
    };
    
    fetchData();
  }, []);

  // Smart university suggestions based on location and student level
  useEffect(() => {
    const fetchUniversitySuggestions = async () => {
      if (!formData.location.trim() || formData.location.length < 3 || !formData.student_level) {
        setSuggestedUniversities([]);
        return;
      }

      setLoadingUniversities(true);
      try {
        const response = await axios.get(`${API}/gamification/universities/suggestions`, {
          params: {
            location: formData.location,
            student_level: formData.student_level,
            limit: 8
          }
        });
        
        setSuggestedUniversities(response.data.suggestions || []);
      } catch (error) {
        console.error('Error fetching university suggestions:', error);
        setSuggestedUniversities([]);
      } finally {
        setLoadingUniversities(false);
      }
    };

    // Debounce the API call
    const timeoutId = setTimeout(fetchUniversitySuggestions, 1000);
    return () => clearTimeout(timeoutId);
  }, [formData.location, formData.student_level]);

  // Skills management functions
  const toggleSkill = (skillName) => {
    setFormData(prev => ({
      ...prev,
      skills: prev.skills.includes(skillName) 
        ? prev.skills.filter(skill => skill !== skillName)
        : [...prev.skills, skillName]
    }));
  };

  const addCustomSkill = () => {
    if (customSkill.trim() && !formData.skills.includes(customSkill.trim())) {
      setFormData(prev => ({
        ...prev,
        skills: [...prev.skills, customSkill.trim()]
      }));
      setCustomSkill('');
    }
  };

  const removeSkill = (skillToRemove) => {
    setFormData(prev => ({
      ...prev,
      skills: prev.skills.filter(skill => skill !== skillToRemove)
    }));
  };

  // Password strength checking
  useEffect(() => {
    if (formData.password) {
      checkPasswordStrength(formData.password);
    }
  }, [formData.password]);

  // Password match checking
  useEffect(() => {
    if (formData.confirmPassword) {
      setPasswordsMatch(formData.password === formData.confirmPassword);
    }
  }, [formData.password, formData.confirmPassword]);

  const checkPasswordStrength = async (password) => {
    try {
      const response = await axios.post(`${API}/auth/password-strength`, { password });
      setPasswordStrength(response.data);
    } catch (error) {
      // Fallback to basic client-side checking
      const score = getPasswordScore(password);
      setPasswordStrength({
        score,
        strength: getStrengthText(score),
        color: getStrengthColor(score),
        feedback: getPasswordFeedback(password)
      });
    }
  };

  const getPasswordScore = (password) => {
    let score = 0;
    if (password.length >= 8) score += 25;
    if (password.length >= 12) score += 25;
    if (/[A-Z]/.test(password)) score += 15;
    if (/[a-z]/.test(password)) score += 15;
    if (/\d/.test(password)) score += 10;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 10;
    return Math.min(100, score);
  };

  const getStrengthText = (score) => {
    if (score >= 80) return 'Very Strong';
    if (score >= 60) return 'Strong';
    if (score >= 40) return 'Medium';
    if (score >= 20) return 'Weak';
    return 'Very Weak';
  };

  const getStrengthColor = (score) => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'blue';
    if (score >= 40) return 'yellow';
    if (score >= 20) return 'orange';
    return 'red';
  };

  const getPasswordFeedback = (password) => {
    const feedback = [];
    if (password.length < 8) feedback.push('Use at least 8 characters');
    if (!/[A-Z]/.test(password)) feedback.push('Add uppercase letters');
    if (!/[a-z]/.test(password)) feedback.push('Add lowercase letters');
    if (!/\d/.test(password)) feedback.push('Add numbers');
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) feedback.push('Add special characters');
    return feedback;
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    
    // Clear error when user starts typing
    if (error) setError('');
  };

  const validateForm = () => {
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }

    if (passwordStrength.score < 40) {
      setError('Password is too weak. Please choose a stronger password.');
      return false;
    }

    if (formData.full_name.trim().length < 2) {
      setError('Full name must be at least 2 characters long');
      return false;
    }

    // Mandatory role validation
    if (!formData.role || !formData.role.trim()) {
      setError('Role selection is required');
      return false;
    }

    // Mandatory location validation  
    if (!formData.location || !formData.location.trim()) {
      setError('Location is required and cannot be empty');
      return false;
    }

    if (formData.location.trim().length < 3) {
      setError('Location must be at least 3 characters long');
      return false;
    }

    // Basic location format validation
    const location = formData.location.trim();
    if (!location.includes(',') && location.split(' ').length < 2) {
      setError('Location should include city and state/country (e.g., "Mumbai, Maharashtra" or "New York, USA")');
      return false;
    }

    // Mandatory skills validation
    if (!formData.skills || formData.skills.length === 0) {
      setError('At least one skill must be selected');
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setLoading(true);
    setError('');

    try {
      const submitData = {
        ...formData,
        skills: formData.skills, // Skills is already an array
        availability_hours: parseInt(formData.availability_hours)
      };
      delete submitData.confirmPassword;

      const response = await axios.post(`${API}/auth/register`, submitData);
      
      // Direct login after registration - no email verification needed
      login(response.data.user, response.data.token);
      navigate('/dashboard');
    } catch (error) {
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          setError(error.response.data.detail[0].msg || 'Registration failed');
        } else {
          setError(error.response.data.detail);
        }
      } else {
        setError('Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const getColorClasses = (color) => {
    const colorMap = {
      red: 'bg-red-500 text-red-700 border-red-300',
      orange: 'bg-orange-500 text-orange-700 border-orange-300',
      yellow: 'bg-yellow-500 text-yellow-700 border-yellow-300',
      blue: 'bg-blue-500 text-blue-700 border-blue-300',
      green: 'bg-green-500 text-green-700 border-green-300'
    };
    return colorMap[color] || colorMap.red;
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="max-w-2xl w-full">
        <div className="form-container fade-in">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-xl">₹</span>
              </div>
            </div>
            <h1 className="text-4xl font-bold gradient-text mb-2">Join EarnAura</h1>
            <p className="text-gray-600">Start your journey to financial success</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center">
              <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Full Name *
                </label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  className="input-modern"
                  placeholder="Enter your full name"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Email Address *
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="input-modern"
                  placeholder="Enter your email"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Password *
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    className="input-modern pr-12"
                    placeholder="Create a strong password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="w-5 h-5" />
                    ) : (
                      <EyeIcon className="w-5 h-5" />
                    )}
                  </button>
                </div>
                
                {/* Password Strength Meter */}
                {formData.password && (
                  <div className="mt-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">Password Strength</span>
                      <span className={`text-sm font-semibold ${passwordStrength.color === 'green' ? 'text-green-600' : 
                        passwordStrength.color === 'blue' ? 'text-blue-600' :
                        passwordStrength.color === 'yellow' ? 'text-yellow-600' :
                        passwordStrength.color === 'orange' ? 'text-orange-600' : 'text-red-600'}`}>
                        {passwordStrength.strength} ({passwordStrength.score}/100)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-300 ${
                          passwordStrength.color === 'green' ? 'bg-green-500' :
                          passwordStrength.color === 'blue' ? 'bg-blue-500' :
                          passwordStrength.color === 'yellow' ? 'bg-yellow-500' :
                          passwordStrength.color === 'orange' ? 'bg-orange-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${passwordStrength.score}%` }}
                      ></div>
                    </div>
                    {passwordStrength.feedback.length > 0 && (
                      <div className="text-sm text-gray-600">
                        <p className="mb-1">Suggestions:</p>
                        <ul className="list-disc list-inside space-y-1">
                          {passwordStrength.feedback.map((feedback, index) => (
                            <li key={index}>{feedback}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Confirm Password *
                </label>
                <div className="relative">
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className={`input-modern pr-12 ${
                      formData.confirmPassword && !passwordsMatch 
                        ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
                        : formData.confirmPassword && passwordsMatch 
                        ? 'border-green-300 focus:border-green-500 focus:ring-green-500' 
                        : ''
                    }`}
                    placeholder="Confirm your password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showConfirmPassword ? (
                      <EyeSlashIcon className="w-5 h-5" />
                    ) : (
                      <EyeIcon className="w-5 h-5" />
                    )}
                  </button>
                  {formData.confirmPassword && (
                    <div className="absolute right-10 top-1/2 transform -translate-y-1/2">
                      {passwordsMatch ? (
                        <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      ) : (
                        <XCircleIcon className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                  )}
                </div>
                {formData.confirmPassword && !passwordsMatch && (
                  <p className="text-sm text-red-600 mt-1">Passwords do not match</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Role *
                </label>
                <select
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  className="input-modern"
                  required
                >
                  <option value="">Select your role</option>
                  <option value="Student">Student</option>
                  <option value="Professional">Professional</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Student Level *
                </label>
                <select
                  name="student_level"
                  value={formData.student_level}
                  onChange={handleChange}
                  className="input-modern"
                  required
                >
                  <option value="high_school">High School</option>
                  <option value="undergraduate">Undergraduate</option>
                  <option value="graduate">Graduate</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Location *
                </label>
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleChange}
                  className="input-modern"
                  placeholder="e.g., Mumbai, Maharashtra"
                  required
                />
                <p className="text-sm text-gray-500 mt-1">
                  Please include city and state/country
                </p>
              </div>

              <div>
                {/* Empty space for grid alignment */}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  University/College
                </label>
                
                {/* Smart University Suggestions */}
                <div className="space-y-3">
                  <select
                    name="university"
                    value={formData.university}
                    onChange={handleChange}
                    className="input-modern"
                  >
                    <option value="">Select your institution (optional)</option>
                    
                    {/* Smart Suggestions Section */}
                    {suggestedUniversities.length > 0 && (
                      <optgroup label="🎯 Recommended for you">
                        {suggestedUniversities.slice(0, 5).map((uni) => (
                          <option key={uni.id} value={uni.name}>
                            {uni.name} {uni.distance_match ? '📍' : uni.level_match ? '🎓' : ''}
                          </option>
                        ))}
                      </optgroup>
                    )}
                    
                    {/* More Options */}
                    {suggestedUniversities.length > 5 && (
                      <optgroup label="🏫 More Options">
                        {suggestedUniversities.slice(5).map((uni) => (
                          <option key={uni.id} value={uni.name}>
                            {uni.name} - {uni.city}
                          </option>
                        ))}
                      </optgroup>
                    )}
                    
                    <option value="other">Other (not listed)</option>
                  </select>
                  
                  {/* Loading indicator */}
                  {loadingUniversities && (
                    <div className="flex items-center text-sm text-emerald-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-emerald-600 mr-2"></div>
                      Finding universities near you...
                    </div>
                  )}
                  
                  {/* Smart suggestions info */}
                  {suggestedUniversities.length > 0 && !loadingUniversities && (
                    <div className="text-sm text-gray-600 bg-emerald-50 border border-emerald-200 rounded-lg p-3">
                      <div className="flex items-center mb-2">
                        <span className="text-emerald-600 font-semibold">🎯 Smart Suggestions</span>
                      </div>
                      <div className="text-xs space-y-1">
                        <div className="flex items-center">
                          <span className="mr-2">📍</span>
                          <span>Near your location ({formData.location})</span>
                        </div>
                        <div className="flex items-center">
                          <span className="mr-2">🎓</span>
                          <span>Matches your level ({formData.student_level})</span>
                        </div>
                        <p className="text-emerald-700 font-medium mt-2">
                          Found {suggestedUniversities.length} institutions for you!
                        </p>
                      </div>
                    </div>
                  )}
                  
                  {/* No suggestions message */}
                  {suggestedUniversities.length === 0 && !loadingUniversities && formData.location.length >= 3 && (
                    <div className="text-sm text-gray-500 bg-gray-50 border border-gray-200 rounded-lg p-3">
                      <p>💡 Enter your location and student level to see personalized university suggestions!</p>
                    </div>
                  )}
                </div>
                
                <p className="text-sm text-gray-500 mt-2">
                  Join campus competitions and connect with your peers
                </p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Available Hours/Week
                </label>
                <input
                  type="number"
                  name="availability_hours"
                  value={formData.availability_hours}
                  onChange={handleChange}
                  className="input-modern"
                  min="1"
                  max="40"
                  placeholder="10"
                />
              </div>
            </div>

            {/* Location field moved above - removed duplicate */}

            {/* Skills Selection Section */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-4">
                Skills Selection *
                <span className="text-red-500 ml-1">
                  (Select at least one skill)
                </span>
              </label>
              
              {/* Trending Skills Grid */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-600 mb-3">Trending Skills</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {trendingSkills.map((skill) => (
                    <button
                      key={skill.name}
                      type="button"
                      onClick={() => toggleSkill(skill.name)}
                      className={`p-3 rounded-lg border-2 text-sm font-medium transition-all ${
                        formData.skills.includes(skill.name)
                          ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                          : 'border-gray-200 bg-white text-gray-700 hover:border-emerald-300 hover:bg-emerald-50'
                      }`}
                    >
                      <div className="text-center">
                        <div className="font-semibold">{skill.name}</div>
                        <div className="text-xs text-gray-500 mt-1">{skill.category}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Skills Input */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-600 mb-2">Add Custom Skill</h4>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={customSkill}
                    onChange={(e) => setCustomSkill(e.target.value)}
                    className="input-modern flex-1"
                    placeholder="Enter a custom skill"
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomSkill())}
                  />
                  <button
                    type="button"
                    onClick={addCustomSkill}
                    className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                  >
                    Add
                  </button>
                </div>
              </div>

              {/* Selected Skills Display */}
              {formData.skills.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-2">Selected Skills ({formData.skills.length})</h4>
                  <div className="flex flex-wrap gap-2">
                    {formData.skills.map((skill) => (
                      <span
                        key={skill}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-emerald-100 text-emerald-800"
                      >
                        {skill}
                        <button
                          type="button"
                          onClick={() => removeSkill(skill)}
                          className="ml-2 text-emerald-600 hover:text-emerald-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Skills Validation Error */}
              {formData.skills.length === 0 && (
                <p className="text-red-500 text-sm mt-2">
                  ⚠️ Please select at least one skill to continue
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Bio
              </label>
              <textarea
                name="bio"
                value={formData.bio}
                onChange={handleChange}
                className="input-modern"
                rows="3"
                maxLength="500"
                placeholder="Tell us about yourself (optional)"
              />
              <div className="text-right text-sm text-gray-500 mt-1">
                {formData.bio.length}/500
              </div>
            </div>

            <button
              type="submit"
              disabled={
                loading || 
                !passwordsMatch || 
                passwordStrength.score < 40 || 
                !formData.role || 
                !formData.location.trim() ||
                formData.skills.length === 0  // Add skills validation
              }
              className="btn-primary w-full flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="spinner"></div>
              ) : (
                'Create Account & Sign In'
              )}
            </button>
          </form>

          <div className="text-center mt-6">
            <p className="text-gray-600">
              Already have an account?{' '}
              <Link to="/login" className="text-emerald-600 font-semibold hover:text-emerald-700">
                Sign in here
              </Link>
            </p>
          </div>

          {/* Security Notice */}
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center">
              <ShieldCheckIcon className="w-5 h-5 text-blue-600 mr-2" />
              <div>
                <p className="text-sm font-semibold text-blue-800">Secure Registration</p>
                <p className="text-sm text-blue-700">
                  Your data is protected with advanced security measures. Start earning immediately after registration!
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
