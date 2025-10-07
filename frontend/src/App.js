import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import pushNotificationService from './services/pushNotificationService';

// Components
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import Register from './components/Register';
import Transaction from './components/Transaction';
import Hustles from './components/Hustles';
import Analytics from './components/Analytics';
import Profile from './components/Profile';
import Budget from './components/Budget';
import FinancialGoals from './components/FinancialGoals';
import Recommendations from './components/Recommendations';
import GamificationProfile from './components/GamificationProfile';
import FriendsAndReferrals from './components/FriendsAndReferrals';
import AllChallenges from './components/AllChallenges';
import Notifications from './components/Notifications';
import Navigation from './components/Navigation';
import Footer from './components/Footer';
import SocialFeed from './components/SocialFeed';
import DailyCheckin from './components/DailyCheckin';
import LimitedOffers from './components/LimitedOffers';
import SharingHub from './components/SharingHub';
import FeatureUnlock from './components/FeatureUnlock';
import FinancialJourney from './components/FinancialJourney';
import DailyTips from './components/DailyTips';
import Timeline from './components/Timeline';
import TipsHistory from './components/TipsHistory';
import OffersHistory from './components/OffersHistory';
import EnhancedPhotoSharing from './components/EnhancedPhotoSharing';
import HabitTracking from './components/HabitTracking';
import WeeklyRecap from './components/WeeklyRecap';
import PersonalizedGoals from './components/PersonalizedGoals';
import CampusAmbassador from './components/CampusAmbassador';
import GrowthMechanics from './components/GrowthMechanics';
import ExpenseReceipts from './components/ExpenseReceipts';
import GroupExpenses from './components/GroupExpenses';
import InterCollegeCompetitions from './components/InterCollegeCompetitions';
import PrizeChallenges from './components/PrizeChallenges';
import CampusReputation from './components/CampusReputation';

// Admin Verification System
import CampusAdminRequest from './components/CampusAdminRequest';
// Removed SystemAdminInterface - merged into SuperAdminInterface
import CampusAdminDashboard from './components/CampusAdminDashboard';
import SuperAdminInterface from './components/SuperAdminInterface';

// Viral Impact Features
import PublicCampusBattle from './components/PublicCampusBattle';
import SpendingInsights from './components/SpendingInsights';
import ViralMilestones from './components/ViralMilestones';
import FriendComparisons from './components/FriendComparisons';
import ImpactStats from './components/ImpactStats';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Currency formatter for Indian Rupees
export const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount);
};

// Main App Component
function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Set up axios defaults
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Check if user is logged in on app start
  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          const response = await axios.get(`${API}/user/profile`);
          setUser(response.data);
          
          // Initialize push notifications for authenticated users
          try {
            await pushNotificationService.initialize();
            pushNotificationService.setupNotificationHandlers();
          } catch (error) {
            console.error('Push notification initialization failed:', error);
          }
          
        } catch (error) {
          console.error('Auth check failed:', error);
          logout();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, [token]);

  const login = (userData, authToken) => {
    setUser(userData);
    setToken(authToken);
    localStorage.setItem('token', authToken);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
  };

  const authValue = {
    user,
    token,
    login,
    logout,
    updateUser,
    isAuthenticated: !!user
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold gradient-text">EarnAura</h2>
          <p className="text-gray-600">Loading your financial dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={authValue}>
      <BrowserRouter>
        <div className="App min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50 flex flex-col">
          {user && <Navigation />}
          <main className="flex-grow">
            <Routes>
              <Route 
                path="/login" 
                element={!user ? <Login /> : <Navigate to="/dashboard" />} 
              />
              <Route 
                path="/register" 
                element={!user ? <Register /> : <Navigate to="/dashboard" />} 
              />
              <Route 
                path="/dashboard" 
                element={user ? <Dashboard /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/transactions" 
                element={user ? <Transaction /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/budget" 
                element={user ? <Budget /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/goals" 
                element={user ? <FinancialGoals /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/hustles" 
                element={user ? <Hustles /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/analytics" 
                element={user ? <Analytics /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/recommendations" 
                element={user ? <Recommendations /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/profile" 
                element={user ? <Profile /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/gamification" 
                element={user ? <GamificationProfile /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/friends-referrals" 
                element={user ? <FriendsAndReferrals /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/challenges" 
                element={user ? <AllChallenges /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/notifications" 
                element={user ? <Notifications /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/social-feed" 
                element={user ? <SocialFeed /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/daily-checkin" 
                element={user ? <DailyCheckin /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/limited-offers" 
                element={user ? <LimitedOffers /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/sharing-hub" 
                element={user ? <SharingHub /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/feature-unlock" 
                element={user ? <FeatureUnlock /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/financial-journey" 
                element={user ? <FinancialJourney /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/daily-tips" 
                element={user ? <DailyTips userId={user?.id} /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/timeline" 
                element={user ? <Timeline userId={user?.id} /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/photo-sharing" 
                element={user ? <EnhancedPhotoSharing userId={user?.id} /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/habit-tracking" 
                element={user ? <HabitTracking /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/weekly-recap" 
                element={user ? <WeeklyRecap /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/personalized-goals" 
                element={user ? <PersonalizedGoals /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/campus-ambassador" 
                element={user ? <CampusAmbassador /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/growth-mechanics" 
                element={user ? <GrowthMechanics /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/expense-receipts" 
                element={user ? <ExpenseReceipts /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/group-expenses" 
                element={user ? <GroupExpenses /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/inter-college-competitions" 
                element={user ? <InterCollegeCompetitions /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/prize-challenges" 
                element={user ? <PrizeChallenges /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/campus-reputation" 
                element={user ? <CampusReputation /> : <Navigate to="/login" />} 
              />

              {/* Admin Verification System Routes */}
              <Route 
                path="/campus-admin/request" 
                element={user ? <CampusAdminRequest /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/campus-admin/dashboard" 
                element={user ? <CampusAdminDashboard /> : <Navigate to="/login" />} 
              />
              {/* SystemAdminInterface removed - functionality merged into SuperAdminInterface */}
              <Route 
                path="/super-admin" 
                element={user ? <SuperAdminInterface /> : <Navigate to="/login" />} 
              />
              
              {/* Viral Impact Features */}
              <Route 
                path="/public/campus-battle" 
                element={<PublicCampusBattle />} 
              />
              <Route 
                path="/spending-insights" 
                element={user ? <SpendingInsights userCampus={user?.university} /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/viral-milestones" 
                element={<ViralMilestones />} 
              />
              <Route 
                path="/friend-comparisons" 
                element={user ? <FriendComparisons /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/public/impact-stats" 
                element={<ImpactStats />} 
              />
              <Route 
                path="/tips-history" 
                element={user ? <TipsHistory /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/offers-history" 
                element={user ? <OffersHistory /> : <Navigate to="/login" />} 
              />
              
              <Route 
                path="/" 
                element={<Navigate to={user ? "/dashboard" : "/login"} />} 
              />
            </Routes>
          </main>
          {user && <Footer />}
        </div>
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

export default App;
