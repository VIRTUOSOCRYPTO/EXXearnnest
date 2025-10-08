import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { 
  HomeIcon, 
  CreditCardIcon,
  BanknotesIcon,
  BriefcaseIcon, 
  ChartBarIcon, 
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
  StarIcon,
  LightBulbIcon,
  TrophyIcon,
  GiftIcon,
  FireIcon,
  Bars3Icon,
  XMarkIcon,
  UsersIcon,
  BellIcon,
  UserGroupIcon,
  AcademicCapIcon,
  RocketLaunchIcon,
  DocumentIcon,
  BuildingOffice2Icon,
  SparklesIcon,
  CalendarDaysIcon
} from '@heroicons/react/24/outline';
import { formatCurrency } from '../App';
import RealTimeNotifications from './RealTimeNotifications';

const Navigation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isCampusOpen, setIsCampusOpen] = useState(false);
  const [isViralOpen, setIsViralOpen] = useState(false);
  const [isAdminOpen, setIsAdminOpen] = useState(false);
  const navRef = useRef(null);

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: HomeIcon },
    { path: '/transactions', label: 'Transactions', icon: CreditCardIcon },
    { path: '/budget', label: 'Budget', icon: BanknotesIcon },
    { path: '/goals', label: 'Goals', icon: StarIcon },
    { path: '/analytics', label: 'Analytics', icon: ChartBarIcon },
    { path: '/hustles', label: 'Side Hustles', icon: BriefcaseIcon },
    { path: '/friends-referrals', label: 'Friends & Referrals', icon: UsersIcon },
    { path: '/gamification', label: 'Achievements', icon: TrophyIcon },
    { path: '/recommendations', label: 'Recommendations', icon: LightBulbIcon },
    { path: '/challenges', label: 'Challenges', icon: FireIcon },
    { path: '/social-feed', label: 'Social Feed', icon: UserGroupIcon },
    { path: '/sharing-hub', label: 'Sharing Hub', icon: GiftIcon },
    { path: '/daily-checkin', label: 'Daily Check-in', icon: StarIcon },
    { path: '/habit-tracking', label: 'Habit Tracking', icon: FireIcon },
    { path: '/weekly-recap', label: 'Weekly Recap', icon: ChartBarIcon },
    { path: '/personalized-goals', label: 'Personalized Goals', icon: TrophyIcon },
    { path: '/limited-offers', label: 'Limited Offers', icon: GiftIcon },
    { path: '/feature-unlock', label: 'Feature Unlock', icon: LightBulbIcon },
    { path: '/financial-journey', label: 'Financial Journey', icon: ChartBarIcon },
    { path: '/daily-tips', label: 'Daily Tips', icon: LightBulbIcon },
    { path: '/timeline', label: 'Timeline', icon: FireIcon },
    { path: '/photo-sharing', label: 'Photo Sharing', icon: UserCircleIcon },
    { path: '/notifications', label: 'Notifications', icon: BellIcon },
    { path: '/campus-ambassador', label: 'Campus Ambassador', icon: AcademicCapIcon },
    { path: '/growth-mechanics', label: 'Growth & Beta', icon: RocketLaunchIcon },
    { path: '/expense-receipts', label: 'Expense Receipts', icon: DocumentIcon },
    { path: '/group-expenses', label: 'Group Expenses', icon: UsersIcon },
  ];

  const campusItems = [
    { path: '/inter-college-competitions', label: 'Inter-College Competitions', icon: TrophyIcon },
    { path: '/prize-challenges', label: 'Prize Challenges', icon: SparklesIcon },
    { path: '/events', label: 'College Events', icon: CalendarDaysIcon },
    { path: '/campus-reputation', label: 'Campus Reputation', icon: TrophyIcon },
  ];

  // Admin navigation items (conditionally shown based on admin_level)
  const adminItems = [
    { path: '/campus-admin/request', label: 'Request Campus Admin Access', icon: BuildingOffice2Icon, showForNonAdmins: true },
    { path: '/campus-admin/dashboard', label: 'Campus Admin Dashboard', icon: ChartBarIcon, requiredLevel: 'campus_admin' },
    { path: '/club-admin/dashboard', label: 'Club Admin Dashboard', icon: ChartBarIcon, requiredLevel: 'club_admin' },
    { path: '/super-admin', label: 'Super Admin Dashboard', icon: UserCircleIcon, requiredLevel: 'super_admin' },
    { path: '/my-events', label: 'My Events', icon: CalendarDaysIcon, requiredLevel: 'any_admin' },
  ];

  const viralItems = [
    { path: '/public/campus-battle', label: 'Campus Battle Arena', icon: TrophyIcon, public: true },
    { path: '/spending-insights', label: 'Spending Insights', icon: ChartBarIcon },
    { path: '/viral-milestones', label: 'Viral Milestones', icon: FireIcon, public: true },
    { path: '/friend-comparisons', label: 'Friend Comparisons', icon: UsersIcon },
    { path: '/public/impact-stats', label: 'Impact Stories', icon: DocumentIcon, public: true },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  const closeAllDropdowns = () => {
    setIsProfileOpen(false);
    setIsCampusOpen(false);
    setIsViralOpen(false);
    setIsAdminOpen(false);
  };

  const toggleProfileDropdown = () => {
    setIsProfileOpen(!isProfileOpen);
    setIsCampusOpen(false);
    setIsViralOpen(false);
    setIsAdminOpen(false);
  };

  const toggleCampusDropdown = () => {
    setIsCampusOpen(!isCampusOpen);
    setIsProfileOpen(false);
    setIsViralOpen(false);
    setIsAdminOpen(false);
  };

  const toggleViralDropdown = () => {
    setIsViralOpen(!isViralOpen);
    setIsProfileOpen(false);
    setIsCampusOpen(false);
    setIsAdminOpen(false);
  };

  const toggleAdminDropdown = () => {
    setIsAdminOpen(!isAdminOpen);
    setIsProfileOpen(false);
    setIsCampusOpen(false);
    setIsViralOpen(false);
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (navRef.current && !navRef.current.contains(event.target)) {
        setIsMobileMenuOpen(false);
        closeAllDropdowns();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Close mobile menu and dropdowns on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
    closeAllDropdowns();
  }, [location.pathname]);

  return (
    <nav ref={navRef} className="bg-white shadow-sm border-b border-gray-100 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-shrink-0">
            <div className="w-7 h-7 sm:w-8 sm:h-8 bg-gradient-to-br from-emerald-500 to-green-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">₹</span>
            </div>
            <h1 className="text-lg sm:text-2xl font-bold gradient-text truncate">EarnAura</h1>
          </div>

          {/* Navigation Links - Desktop */}
          <div className="hidden lg:flex items-center space-x-1">
            {/* Core Navigation Items */}
            {navItems.slice(0, 8).map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'text-gray-600 hover:text-emerald-600 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
            
            {/* Campus Dropdown */}
            <div className="relative">
              {(() => {
                const hasCampusActive = campusItems.some(item => location.pathname === item.path);
                return (
                  <button 
                    onClick={toggleCampusDropdown}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      hasCampusActive || isCampusOpen
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'text-gray-600 hover:text-emerald-600 hover:bg-gray-50'
                    }`}>
                    <BuildingOffice2Icon className="w-4 h-4" />
                    Campus
                    {hasCampusActive && <div className="w-2 h-2 bg-emerald-600 rounded-full ml-1" />}
                    <svg className={`w-4 h-4 transition-transform duration-200 ${isCampusOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                );
              })()}
              
              {/* Campus Dropdown Menu */}
              <div className={`absolute top-full left-0 mt-1 w-64 bg-white shadow-lg rounded-lg border border-gray-200 transition-all duration-200 z-50 ${
                isCampusOpen ? 'opacity-100 visible' : 'opacity-0 invisible'
              }`}>
                <div className="p-2 space-y-1">
                  {campusItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;
                    
                    return (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={closeAllDropdowns}
                        className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                          isActive
                            ? 'bg-purple-100 text-purple-700'
                            : 'text-gray-600 hover:text-purple-600 hover:bg-purple-50'
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                        {item.label}
                      </Link>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Viral Features Dropdown */}
            <div className="relative">
              {(() => {
                const hasViralActive = viralItems.some(item => location.pathname === item.path);
                return (
                  <button 
                    onClick={toggleViralDropdown}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      hasViralActive || isViralOpen
                        ? 'bg-orange-100 text-orange-700'
                        : 'text-gray-600 hover:text-orange-600 hover:bg-gray-50'
                    }`}>
                    <FireIcon className="w-4 h-4" />
                    🔥 Viral
                    {hasViralActive && <div className="w-2 h-2 bg-orange-600 rounded-full ml-1" />}
                    <svg className={`w-4 h-4 transition-transform duration-200 ${isViralOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                );
              })()}
              
              {/* Viral Features Dropdown Menu */}
              <div className={`absolute top-full left-0 mt-1 w-64 bg-white shadow-lg rounded-lg border border-gray-200 transition-all duration-200 z-50 ${
                isViralOpen ? 'opacity-100 visible' : 'opacity-0 invisible'
              }`}>
                <div className="p-2 space-y-1">
                  {viralItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;
                    
                    return (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={closeAllDropdowns}
                        className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                          isActive
                            ? 'bg-orange-100 text-orange-700'
                            : 'text-gray-600 hover:text-orange-600 hover:bg-orange-50'
                        }`}
                        {...(item.public ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
                      >
                        <Icon className="w-4 h-4" />
                        {item.label}
                        {item.public && <span className="text-xs bg-orange-200 text-orange-800 px-2 py-1 rounded-full ml-auto">Public</span>}
                      </Link>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Admin Dropdown */}
            <div className="relative">
              {(() => {
                const hasAdminActive = adminItems.some(item => location.pathname === item.path);
                return (
                  <button 
                    onClick={toggleAdminDropdown}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      hasAdminActive || isAdminOpen
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:text-blue-600 hover:bg-gray-50'
                    }`}>
                    <BuildingOffice2Icon className="w-4 h-4" />
                    Admin
                    {hasAdminActive && <div className="w-2 h-2 bg-blue-600 rounded-full ml-1" />}
                    <svg className={`w-4 h-4 transition-transform duration-200 ${isAdminOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                );
              })()}
              
              {/* Admin Dropdown Menu */}
              <div className={`absolute top-full left-0 mt-1 w-64 bg-white shadow-lg rounded-lg border border-gray-200 transition-all duration-200 z-50 ${
                isAdminOpen ? 'opacity-100 visible' : 'opacity-0 invisible'
              }`}>
                <div className="p-2 space-y-1">
                  {adminItems.map((item) => {
                    // Show based on user admin_level
                    const userAdminLevel = user?.admin_level || 'user';
                    
                    // Show "Request Campus Admin Access" for non-admins
                    if (item.showForNonAdmins && (userAdminLevel === 'user' || !user?.is_admin)) {
                      const Icon = item.icon;
                      const isActive = location.pathname === item.path;
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={closeAllDropdowns}
                          className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                            isActive
                              ? 'bg-blue-100 text-blue-700'
                              : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                          }`}
                        >
                          <Icon className="w-4 h-4" />
                          {item.label}
                        </Link>
                      );
                    }
                    
                    // Show specific dashboards based on admin level
                    if (item.requiredLevel) {
                      // Super admins can see all dashboards
                      if (userAdminLevel === 'super_admin' || user?.is_super_admin) {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;
                        return (
                          <Link
                            key={item.path}
                            to={item.path}
                            onClick={closeAllDropdowns}
                            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                              isActive
                                ? 'bg-blue-100 text-blue-700'
                                : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                            }`}
                          >
                            <Icon className="w-4 h-4" />
                            {item.label}
                          </Link>
                        );
                      }
                      
                      // Show only matching dashboard for specific admin level
                      if (userAdminLevel === item.requiredLevel || 
                          (item.requiredLevel === 'any_admin' && userAdminLevel !== 'user')) {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;
                        return (
                          <Link
                            key={item.path}
                            to={item.path}
                            onClick={closeAllDropdowns}
                            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                              isActive
                                ? 'bg-blue-100 text-blue-700'
                                : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                            }`}
                          >
                            <Icon className="w-4 h-4" />
                            {item.label}
                          </Link>
                        );
                      }
                      
                      return null;
                    }
                    
                    return null;
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-2 sm:space-x-4">
            {/* Real-time Notifications */}
            <div className="hidden sm:block">
              <RealTimeNotifications />
            </div>
            {/* Hamburger Menu Button - Show only on mobile/tablet */}
            <div className="lg:hidden">
              <button
                onClick={toggleMobileMenu}
                className="flex items-center justify-center w-10 h-10 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
                aria-label="Toggle menu"
              >
                {isMobileMenuOpen ? (
                  <XMarkIcon className="w-6 h-6" />
                ) : (
                  <Bars3Icon className="w-6 h-6" />
                )}
              </button>
            </div>

            {/* Mobile Profile Icon - Show only on mobile when menu is closed */}
            <div className="md:hidden lg:hidden">
              {!isMobileMenuOpen && (
                <Link to="/profile" onClick={closeMobileMenu} className="flex items-center hover:bg-gray-50 rounded-lg p-2 transition-colors">
                  {user?.profile_photo ? (
                    <img 
                      src={`${process.env.REACT_APP_BACKEND_URL}${user.profile_photo}`}
                      alt="Profile"
                      className="w-8 h-8 rounded-full object-cover"
                    />
                  ) : (
                    <UserCircleIcon className="w-8 h-8 text-gray-400" />
                  )}
                </Link>
              )}
            </div>

            {/* Desktop Profile Dropdown - Show full info on desktop */}
            <div className="hidden lg:block relative">
              <button 
                onClick={toggleProfileDropdown}
                className={`flex items-center space-x-3 rounded-lg p-2 transition-colors max-w-56 w-full ${
                  isProfileOpen ? 'bg-gray-100' : 'hover:bg-gray-50'
                }`}>
                {user?.profile_photo ? (
                  <img 
                    src={`${process.env.REACT_APP_BACKEND_URL}${user.profile_photo}`}
                    alt="Profile"
                    className="w-8 h-8 rounded-full object-cover flex-shrink-0"
                  />
                ) : (
                  <UserCircleIcon className="w-8 h-8 text-gray-400 flex-shrink-0" />
                )}
                <div className="text-sm min-w-0 flex-1 text-left">
                  <p className="font-semibold text-gray-900 truncate">{user?.full_name}</p>
                  <p className="text-gray-500 truncate">{formatCurrency(user?.total_earnings || 0)} earned</p>
                </div>
                <svg className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform duration-200 ${isProfileOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {/* Profile Dropdown Menu */}
              <div className={`absolute top-full right-0 mt-1 w-56 bg-white shadow-lg rounded-lg border border-gray-200 transition-all duration-200 z-50 ${
                isProfileOpen ? 'opacity-100 visible' : 'opacity-0 invisible'
              }`}>
                <div className="p-2 space-y-1">
                  {/* Profile Header */}
                  <div className="px-3 py-2 border-b border-gray-100">
                    <p className="font-medium text-gray-900 truncate">{user?.full_name}</p>
                    <p className="text-sm text-gray-500 truncate">{user?.email}</p>
                    <p className="text-xs text-emerald-600 font-medium mt-1">{formatCurrency(user?.total_earnings || 0)} total earned</p>
                  </div>
                  
                  {/* Profile Actions */}
                  <Link
                    to="/profile"
                    onClick={closeAllDropdowns}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 transition-all duration-200"
                  >
                    <UserCircleIcon className="w-4 h-4" />
                    View Profile
                  </Link>
                  
                  <Link
                    to="/gamification"
                    onClick={closeAllDropdowns}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-purple-600 hover:bg-purple-50 transition-all duration-200"
                  >
                    <TrophyIcon className="w-4 h-4" />
                    Achievements
                  </Link>
                  
                  <Link
                    to="/notifications"
                    onClick={closeAllDropdowns}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-yellow-600 hover:bg-yellow-50 transition-all duration-200"
                  >
                    <BellIcon className="w-4 h-4" />
                    Notification Settings
                  </Link>
                  
                  <div className="border-t border-gray-100 mt-2 pt-2">
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-red-600 hover:bg-red-50 transition-all duration-200 w-full text-left"
                    >
                      <ArrowRightOnRectangleIcon className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Mobile/Tablet Logout Button - Only show on smaller screens */}
            <div className="lg:hidden">
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-2 sm:px-3 py-2 text-sm font-medium text-gray-600 hover:text-red-600 transition-colors"
                title="Logout"
              >
                <ArrowRightOnRectangleIcon className="w-5 h-5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile/Tablet Dropdown Navigation */}
        {isMobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-100 bg-white shadow-lg">
            {/* Navigation Items */}
            <div className="px-4 py-4 space-y-2 max-h-96 overflow-y-auto">
              {/* Core Navigation */}
              {navItems.slice(0, 8).map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={closeMobileMenu}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'text-gray-600 hover:text-emerald-600 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {item.label}
                  </Link>
                );
              })}

              {/* Campus Section */}
              <div className="border-t border-gray-100 pt-4 mt-4">
                <div className="px-4 pb-2">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                    <BuildingOffice2Icon className="w-4 h-4" />
                    Campus Features
                  </h3>
                </div>
                {campusItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={closeMobileMenu}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-purple-100 text-purple-700'
                          : 'text-gray-600 hover:text-purple-600 hover:bg-purple-50'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      {item.label}
                    </Link>
                  );
                })}
              </div>

              {/* Viral Features Section */}
              <div className="border-t border-gray-100 pt-4 mt-4">
                <div className="px-4 pb-2">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                    <FireIcon className="w-4 h-4" />
                    🔥 Viral Features
                  </h3>
                </div>
                {viralItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={closeMobileMenu}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-orange-100 text-orange-700'
                          : 'text-gray-600 hover:text-orange-600 hover:bg-orange-50'
                      }`}
                      {...(item.public ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
                    >
                      <Icon className="w-5 h-5" />
                      {item.label}
                      {item.public && <span className="text-xs bg-orange-200 text-orange-800 px-2 py-1 rounded-full">Public</span>}
                    </Link>
                  );
                })}
              </div>

              {/* Admin Section */}
              <div className="border-t border-gray-100 pt-4 mt-4">
                <div className="px-4 pb-2">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                    <BuildingOffice2Icon className="w-4 h-4" />
                    Admin
                  </h3>
                </div>
                {adminItems.map((item) => {
                  // Show based on user admin_level
                  const userAdminLevel = user?.admin_level || 'user';
                  
                  // Show "Request Campus Admin Access" for non-admins
                  if (item.showForNonAdmins && (userAdminLevel === 'user' || !user?.is_admin)) {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;
                    return (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={closeMobileMenu}
                        className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                          isActive
                            ? 'bg-blue-100 text-blue-700'
                            : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                        {item.label}
                      </Link>
                    );
                  }
                  
                  // Show specific dashboards based on admin level
                  if (item.requiredLevel) {
                    // Super admins can see all dashboards
                    if (userAdminLevel === 'super_admin' || user?.is_super_admin) {
                      const Icon = item.icon;
                      const isActive = location.pathname === item.path;
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={closeMobileMenu}
                          className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                            isActive
                              ? 'bg-blue-100 text-blue-700'
                              : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                          }`}
                        >
                          <Icon className="w-5 h-5" />
                          {item.label}
                        </Link>
                      );
                    }
                    
                    // Show only matching dashboard for specific admin level
                    if (userAdminLevel === item.requiredLevel || 
                        (item.requiredLevel === 'any_admin' && userAdminLevel !== 'user')) {
                      const Icon = item.icon;
                      const isActive = location.pathname === item.path;
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={closeMobileMenu}
                          className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                            isActive
                              ? 'bg-blue-100 text-blue-700'
                              : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                          }`}
                        >
                          <Icon className="w-5 h-5" />
                          {item.label}
                        </Link>
                      );
                    }
                    
                    return null;
                  }
                  
                  return null;
                })}
              </div>
              
              {/* Profile Section */}
              <div className="border-t border-gray-100 pt-4 mt-4">
                <Link
                  to="/profile"
                  onClick={closeMobileMenu}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-600 hover:text-emerald-600 hover:bg-gray-50 transition-all duration-200"
                >
                  {user?.profile_photo ? (
                    <img 
                      src={`${process.env.REACT_APP_BACKEND_URL}${user.profile_photo}`}
                      alt="Profile"
                      className="w-5 h-5 rounded-full object-cover"
                    />
                  ) : (
                    <UserCircleIcon className="w-5 h-5" />
                  )}
                  <div>
                    <div className="font-semibold">{user?.full_name}</div>
                    <div className="text-xs text-gray-500">View Profile</div>
                  </div>
                </Link>
                
                {/* Logout Button */}
                <button
                  onClick={() => {
                    handleLogout();
                    closeMobileMenu();
                  }}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-600 hover:text-red-600 hover:bg-red-50 transition-all duration-200 w-full text-left mt-2"
                >
                  <ArrowRightOnRectangleIcon className="w-5 h-5" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navigation;
