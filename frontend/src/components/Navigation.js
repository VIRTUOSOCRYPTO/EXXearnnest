import React from 'react';
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
  TrophyIcon
} from '@heroicons/react/24/outline';
import { formatCurrency } from '../App';

const Navigation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: HomeIcon },
    { path: '/transactions', label: 'Transactions', icon: CreditCardIcon },
    { path: '/budget', label: 'Budget', icon: BanknotesIcon },
    { path: '/goals', label: 'Goals', icon: StarIcon },
    { path: '/gamification', label: 'Achievements', icon: TrophyIcon },
    { path: '/hustles', label: 'Side Hustles', icon: BriefcaseIcon },
    { path: '/analytics', label: 'Analytics', icon: ChartBarIcon },
    { path: '/recommendations', label: 'Recommendations', icon: LightBulbIcon },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-shrink-0">
            <div className="w-7 h-7 sm:w-8 sm:h-8 bg-gradient-to-br from-emerald-500 to-green-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">₹</span>
            </div>
            <h1 className="text-lg sm:text-2xl font-bold gradient-text truncate">EarnNest</h1>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
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
            {/* Mobile Profile Icon - Show only on mobile */}
            <div className="md:hidden">
              <Link to="/profile" className="flex items-center hover:bg-gray-50 rounded-lg p-2 transition-colors">
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
            </div>

            {/* Desktop Profile - Show full info on desktop */}
            <div className="hidden md:flex items-center space-x-3">
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

        {/* Mobile Navigation */}
        <div className="md:hidden border-t border-gray-100 py-2">
          {/* Primary Navigation - Top Row */}
          <div className="grid grid-cols-3 gap-1 px-2 mb-2">
            {navItems.slice(0, 3).map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex flex-col items-center gap-1 py-2 px-1 rounded-lg text-xs font-medium transition-all duration-200 ${
                    isActive
                      ? 'text-emerald-700 bg-emerald-50'
                      : 'text-gray-600'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-xs truncate">{item.label}</span>
                </Link>
              );
            })}
          </div>
          
          {/* Secondary Navigation - Bottom Row */}
          <div className="grid grid-cols-3 gap-1 px-2">
            {navItems.slice(3).map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex flex-col items-center gap-1 py-2 px-1 rounded-lg text-xs font-medium transition-all duration-200 ${
                    isActive
                      ? 'text-emerald-700 bg-emerald-50'
                      : 'text-gray-600'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-xs truncate">{item.label === 'Side Hustles' ? 'Hustles' : item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
