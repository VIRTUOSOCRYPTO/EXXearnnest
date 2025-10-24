import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';
import { 
  EyeIcon, 
  EyeSlashIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  UserIcon,
  MapPinIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Register = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 3;
  
  // Extract referral code from URL params
  const [referralCode, setReferralCode] = useState('');
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    phone_number: '',
    role: '',
    location: '',
    student_level: 'undergraduate',
    university: '',
    skills: [],
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

  // Extract referral code from URL parameters
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const refCode = searchParams.get('ref');
    if (refCode) {
      setReferralCode(refCode);
      console.log('Referral code detected:', refCode);
    }
  }, [location.search]);

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
    
    if (error) setError('');
  };

  const validateStep = (step) => {
    switch (step) {
      case 1:
        if (!formData.full_name.trim() || formData.full_name.trim().length < 2) {
          setError('Full name must be at least 2 characters long');
          return false;
        }
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
          setError('Please enter a valid email address');
          return false;
        }
        if (!formData.phone_number || !formData.phone_number.trim()) {
          setError('Phone number is required');
          return false;
        }
        const phone = formData.phone_number.replace(/[^0-9+]/g, '');
        if (!/^\+?\d{10,15}$/.test(phone)) {
          setError('Phone number must be 10-15 digits');
          return false;
        }
        if (formData.password !== formData.confirmPassword) {
          setError('Passwords do not match');
          return false;
        }
        if (passwordStrength.score < 40) {
          setError('Password is too weak. Please choose a stronger password.');
          return false;
        }
        break;
      case 2:
        if (!formData.role || !formData.role.trim()) {
          setError('Role selection is required');
          return false;
        }
        if (!formData.location || !formData.location.trim()) {
          setError('Location is required');
          return false;
        }
        if (formData.location.trim().length < 3) {
          setError('Location must be at least 3 characters long');
          return false;
        }
        const location = formData.location.trim();
        if (!location.includes(',') && location.split(' ').length < 2) {
          setError('Location should include city and state/country');
          return false;
        }
        break;
      case 3:
        if (!formData.skills || formData.skills.length === 0) {
          setError('At least one skill must be selected');
          return false;
        }
        break;
    }
    return true;
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(currentStep + 1);
      setError('');
    }
  };

  const prevStep = () => {
    setCurrentStep(currentStep - 1);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateStep(3)) return;

    setLoading(true);
    setError('');

    try {
      const submitData = {
        ...formData,
        skills: formData.skills,
        availability_hours: parseInt(formData.availability_hours)
      };
      delete submitData.confirmPassword;

      // Build URL with referral code if present
      let registrationUrl = `${API}/auth/register`;
      if (referralCode) {
        registrationUrl += `?ref=${encodeURIComponent(referralCode)}`;
      }
      
      const response = await axios.post(registrationUrl, submitData);
      
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

  const getStepIcon = (step) => {
    switch (step) {
      case 1: return <UserIcon className="w-5 h-5" />;
      case 2: return <MapPinIcon className="w-5 h-5" />;
      case 3: return <AcademicCapIcon className="w-5 h-5" />;
      default: return <UserIcon className="w-5 h-5" />;
    }
  };

  const getStepTitle = (step) => {
    switch (step) {
      case 1: return 'Account Details';
      case 2: return 'Profile Information';
      case 3: return 'Skills & Preferences';
      default: return 'Account Details';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8 bg-gradient-to-br from-emerald-50 via-blue-50 to-indigo-50">
      {/* Hero Background Illustrations */}
      <div className="absolute inset-0 overflow-hidden">
        <div 
          className="absolute top-0 right-0 w-1/3 h-1/2 opacity-10 bg-cover bg-center"
          style={{
            backgroundImage: "url('https://images.pexels.com/photos/9169180/pexels-photo-9169180.jpeg')"
          }}
        />
        <div 
          className="absolute bottom-0 left-0 w-1/4 h-1/3 opacity-10 bg-cover bg-center"
          style={{
            backgroundImage: "url('https://images.unsplash.com/photo-1655548201132-824b96322d69?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHw0fHxmaW5hbmNlJTIwYXBwfGVufDB8fHxibHVlfDE3NTk0ODgwOTJ8MA&ixlib=rb-4.1.0&q=85')"
          }}
        />
      </div>

      <div className="max-w-2xl w-full relative z-10">
        <div className="bg-white/80 backdrop-blur-sm border border-white/20 shadow-xl rounded-2xl p-8 fade-in">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-6">
              <div className="relative">
                <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 via-green-500 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <span className="text-white font-bold text-2xl">₹</span>
                </div>
                <div className="absolute -inset-1 bg-gradient-to-br from-emerald-400 to-green-400 rounded-2xl opacity-20 blur"></div>
              </div>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-600 via-green-600 to-emerald-700 bg-clip-text text-transparent mb-2">Join EarnAura</h1>
            <p className="text-gray-600">Start your financial success journey today</p>
            
            {/* Enhanced Progress Indicator */}
            <div className="mt-8 mb-6">
              <div className="flex items-center justify-center space-x-4">
                {[1, 2, 3].map((step) => (
                  <div key={step} className="flex items-center">
                    <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all ${
                      currentStep >= step 
                        ? 'bg-emerald-500 border-emerald-500 text-white' 
                        : 'border-gray-300 text-gray-400'
                    }`}>
                      {currentStep > step ? (
                        <CheckCircleIcon className="w-5 h-5" />
                      ) : (
                        getStepIcon(step)
                      )}
                    </div>
                    {step < 3 && (
                      <div className={`w-16 h-1 mx-2 rounded ${
                        currentStep > step ? 'bg-emerald-500' : 'bg-gray-200'
                      }`} />
                    )}
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <p className="text-sm font-medium text-emerald-600">
                  Step {currentStep} of {totalSteps}: {getStepTitle(currentStep)}
                </p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div 
                    className="bg-gradient-to-r from-emerald-500 to-green-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(currentStep / totalSteps) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {error && (
            <div className="bg-red-50/80 backdrop-blur-sm border border-red-200/60 text-red-700 px-4 py-3 rounded-xl mb-6 flex items-center animate-shake">
              <ExclamationTriangleIcon className="w-5 h-5 mr-2 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {referralCode && (
            <div className="bg-emerald-50/80 backdrop-blur-sm border border-emerald-200/60 text-emerald-700 px-4 py-3 rounded-xl mb-6 flex items-center">
              <CheckCircleIcon className="w-5 h-5 mr-2 flex-shrink-0" />
              <div>
                <span className="text-sm font-medium">🎉 Referral Code Applied!</span>
                <p className="text-xs mt-1">You'll automatically become friends with your referrer and both get bonus points!</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Step 1: Account Details */}
            {currentStep === 1 && (
              <div className="space-y-5 animate-fadeIn">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
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
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
                    placeholder="Enter your email"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Phone Number *
                  </label>
                  <input
                    type="tel"
                    name="phone_number"
                    value={formData.phone_number}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
                    placeholder="Enter your phone number (10-15 digits)"
                    required
                  />
                </div>

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
                      className="w-full px-4 py-3 pr-12 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
                      placeholder="Create a strong password"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 transition-colors"
                    >
                      {showPassword ? <EyeSlashIcon className="w-5 h-5" /> : <EyeIcon className="w-5 h-5" />}
                    </button>
                  </div>
                  
                  {/* Enhanced Password Strength Meter */}
                  {formData.password && (
                    <div className="mt-3 p-3 bg-gray-50/50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Password Strength</span>
                        <span className={`text-sm font-semibold ${
                          passwordStrength.color === 'green' ? 'text-green-600' : 
                          passwordStrength.color === 'blue' ? 'text-blue-600' :
                          passwordStrength.color === 'yellow' ? 'text-yellow-600' :
                          passwordStrength.color === 'orange' ? 'text-orange-600' : 'text-red-600'
                        }`}>
                          {passwordStrength.strength}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-500 ${
                            passwordStrength.color === 'green' ? 'bg-green-500' :
                            passwordStrength.color === 'blue' ? 'bg-blue-500' :
                            passwordStrength.color === 'yellow' ? 'bg-yellow-500' :
                            passwordStrength.color === 'orange' ? 'bg-orange-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${passwordStrength.score}%` }}
                        />
                      </div>
                      {passwordStrength.feedback.length > 0 && (
                        <div className="text-xs text-gray-600">
                          <p className="mb-1 font-medium">Suggestions:</p>
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
                      className={`w-full px-4 py-3 pr-20 border rounded-xl focus:ring-2 focus:ring-emerald-500/20 transition-all bg-white/50 ${
                        formData.confirmPassword && !passwordsMatch 
                          ? 'border-red-300 focus:border-red-500' 
                          : formData.confirmPassword && passwordsMatch 
                          ? 'border-green-300 focus:border-green-500' 
                          : 'border-gray-200 focus:border-emerald-500'
                      }`}
                      placeholder="Confirm your password"
                      required
                    />
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-2">
                      {formData.confirmPassword && (
                        <div>
                          {passwordsMatch ? (
                            <CheckCircleIcon className="w-5 h-5 text-green-500" />
                          ) : (
                            <XCircleIcon className="w-5 h-5 text-red-500" />
                          )}
                        </div>
                      )}
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="text-gray-500 hover:text-gray-700 transition-colors"
                      >
                        {showConfirmPassword ? <EyeSlashIcon className="w-5 h-5" /> : <EyeIcon className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>
                  {formData.confirmPassword && !passwordsMatch && (
                    <p className="text-sm text-red-600 mt-1 flex items-center">
                      <XCircleIcon className="w-4 h-4 mr-1" />
                      Passwords do not match
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Step 2: Profile Information */}
            {currentStep === 2 && (
              <div className="space-y-5 animate-fadeIn">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Role *
                    </label>
                    <select
                      name="role"
                      value={formData.role}
                      onChange={handleChange}
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
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
                      Student Level
                    </label>
                    <select
                      name="student_level"
                      value={formData.student_level}
                      onChange={handleChange}
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
                    >
                      <option value="high_school">High School</option>
                      <option value="undergraduate">Undergraduate</option>
                      <option value="graduate">Graduate</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Location *
                  </label>
                  <input
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
                    placeholder="e.g., Mumbai, Maharashtra"
                    required
                  />
                  <p className="text-sm text-gray-500 mt-1 flex items-center">
                    <MapPinIcon className="w-4 h-4 mr-1" />
                    Please include city and state/country
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    University/College (Optional)
                  </label>
                  
                  <div className="space-y-3">
                    <select
                      name="university"
                      value={formData.university}
                      onChange={handleChange}
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
                    >
                      <option value="">Select your institution (optional)</option>
                      
                      {suggestedUniversities.length > 0 && (
                        <optgroup label="🎯 Recommended for you">
                          {suggestedUniversities.slice(0, 5).map((uni) => (
                            <option key={uni.id} value={uni.name}>
                              {uni.name} {uni.distance_match ? '📍' : uni.level_match ? '🎓' : ''}
                            </option>
                          ))}
                        </optgroup>
                      )}
                      
                      <option value="other">Other (not listed)</option>
                    </select>
                    
                    {loadingUniversities && (
                      <div className="flex items-center text-sm text-emerald-600">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-emerald-600 mr-2"></div>
                        Finding universities near you...
                      </div>
                    )}
                  </div>
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
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
                    min="1"
                    max="40"
                    placeholder="10"
                  />
                </div>
              </div>
            )}

            {/* Step 3: Skills & Preferences */}
            {currentStep === 3 && (
              <div className="space-y-6 animate-fadeIn">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-4">
                    Skills Selection *
                    <span className="text-red-500 ml-1">
                      (Select at least one skill)
                    </span>
                  </label>
                  
                  {/* Enhanced Trending Skills Grid */}
                  <div className="mb-5">
                    <h4 className="text-sm font-medium text-gray-600 mb-3 flex items-center">
                      <span className="mr-2">🔥</span>
                      Trending Skills
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {trendingSkills.map((skill) => (
                        <button
                          key={skill.name}
                          type="button"
                          onClick={() => toggleSkill(skill.name)}
                          className={`p-3 rounded-xl border-2 text-sm font-medium transition-all ${
                            formData.skills.includes(skill.name)
                              ? 'border-emerald-500 bg-emerald-50 text-emerald-700 shadow-md'
                              : 'border-gray-200 bg-white text-gray-700 hover:border-emerald-300 hover:bg-emerald-50 hover:shadow-sm'
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

                  {/* Enhanced Custom Skills Input */}
                  <div className="mb-5 p-4 bg-gray-50/50 rounded-xl">
                    <h4 className="text-sm font-medium text-gray-600 mb-3 flex items-center">
                      <span className="mr-2">➕</span>
                      Add Custom Skill
                    </h4>
                    <div className="flex gap-3">
                      <input
                        type="text"
                        value={customSkill}
                        onChange={(e) => setCustomSkill(e.target.value)}
                        className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/70"
                        placeholder="Enter a custom skill"
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomSkill())}
                      />
                      <button
                        type="button"
                        onClick={addCustomSkill}
                        className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-white rounded-xl hover:from-emerald-600 hover:to-green-600 transition-all font-medium"
                      >
                        Add
                      </button>
                    </div>
                  </div>

                  {/* Enhanced Selected Skills Display */}
                  {formData.skills.length > 0 && (
                    <div className="p-4 bg-emerald-50/50 rounded-xl">
                      <h4 className="text-sm font-medium text-emerald-700 mb-3 flex items-center">
                        <CheckCircleIcon className="w-4 h-4 mr-2" />
                        Selected Skills ({formData.skills.length})
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {formData.skills.map((skill) => (
                          <span
                            key={skill}
                            className="inline-flex items-center px-3 py-2 rounded-full text-sm bg-emerald-100 text-emerald-800 border border-emerald-200"
                          >
                            {skill}
                            <button
                              type="button"
                              onClick={() => removeSkill(skill)}
                              className="ml-2 text-emerald-600 hover:text-emerald-800 hover:bg-emerald-200 rounded-full p-0.5 transition-colors"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Bio (Optional)
                  </label>
                  <textarea
                    name="bio"
                    value={formData.bio}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
                    rows="3"
                    maxLength="500"
                    placeholder="Tell us about yourself and your goals..."
                  />
                  <div className="text-right text-sm text-gray-500 mt-1">
                    {formData.bio.length}/500
                  </div>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-6">
              {currentStep > 1 && (
                <button
                  type="button"
                  onClick={prevStep}
                  className="px-6 py-3 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-all font-medium"
                >
                  Previous
                </button>
              )}
              
              {currentStep < totalSteps ? (
                <button
                  type="button"
                  onClick={nextStep}
                  className={`px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-white rounded-xl hover:from-emerald-600 hover:to-green-600 transition-all font-medium ${
                    currentStep === 1 ? 'ml-auto' : ''
                  }`}
                >
                  Next Step
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading || formData.skills.length === 0}
                  className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-white rounded-xl hover:from-emerald-600 hover:to-green-600 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
                      Creating Account...
                    </>
                  ) : (
                    'Create Account & Sign In'
                  )}
                </button>
              )}
            </div>
          </form>

          <div className="text-center mt-6">
            <p className="text-gray-600">
              Already have an EarnAura account?{' '}
              <Link to="/login" className="text-emerald-600 font-semibold hover:text-emerald-700 transition-colors">
                Sign in here
              </Link>
            </p>
          </div>

          {/* Enhanced Security Notice */}
          <div className="mt-6 p-4 bg-gradient-to-r from-blue-50/80 to-emerald-50/80 backdrop-blur-sm border border-blue-200/60 rounded-xl">
            <div className="flex items-center">
              <ShieldCheckIcon className="w-5 h-5 text-blue-600 mr-3 flex-shrink-0" />
              <div>
                <p className="text-sm font-semibold text-blue-800">Secure & Instant Registration</p>
                <p className="text-sm text-blue-700">
                  Your data is protected with bank-grade security. Start earning immediately after registration!
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
