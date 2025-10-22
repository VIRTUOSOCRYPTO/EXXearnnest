import React, { useState, useEffect, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import pushNotificationService from './services/pushNotificationService';
import { Toaster } from 'sonner';

// Always load these critical components (Login, Register, Dashboard, Navigation, Footer)
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import Register from './components/Register';
import Navigation from './components/Navigation';
import Footer from './components/Footer';

// ============================================================================
// LAZY LOADED COMPONENTS - Code Splitting for Better Performance
// ============================================================================

// Core Features - Lazy Loaded
const Transaction = lazy(() => import('./components/Transaction'));
const Hustles = lazy(() => import('./components/Hustles'));
const Analytics = lazy(() => import('./components/Analytics'));
const Profile = lazy(() => import('./components/Profile'));
const Budget = lazy(() => import('./components/Budget'));
const FinancialGoals = lazy(() => import('./components/FinancialGoals'));
const Recommendations = lazy(() => import('./components/Recommendations'));
const Notifications = lazy(() => import('./components/Notifications'));
const NotificationCenter = lazy(() => import('./components/NotificationCenter'));

// Gamification Features - Lazy Loaded
const GamificationProfile = lazy(() => import('./components/GamificationProfile'));
const FriendsAndReferrals = lazy(() => import('./components/FriendsAndReferrals'));
const AllChallenges = lazy(() => import('./components/AllChallenges'));
const SocialFeed = lazy(() => import('./components/SocialFeed'));
const DailyCheckin = lazy(() => import('./components/DailyCheckin'));

// Enhanced Features - Lazy Loaded
const LimitedOffers = lazy(() => import('./components/LimitedOffers'));
const SharingHub = lazy(() => import('./components/SharingHub'));
const FeatureUnlock = lazy(() => import('./components/FeatureUnlock'));
const FinancialJourney = lazy(() => import('./components/FinancialJourney'));
const DailyTips = lazy(() => import('./components/DailyTips'));
const Timeline = lazy(() => import('./components/Timeline'));
const TipsHistory = lazy(() => import('./components/TipsHistory'));
const OffersHistory = lazy(() => import('./components/OffersHistory'));
const EnhancedPhotoSharing = lazy(() => import('./components/EnhancedPhotoSharing'));
const HabitTracking = lazy(() => import('./components/HabitTracking'));
const WeeklyRecap = lazy(() => import('./components/WeeklyRecap'));
const PersonalizedGoals = lazy(() => import('./components/PersonalizedGoals'));

// Campus Features - Lazy Loaded
const CampusAmbassador = lazy(() => import('./components/CampusAmbassador'));
const GrowthMechanics = lazy(() => import('./components/GrowthMechanics'));
const ExpenseReceipts = lazy(() => import('./components/ExpenseReceipts'));
const GroupExpenses = lazy(() => import('./components/GroupExpenses'));
const InterCollegeCompetitions = lazy(() => import('./components/InterCollegeCompetitions'));
const PrizeChallenges = lazy(() => import('./components/PrizeChallenges'));
const CreateCompetition = lazy(() => import('./components/CreateCompetition'));
const CreateChallenge = lazy(() => import('./components/CreateChallenge'));
const CampusReputation = lazy(() => import('./components/CampusReputation'));

// Admin System - Lazy Loaded
const CampusAdminRequest = lazy(() => import('./components/CampusAdminRequest'));
const CampusAdminDashboard = lazy(() => import('./components/CampusAdminDashboard'));
const ClubAdminDashboard = lazy(() => import('./components/ClubAdminDashboard'));
const SuperAdminInterface = lazy(() => import('./components/SuperAdminInterface'));
const MyRegistrations = lazy(() => import('./components/MyRegistrations'));

// College Events System - Lazy Loaded
const CreateEvent = lazy(() => import('./components/CreateEvent'));
const EditEvent = lazy(() => import('./components/EditEvent'));
const EventsList = lazy(() => import('./components/EventsList'));
const EventDetails = lazy(() => import('./components/EventDetails'));
const MyEvents = lazy(() => import('./components/MyEvents'));

// Viral Impact Features - Lazy Loaded
const PublicCampusBattle = lazy(() => import('./components/PublicCampusBattle'));
const SpendingInsights = lazy(() => import('./components/SpendingInsights'));
const ViralMilestones = lazy(() => import('./components/ViralMilestones'));
const FriendComparisons = lazy(() => import('./components/FriendComparisons'));
const ImpactStats = lazy(() => import('./components/ImpactStats'));

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-500 mx-auto mb-4"></div>
      <p className="text-gray-600 font-medium">Loading...</p>
    </div>
  </div>
);

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
          <Toaster position="top-right" richColors closeButton />
          {user && <Navigation />}
          <main className="flex-grow">
            <Suspense fallback={<LoadingFallback />}>
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
                path="/my-registrations" 
                element={user ? <MyRegistrations /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/notification-center" 
                element={user ? <NotificationCenter /> : <Navigate to="/login" />} 
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
                path="/create-competition" 
                element={user ? <CreateCompetition /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/create-challenge" 
                element={user ? <CreateChallenge /> : <Navigate to="/login" />} 
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
              <Route 
                path="/campus-admin" 
                element={user ? <Navigate to="/campus-admin/dashboard" /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/club-admin/dashboard" 
                element={user ? <ClubAdminDashboard /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/club-admin" 
                element={user ? <Navigate to="/club-admin/dashboard" /> : <Navigate to="/login" />} 
              />
              {/* SystemAdminInterface removed - functionality merged into SuperAdminInterface */}
              <Route 
                path="/super-admin" 
                element={user ? <SuperAdminInterface /> : <Navigate to="/login" />} 
              />
              
              {/* College Events System */}
              <Route 
                path="/events" 
                element={user ? <EventsList /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/events/create" 
                element={user ? <CreateEvent /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/create-college-event" 
                element={user ? <CreateEvent /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/events/:id" 
                element={user ? <EventDetails /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/events/:id/edit" 
                element={user ? <EditEvent /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/my-events" 
                element={user ? <MyEvents /> : <Navigate to="/login" />} 
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
            </Suspense>
          </main>
          {user && <Footer />}
        </div>
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

export default App;
