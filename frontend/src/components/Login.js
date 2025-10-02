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
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="form-container fade-in">
            <div className="text-center mb-8">
              <div className="flex items-center justify-center mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                  <KeyIcon className="w-6 h-6 text-white" />
                </div>
              </div>
              <h1 className="text-4xl font-bold gradient-text mb-2">Reset Password</h1>
              <p className="text-gray-600">Enter your email and new password</p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center">
                <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
                {error}
              </div>
            )}

            {successMessage && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6 flex items-center">
                <CheckCircleIcon className="w-5 h-5 mr-2" />
                {successMessage}
              </div>
            )}

            <form onSubmit={handleResetPassword} className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={resetData.email}
                  onChange={(e) => setResetData({...resetData, email: e.target.value})}
                  className="input-modern"
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
                  className="input-modern"
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
                  className="input-modern"
                  placeholder="Confirm new password"
                  required
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowResetPassword(false)}
                  className="btn-secondary flex-1"
                >
                  Back to Login
                </button>
                <button
                  type="submit"
                  disabled={resetLoading}
                  className="btn-primary flex-1"
                >
                  {resetLoading ? <div className="spinner"></div> : 'Reset Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="form-container fade-in">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-xl">₹</span>
              </div>
            </div>
            <h1 className="text-4xl font-bold gradient-text mb-2">EarnAura</h1>
            <p className="text-gray-600">Welcome back! Ready to grow your earnings?</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center">
              <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
              {error}
            </div>
          )}

          {successMessage && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6 flex items-center">
              <CheckCircleIcon className="w-5 h-5 mr-2" />
              {successMessage}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Email Address
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
                  className="input-modern pr-12"
                  placeholder="Enter your password"
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
                className="text-sm text-emerald-600 font-semibold hover:text-emerald-700"
              >
                Reset password?
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center"
            >
              {loading ? (
                <div className="spinner"></div>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="text-center mt-6">
            <p className="text-gray-600">
              Don't have an account?{' '}
              <Link to="/register" className="text-emerald-600 font-semibold hover:text-emerald-700">
                Sign up here
              </Link>
            </p>
          </div>

          {/* Security Notice */}
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center">
              <ShieldCheckIcon className="w-5 h-5 text-blue-600 mr-2" />
              <div>
                <p className="text-sm font-semibold text-blue-800">Secure Login</p>
                <p className="text-sm text-blue-700">
                  Your login is protected with advanced security measures.
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
