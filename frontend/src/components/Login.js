import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../App';
import { 
  EyeIcon, 
  EyeSlashIcon, 
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  KeyIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showResetPassword, setShowResetPassword] = useState(false);
  const [resetData, setResetData] = useState({
    email: '',
    new_password: '',
    confirm_password: ''
  });
  const [resetLoading, setResetLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  
  const { login } = useAuth();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/auth/login`, formData);
      login(response.data.user, response.data.token);
      navigate('/dashboard');
    } catch (error) {
      if (error.response?.status === 423) {
        setError('Account temporarily locked due to multiple failed login attempts. Please try again later or reset your password.');
      } else if (error.response?.status === 401) {
        setError('Invalid email or password. Please check your credentials and try again.');
      } else {
        setError('Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    if (resetData.new_password !== resetData.confirm_password) {
      setError('Passwords do not match');
      return;
    }

    if (resetData.new_password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setResetLoading(true);
    setError('');

    try {
      await axios.post(`${API}/auth/reset-password`, {
        email: resetData.email,
        new_password: resetData.new_password
      });
      setSuccessMessage('Password reset successfully! You can now log in with your new password.');
      setShowResetPassword(false);
      setResetData({
        email: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (error) {
      setError(error.response?.data?.detail || 'Password reset failed. Please try again.');
    } finally {
      setResetLoading(false);
    }
  };

  if (showResetPassword) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-emerald-50 via-blue-50 to-indigo-50">
        <div className="max-w-md w-full">
          <div className="bg-white/80 backdrop-blur-sm border border-white/20 shadow-xl rounded-2xl p-8 fade-in">
            <div className="text-center mb-8">
              <div className="flex items-center justify-center mb-6">
                <div className="relative">
                  <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 via-green-500 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg">
                    <KeyIcon className="w-8 h-8 text-white" />
                  </div>
                  <div className="absolute -inset-1 bg-gradient-to-br from-emerald-400 to-green-400 rounded-2xl opacity-20 blur"></div>
                </div>
              </div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-600 via-green-600 to-emerald-700 bg-clip-text text-transparent mb-2">Reset Password</h1>
              <p className="text-gray-600">Secure your EarnAura account</p>
              
              {/* Progress indicator */}
              <div className="mt-6 flex items-center justify-center space-x-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                <div className="w-8 h-1 bg-emerald-500 rounded"></div>
                <div className="w-2 h-2 bg-emerald-200 rounded-full"></div>
              </div>
            </div>

            {error && (
              <div className="bg-red-50/80 backdrop-blur-sm border border-red-200/60 text-red-700 px-4 py-3 rounded-xl mb-6 flex items-center animate-shake">
                <ExclamationTriangleIcon className="w-5 h-5 mr-2 flex-shrink-0" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            {successMessage && (
              <div className="bg-emerald-50/80 backdrop-blur-sm border border-emerald-200/60 text-emerald-700 px-4 py-3 rounded-xl mb-6 flex items-center">
                <CheckCircleIcon className="w-5 h-5 mr-2 flex-shrink-0" />
                <span className="text-sm">{successMessage}</span>
              </div>
            )}

            <form onSubmit={handleResetPassword} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={resetData.email}
                  onChange={(e) => setResetData({...resetData, email: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
                  placeholder="Enter your email"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  New Password
                </label>
                <input
                  type="password"
                  value={resetData.new_password}
                  onChange={(e) => setResetData({...resetData, new_password: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
                  placeholder="Enter new password"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={resetData.confirm_password}
                  onChange={(e) => setResetData({...resetData, confirm_password: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
                  placeholder="Confirm new password"
                  required
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowResetPassword(false)}
                  className="flex-1 px-6 py-3 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-all font-medium"
                >
                  Back to Login
                </button>
                <button
                  type="submit"
                  disabled={resetLoading}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-white rounded-xl hover:from-emerald-600 hover:to-green-600 transition-all font-medium disabled:opacity-50 flex items-center justify-center"
                >
                  {resetLoading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  ) : (
                    'Reset Password'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-emerald-50 via-blue-50 to-indigo-50">
      {/* Hero Background Illustration */}
      <div className="absolute inset-0 overflow-hidden">
        <div 
          className="absolute top-0 right-0 w-1/3 h-1/2 opacity-10 bg-cover bg-center"
          style={{
            backgroundImage: "url('https://images.unsplash.com/photo-1660020619062-70b16c44bf0f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwyfHxmaW5hbmNlJTIwYXBwfGVufDB8fHxibHVlfDE3NTk0ODgwOTJ8MA&ixlib=rb-4.1.0&q=85')"
          }}
        />
        <div 
          className="absolute bottom-0 left-0 w-1/4 h-1/3 opacity-10 bg-cover bg-center"
          style={{
            backgroundImage: "url('https://images.unsplash.com/photo-1551721434-8b94ddff0e6d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwzfHxmaW5hbmNlJTIwYXBwfGVufDB8fHxibHVlfDE3NTk0ODgwOTJ8MA&ixlib=rb-4.1.0&q=85')"
          }}
        />
      </div>

      <div className="max-w-md w-full relative z-10">
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
            <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-600 via-green-600 to-emerald-700 bg-clip-text text-transparent mb-2">EarnAura</h1>
            <p className="text-gray-600">Welcome back to your financial journey</p>
            
            {/* Progress indicator */}
            <div className="mt-6 flex items-center justify-center space-x-2">
              <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
              <div className="w-8 h-1 bg-emerald-200 rounded"></div>
              <div className="w-2 h-2 bg-emerald-200 rounded-full"></div>
            </div>
          </div>

          {error && (
            <div className="bg-red-50/80 backdrop-blur-sm border border-red-200/60 text-red-700 px-4 py-3 rounded-xl mb-6 flex items-center animate-shake">
              <ExclamationTriangleIcon className="w-5 h-5 mr-2 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {successMessage && (
            <div className="bg-emerald-50/80 backdrop-blur-sm border border-emerald-200/60 text-emerald-700 px-4 py-3 rounded-xl mb-6 flex items-center">
              <CheckCircleIcon className="w-5 h-5 mr-2 flex-shrink-0" />
              <span className="text-sm">{successMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Email Address
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
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full px-4 py-3 pr-12 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all bg-white/50"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 transition-colors"
                >
                  {showPassword ? (
                    <EyeSlashIcon className="w-5 h-5" />
                  ) : (
                    <EyeIcon className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                  Remember me
                </label>
              </div>

              <button
                type="button"
                onClick={() => setShowResetPassword(true)}
                className="text-sm text-emerald-600 font-semibold hover:text-emerald-700 transition-colors"
              >
                Forgot password?
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-white rounded-xl hover:from-emerald-600 hover:to-green-600 transition-all font-medium disabled:opacity-50 flex items-center justify-center"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                'Sign In to EarnAura'
              )}
            </button>
          </form>

          <div className="text-center mt-6">
            <p className="text-gray-600">
              New to EarnAura?{' '}
              <Link to="/register" className="text-emerald-600 font-semibold hover:text-emerald-700 transition-colors">
                Create your account
              </Link>
            </p>
          </div>

          {/* Enhanced Security Notice */}
          <div className="mt-6 p-4 bg-gradient-to-r from-blue-50/80 to-emerald-50/80 backdrop-blur-sm border border-blue-200/60 rounded-xl">
            <div className="flex items-center">
              <ShieldCheckIcon className="w-5 h-5 text-blue-600 mr-3 flex-shrink-0" />
              <div>
                <p className="text-sm font-semibold text-blue-800">Bank-Grade Security</p>
                <p className="text-sm text-blue-700">
                  Your financial data is protected with 256-bit encryption
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
