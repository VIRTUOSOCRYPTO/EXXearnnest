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
  UserGroupIcon
} from '@heroicons/react/24/outline';
import { formatCurrency } from '../App';

const Navigation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const navRef = useRef(null);

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: HomeIcon },
    { path: '/transactions', label: 'Transactions', icon: CreditCardIcon },
    { path: '/budget', label: 'Budget', icon: BanknotesIcon },
    { path: '/goals', label: 'Goals', icon: StarIcon },
    { path: '/friends-referrals', label: 'Friends & Referrals', icon: UsersIcon },
    { path: '/challenges', label: 'Challenges', icon: FireIcon },
    { path: '/gamification', label: 'Achievements', icon: TrophyIcon },
    { path: '/notifications', label: 'Notifications', icon: BellIcon },
    { path: '/hustles', label: 'Side Hustles', icon: BriefcaseIcon },
    { path: '/analytics', label: 'Analytics', icon: ChartBarIcon },
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

  // Close mobile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (navRef.current && !navRef.current.contains(event.target)) {
        setIsMobileMenuOpen(false);
      }
    };

    if (isMobileMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isMobileMenuOpen]);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
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
            <h1 className="text-lg sm:text-2xl font-bold gradient-text truncate">EarnNest</h1>
          </div>

          {/* Navigation Links - Desktop */}
          <div className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
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
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-2 sm:space-x-4">
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

            {/* Desktop Profile - Show full info on desktop */}
            <div className="hidden lg:flex items-center space-x-3">
              <Link to="/profile" className="flex items-center space-x-3 hover:bg-gray-50 rounded-lg p-2 transition-colors max-w-48">
                {user?.profile_photo ? (
                  <img 
                    src={`${process.env.REACT_APP_BACKEND_URL}${user.profile_photo}`}
                    alt="Profile"
                    className="w-8 h-8 rounded-full object-cover flex-shrink-0"
                  />
                ) : (
                  <UserCircleIcon className="w-8 h-8 text-gray-400 flex-shrink-0" />
                )}
                <div className="text-sm min-w-0 flex-1">
                  <p className="font-semibold text-gray-900 truncate">{user?.full_name}</p>
                  <p className="text-gray-500 truncate">{formatCurrency(user?.total_earnings || 0)} earned</p>
                </div>
              </Link>
            </div>
            
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-2 sm:px-3 py-2 text-sm font-medium text-gray-600 hover:text-red-600 transition-colors"
              title="Logout"
            >
              <ArrowRightOnRectangleIcon className="w-5 h-5" />
              <span className="hidden lg:inline">Logout</span>
            </button>
          </div>
        </div>

        {/* Mobile/Tablet Dropdown Navigation */}
        {isMobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-100 bg-white shadow-lg">
            {/* Navigation Items */}
            <div className="px-4 py-4 space-y-2">
              {navItems.map((item) => {
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
