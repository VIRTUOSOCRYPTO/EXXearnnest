import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  PlusIcon, 
  BanknotesIcon, 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon,
  CalendarIcon,
  TagIcon,
  LinkIcon,
  StarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  CurrencyRupeeIcon,
} from '@heroicons/react/24/outline';
import EnhancedCelebration from './EnhancedCelebration';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [budgetWarning, setBudgetWarning] = useState('');
  const [budgetInfo, setBudgetInfo] = useState({});
  const [isMultiCategory, setIsMultiCategory] = useState(false);
  const [categoryTouched, setCategoryTouched] = useState(false);
  
  // App suggestions state
  const [appSuggestions, setAppSuggestions] = useState([]);
  const [showAppSuggestions, setShowAppSuggestions] = useState(false);
  const [loadingAppSuggestions, setLoadingAppSuggestions] = useState(false);
  // Emergency services feature removed
  
  // Smart Return Detection states
  const [showReturnPrompt, setShowReturnPrompt] = useState(false);
  const [visitedApp, setVisitedApp] = useState(null);
  const [quickAddData, setQuickAddData] = useState({});
  const [isQuickAdding, setIsQuickAdding] = useState(false);
  
  // Milestone celebration states
  const [showMilestoneCelebration, setShowMilestoneCelebration] = useState(false);
  const [currentMilestone, setCurrentMilestone] = useState(null);
  
  // Voice Command functionality removed
  
  const [formData, setFormData] = useState({
    type: 'income',
    amount: '',
    category: '',
    description: '',
    source: '',
    is_hustle_related: false
  });
  
  // Multi-category form data
  const [multiCategoryData, setMultiCategoryData] = useState({
    type: 'expense',
    total_amount: '',
    description: '',
    categories: {}
  });

  const incomeCategories = ['Salary', 'Freelance', 'Tutoring', 'Side Hustle', 'Scholarship', 'Other'];
  const expenseCategories = [
    'Food', 'Transportation', 'Books', 'Entertainment', 'Rent', 'Utilities', 
    'Movies', 'Shopping', 'Groceries', 'Subscriptions', 'Emergency Fund', 'Other'
  ];

 

  useEffect(() => {
    fetchTransactions();
  }, []);

  useEffect(() => {
    // Check for return from app on component mount
    checkForReturnFromApp();
    
    // Listen for window focus to detect return
    const handleWindowFocus = () => {
      setTimeout(() => {
        checkForReturnFromApp();
      }, 1000); // Small delay to allow tab switching
    };
    
    window.addEventListener('focus', handleWindowFocus);
    
    return () => {
      window.removeEventListener('focus', handleWindowFocus);
    };
  }, []);

  // Smart Return Detection - Check if user returned from an app
  const checkForReturnFromApp = () => {
    const visitData = sessionStorage.getItem('earnest_app_visit');
    if (visitData) {
      try {
        const { app, category, timestamp } = JSON.parse(visitData);
        const now = new Date().getTime();
        const visitTime = new Date(timestamp).getTime();
        
        // Show prompt if return is within 30 minutes and not already shown
        if ((now - visitTime) < 30 * 60 * 1000 && !sessionStorage.getItem('earnest_prompt_shown')) {
          setVisitedApp(app);
          setShowReturnPrompt(true);
          
          // Pre-fill quick add data based on visited app
          const commonAmounts = getCommonAmounts(app.name);
          setQuickAddData({
            category: category,
            merchant: app.name,
            commonAmounts: commonAmounts,
            suggestedDescription: `${app.name} - Quick Purchase`
          });
          
          // Mark prompt as shown
          sessionStorage.setItem('earnest_prompt_shown', 'true');
        }
      } catch (error) {
        console.error('Error parsing visit data:', error);
      }
    }
  };

  // Get common purchase amounts for different apps
  const getCommonAmounts = (appName) => {
    const amounts = {
      'Zomato': [150, 250, 400, 600],
      'Swiggy': [180, 300, 450, 650], 
      'McDonald\'s': [200, 350, 500, 750],
      'Domino\'s': [300, 500, 800, 1200],
      'KFC': [250, 400, 600, 900],
      'Dunzo': [100, 200, 300, 500],
      'BookMyShow': [200, 400, 600, 1000],
      'Uber': [50, 100, 200, 350],
      'Rapido': [25, 50, 75, 150],
      'Amazon': [500, 1000, 2000, 5000],
      'Flipkart': [600, 1200, 2500, 5000],
      'Netflix': [199, 499, 649, 999],
      'Spotify': [119, 199, 389, 579]
    };
    
    return amounts[appName] || [100, 200, 500, 1000];
  };

  // Fetch app suggestions when category is selected
  const fetchAppSuggestions = async (category) => {
    if (!category || category === 'Other') {
      setShowAppSuggestions(false);
      setAppSuggestions([]);
      return;
    }
    
    // Emergency Fund now shows app suggestions like other categories
    
    setLoadingAppSuggestions(true);
    try {
      const response = await axios.get(`${API}/app-suggestions/${category}`);
      setAppSuggestions(response.data.apps || []);
      setShowAppSuggestions(response.data.apps && response.data.apps.length > 0);
    } catch (error) {
      console.error('Error fetching app suggestions:', error);
      setAppSuggestions([]);
      setShowAppSuggestions(false);
    } finally {
      setLoadingAppSuggestions(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  };

  // Enhanced app suggestion click with tracking
  const handleAppSuggestionClick = (app) => {
    // Store visit data for return detection
    const visitData = {
      app: app,
      category: formData.category || 'General',
      timestamp: new Date().toISOString(),
      sessionId: Date.now() + Math.random()
    };
    
    sessionStorage.setItem('earnest_app_visit', JSON.stringify(visitData));
    sessionStorage.removeItem('earnest_prompt_shown'); // Reset prompt flag
    
    // Add tracking parameters to URL if possible
    let trackingUrl = app.url;
    try {
      const url = new URL(app.url);
      url.searchParams.append('utm_source', 'earnest');
      url.searchParams.append('utm_medium', 'expense_tracker');
      url.searchParams.append('utm_campaign', 'smart_suggestions');
      trackingUrl = url.toString();
    } catch (error) {
      // Use original URL if parsing fails
      trackingUrl = app.url;
    }
    
    // Show loading indicator on the app card
    const appElement = document.getElementById(`app-${app.name.replace(/\s+/g, '')}`);
    if (appElement) {
      appElement.style.opacity = '0.7';
      appElement.style.transform = 'scale(0.98)';
    }
    
    // Open URL in new tab
    window.open(trackingUrl, '_blank', 'noopener,noreferrer');
    
    // Reset app card appearance after delay
    setTimeout(() => {
      if (appElement) {
        appElement.style.opacity = '1';
        appElement.style.transform = 'scale(1)';
      }
    }, 1000);
  };

  // Quick add transaction from return prompt
  const handleQuickAdd = async (amount, customAmount = null) => {
    setIsQuickAdding(true);
    
    // Close modal immediately for better UX
    setShowReturnPrompt(false);
    
    try {
      const finalAmount = customAmount || amount;
      const transactionData = {
        type: 'expense',
        amount: parseFloat(finalAmount),
        category: quickAddData.category,
        description: `${quickAddData.merchant} - Auto-detected purchase`,
        source: '',
        is_hustle_related: false
      };

      // Validate budget for expense
      const error = await validateExpenseBudget(quickAddData.category, parseFloat(finalAmount));
      if (error) {
        alert(error);
        // Clean up session data even on error
        sessionStorage.removeItem('earnest_app_visit');
        sessionStorage.removeItem('earnest_prompt_shown');
        return;
      }

      await axios.post(`${API}/transactions`, transactionData);
      
      // Clean up session data
      sessionStorage.removeItem('earnest_app_visit');
      sessionStorage.removeItem('earnest_prompt_shown');
      
      // Close the Add Transaction modal and redirect to transactions list
      setShowAddForm(false);
      
      // Refresh transactions to show the new entry
      fetchTransactions();
      
      // Show subtle success notification instead of alert
      const successMessage = document.createElement('div');
      successMessage.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 transform transition-all duration-300';
      successMessage.innerHTML = `
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
          </svg>
          <span>₹${finalAmount} transaction added successfully!</span>
        </div>
      `;
      document.body.appendChild(successMessage);
      
      // Remove notification after 3 seconds
      setTimeout(() => {
        successMessage.style.transform = 'translateX(100%)';
        setTimeout(() => {
          if (successMessage.parentNode) {
            successMessage.parentNode.removeChild(successMessage);
          }
        }, 300);
      }, 3000);
      
    } catch (error) {
      console.error('Error creating quick transaction:', error);
      if (error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert('Failed to create transaction. Please try again.');
      }
      
      // Clean up session data on error too
      sessionStorage.removeItem('earnest_app_visit');
      sessionStorage.removeItem('earnest_prompt_shown');
    } finally {
      setIsQuickAdding(false);
    }
  };

  // Dismiss return prompt
  const dismissReturnPrompt = () => {
    setShowReturnPrompt(false);
    sessionStorage.removeItem('earnest_app_visit');
    sessionStorage.removeItem('earnest_prompt_shown');
  };

  const fetchTransactions = async () => {
    try {
      const response = await axios.get(`${API}/transactions?limit=100`);
      setTransactions(response.data);
      
      // Check for milestones after fetching transactions
      await checkForMilestones();
    } catch (error) {
      console.error('Error fetching transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkForMilestones = async () => {
    try {
      // Get user's current financial stats
      const [analyticsRes, userRes] = await Promise.all([
        axios.get(`${API}/analytics/summary`),
        axios.get(`${API}/user/profile`)
      ]);

      const analytics = analyticsRes.data;
      const user = userRes.data;

      // Check for savings milestones
      const totalSavings = analytics.net_amount || 0;
      const savingsMilestones = [1000, 5000, 10000, 25000, 50000, 100000];
      
      for (const milestone of savingsMilestones) {
        if (totalSavings >= milestone && (!user.last_celebrated_savings || user.last_celebrated_savings < milestone)) {
          setCurrentMilestone({
            type: 'savings',
            title: 'Savings Milestone Reached!',
            message: `You've successfully saved ₹${milestone.toLocaleString()}! 🎉`,
            amount: milestone,
            stats: {
              'Total Savings': `₹${totalSavings.toLocaleString()}`,
              'Transactions': analytics.transaction_count,
              'Current Streak': `${user.current_streak || 0} days`
            },
            description: 'Every rupee saved brings you closer to financial freedom!'
          });
          setShowMilestoneCelebration(true);
          
          // Update user's last celebrated milestone
          await axios.put(`${API}/user/profile`, {
            last_celebrated_savings: milestone
          });
          break;
        }
      }

      // Check for streak milestones
      const currentStreak = user.current_streak || 0;
      const streakMilestones = [7, 15, 30, 60, 100];
      
      for (const milestone of streakMilestones) {
        if (currentStreak >= milestone && (!user.last_celebrated_streak || user.last_celebrated_streak < milestone)) {
          setCurrentMilestone({
            type: 'streak',
            title: 'Streak Achievement!',
            message: `Amazing! You've maintained a ${milestone}-day tracking streak! 🔥`,
            stats: {
              'Current Streak': `${currentStreak} days`,
              'Total Savings': `₹${totalSavings.toLocaleString()}`,
              'Transactions': analytics.transaction_count
            },
            description: 'Consistency is the key to financial success!'
          });
          setShowMilestoneCelebration(true);
          
          // Update user's last celebrated streak
          await axios.put(`${API}/user/profile`, {
            last_celebrated_streak: milestone
          });
          break;
        }
      }

      // Check for transaction count milestones
      const transactionCount = analytics.transaction_count || 0;
      const transactionMilestones = [10, 50, 100, 250, 500, 1000];
      
      for (const milestone of transactionMilestones) {
        if (transactionCount >= milestone && (!user.last_celebrated_transactions || user.last_celebrated_transactions < milestone)) {
          setCurrentMilestone({
            type: 'budget',
            title: 'Tracking Champion!',
            message: `You've recorded ${milestone} transactions! You're becoming a pro! 📊`,
            stats: {
              'Transactions': transactionCount,
              'Total Savings': `₹${totalSavings.toLocaleString()}`,
              'Average per Transaction': `₹${Math.round(totalSavings / transactionCount).toLocaleString()}`
            },
            description: 'The more you track, the better you manage!'
          });
          setShowMilestoneCelebration(true);
          
          // Update user's last celebrated transaction milestone
          await axios.put(`${API}/user/profile`, {
            last_celebrated_transactions: milestone
          });
          break;
        }
      }

    } catch (error) {
      console.error('Error checking milestones:', error);
    }
  };

  const checkCategoryBudget = async (category) => {
    try {
      const response = await axios.get(`${API}/budgets/category/${category}`);
      setBudgetInfo(prev => ({
        ...prev,
        [category]: response.data
      }));
      return response.data;
    } catch (error) {
      console.error('Error checking budget:', error);
      return null;
    }
  };

  const validateExpenseBudget = async (category, amount) => {
    const budget = await checkCategoryBudget(category);
    if (!budget || !budget.has_budget) {
      return `No budget allocated for '${category}' category. Please allocate budget first.`;
    }
    
    if (amount > budget.remaining_amount) {
      return `No money, you reached the limit! Remaining budget for '${category}': ₹${budget.remaining_amount.toFixed(2)}, but you're trying to spend ₹${amount.toFixed(2)}`;
    }
    
    return null; // No error
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setBudgetWarning('');
    
    try {
      if (isMultiCategory) {
        // Handle multi-category transaction
        const totalCategoryAmount = Object.values(multiCategoryData.categories).reduce((sum, amount) => sum + (parseFloat(amount) || 0), 0);
        
        if (Math.abs(totalCategoryAmount - parseFloat(multiCategoryData.total_amount)) > 0.01) {
          setBudgetWarning(`Category amounts (${formatCurrency(totalCategoryAmount)}) don't match total amount (${formatCurrency(parseFloat(multiCategoryData.total_amount))})`);
          return;
        }

        // Validate budget for each expense category
        if (multiCategoryData.type === 'expense') {
          for (const [category, amount] of Object.entries(multiCategoryData.categories)) {
            if (amount && parseFloat(amount) > 0) {
              const error = await validateExpenseBudget(category, parseFloat(amount));
              if (error) {
                setBudgetWarning(error);
                return;
              }
            }
          }
        }

        // Create separate transactions for each category
        const promises = Object.entries(multiCategoryData.categories).map(([category, amount]) => {
          if (amount && parseFloat(amount) > 0) {
            return axios.post(`${API}/transactions`, {
              type: multiCategoryData.type,
              amount: parseFloat(amount),
              category: category,
              description: `${multiCategoryData.description} (Split transaction)`,
              source: '',
              is_hustle_related: false
            });
          }
        }).filter(Boolean);

        await Promise.all(promises);
        
        // Reset multi-category form
        setMultiCategoryData({
          type: 'expense',
          total_amount: '',
          description: '',
          categories: {}
        });
      } else {
        // Handle single transaction
        const submitData = {
          ...formData,
          amount: parseFloat(formData.amount)
        };

        // Validate budget for single expense
        if (formData.type === 'expense') {
          const error = await validateExpenseBudget(formData.category, parseFloat(formData.amount));
          if (error) {
            setBudgetWarning(error);
            return;
          }
        }

        const response = await axios.post(`${API}/transactions`, submitData);
        
        // Check for immediate milestone data from backend
        if (response.data && response.data.milestone_data) {
          setCurrentMilestone({
            ...response.data.milestone_data,
            celebration_type: 'immediate'
          });
          setShowMilestoneCelebration(true);
        }
        
        // Reset single form
        setFormData({
          type: 'income',
          amount: '',
          category: '',
          description: '',
          source: '',
          is_hustle_related: false
        });
      }

      setShowAddForm(false);
      await fetchTransactions();
      
      // Check for additional pending celebrations from backend
      setTimeout(async () => {
        try {
          const celebrationsRes = await axios.get(`${API}/gamification/celebrations/pending`);
          if (celebrationsRes.data.celebrations.length > 0) {
            setCurrentMilestone({
              ...celebrationsRes.data.celebrations[0],
              celebration_type: 'pending'
            });
            setShowMilestoneCelebration(true);
          }
        } catch (error) {
          console.error('Error checking pending celebrations:', error);
        }
        
        // Fallback to legacy milestone check
        checkForMilestones();
      }, 1000);
      
    } catch (error) {
      console.error('Error creating transaction:', error);
      if (error.response?.data?.detail) {
        setBudgetWarning(error.response.data.detail);
      } else {
        setBudgetWarning('Failed to create transaction. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Handle category selection and suggestions
    if (name === 'category') {
      setCategoryTouched(true);
      
      // Reset all suggestion states
      setShowAppSuggestions(false);
      setAppSuggestions([]);
      
      if (value) {
        // Check budget for expense categories
        if (formData.type === 'expense') {
          checkCategoryBudget(value);
        }
        
        // Fetch app suggestions
        fetchAppSuggestions(value);
      }
    }
  };

  const handleMultiCategoryChange = (field, value) => {
    setMultiCategoryData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCategoryAmountChange = (category, amount) => {
    setMultiCategoryData(prev => ({
      ...prev,
      categories: {
        ...prev.categories,
        [category]: amount
      }
    }));
  };

  // Emergency services functions removed

  const handlePlaceCall = (phone) => {
    if (phone) {
      window.location.href = `tel:${phone}`;
    }
  };

  const calculateMultiCategoryTotal = () => {
    return Object.values(multiCategoryData.categories).reduce((sum, amount) => sum + (parseFloat(amount) || 0), 0);
  };

  // Google search handler for app suggestions
  const handleGoogleSearchTransaction = (category) => {
    const searchQueries = {
      'Food': 'best food delivery apps restaurants near me India',
      'Transportation': 'best transportation apps ride sharing public transport India',
      'Books': 'best book reading apps online bookstores India',
      'Entertainment': 'best entertainment apps streaming services India',
      'Rent': 'best rental apps apartment finder real estate India',
      'Utilities': 'best utility apps bill payment services India',
      'Movies': 'best movie streaming apps cinema booking India',
      'Shopping': 'best shopping apps online stores deals India',
      'Groceries': 'best grocery delivery apps supermarket online India',
      'Subscriptions': 'best subscription management apps services India',
      'Emergency Fund': 'emergency fund savings apps financial planning India',
      'Other': 'best apps services India'
    };
    
    const query = searchQueries[category] || `best ${category.toLowerCase()} apps India`;
    const googleUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
    window.open(googleUrl, '_blank', 'noopener,noreferrer');
  };

  // Voice command handlers removed

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const groupTransactionsByDate = (transactions) => {
    const groups = {};
    transactions.forEach(transaction => {
      const date = new Date(transaction.date).toDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(transaction);
    });
    return groups;
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-20 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  const groupedTransactions = groupTransactionsByDate(transactions);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 fade-in">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Transactions</h1>
          <p className="text-gray-600 mt-1">Track your income and expenses</p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="btn-primary flex items-center gap-2"
        >
          <PlusIcon className="w-5 h-5" />
          Add Transaction
        </button>
      </div>

      {/* Voice Command Interface removed */}

      {/* Add Transaction Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto slide-up">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold">Add New Transaction</h2>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsMultiCategory(!isMultiCategory)}
                  className={`px-3 py-1 text-sm rounded-full transition-colors ${
                    isMultiCategory 
                      ? 'bg-emerald-100 text-emerald-700' 
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {isMultiCategory ? 'Multi-Category' : 'Single Category'}
                </button>
              </div>
            </div>
            
            {isMultiCategory ? (
              /* Multi-Category Form */
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-blue-700 mb-2">
                    Split a single expense across multiple categories
                  </p>
                </div>

                {budgetWarning && (
                  <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
                    <p className="text-sm text-red-700">{budgetWarning}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Total Amount
                    </label>
                    <input
                      type="number"
                      value={multiCategoryData.total_amount}
                      onChange={(e) => handleMultiCategoryChange('total_amount', e.target.value)}
                      className="input-modern"
                      placeholder="0.00"
                      step="0.01"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Description
                    </label>
                    <input
                      type="text"
                      value={multiCategoryData.description}
                      onChange={(e) => handleMultiCategoryChange('description', e.target.value)}
                      className="input-modern"
                      placeholder="Brief description"
                      required
                    />
                  </div>
                </div>

                {/* Category Amount Grid */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-4">
                    Category Breakdown
                  </label>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {expenseCategories.map(category => (
                      <div key={category} className="bg-gray-50 p-3 rounded-lg">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          {category}
                        </label>
                        <input
                          type="number"
                          value={multiCategoryData.categories[category] || ''}
                          onChange={(e) => handleCategoryAmountChange(category, e.target.value)}
                          className="input-modern"
                          placeholder="0.00"
                          step="0.01"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Summary */}
                <div className="bg-emerald-50 p-4 rounded-lg">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Total Amount:</span>
                      <span className="font-semibold ml-2">
                        {formatCurrency(parseFloat(multiCategoryData.total_amount) || 0)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Categories Total:</span>
                      <span className={`font-semibold ml-2 ${
                        Math.abs(calculateMultiCategoryTotal() - (parseFloat(multiCategoryData.total_amount) || 0)) < 0.01
                          ? 'text-emerald-600' 
                          : 'text-red-500'
                      }`}>
                        {formatCurrency(calculateMultiCategoryTotal())}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddForm(false);
                      setIsMultiCategory(false);
                    }}
                    className="btn-secondary flex-1"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary flex-1"
                    disabled={submitting || Math.abs(calculateMultiCategoryTotal() - (parseFloat(multiCategoryData.total_amount) || 0)) > 0.01}
                  >
                    {submitting ? 'Adding...' : 'Add Multi-Category Transaction'}
                  </button>
                </div>
              </form>
            ) : (
              /* Single Transaction Form */
              <form onSubmit={handleSubmit} className="space-y-4">
                {budgetWarning && (
                  <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
                    <p className="text-sm text-red-700">{budgetWarning}</p>
                  </div>
                )}
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Type
                  </label>
                  <select
                    name="type"
                    value={formData.type}
                    onChange={handleChange}
                    className="input-modern"
                    required
                  >
                    <option value="income">Income</option>
                    <option value="expense">Expense</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Category
                  </label>
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleChange}
                    className="input-modern"
                    required
                  >
                    <option value="">Select category</option>
                    {(formData.type === 'income' ? incomeCategories : expenseCategories).map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                  
                  {/* Budget Information Display */}
                  {formData.type === 'expense' && formData.category && budgetInfo[formData.category] && (
                    <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <div className="text-xs font-semibold text-blue-800 mb-1">Budget Status for {formData.category}</div>
                      {budgetInfo[formData.category].has_budget ? (
                        <div className="grid grid-cols-3 gap-2 text-xs">
                          <div>
                            <span className="text-gray-600">Allocated:</span>
                            <div className="font-medium">{formatCurrency(budgetInfo[formData.category].allocated_amount)}</div>
                          </div>
                          <div>
                            <span className="text-gray-600">Spent:</span>
                            <div className="font-medium text-red-600">{formatCurrency(budgetInfo[formData.category].spent_amount)}</div>
                          </div>
                          <div>
                            <span className="text-gray-600">Remaining:</span>
                            <div className={`font-medium ${budgetInfo[formData.category].remaining_amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {formatCurrency(budgetInfo[formData.category].remaining_amount)}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-xs text-orange-600">
                          No budget allocated for this category. Please allocate budget first.
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Enhanced App Suggestions */}
                  {
                    showAppSuggestions && formData.category && (
                      <div className="mt-3 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
                        <div className="flex items-center gap-2 mb-3">
                          <LinkIcon className="w-4 h-4 text-blue-600" />
                          <h4 className="text-sm font-semibold text-blue-800">
                            Recommended Apps & Websites for {formData.category}
                          </h4>
                        </div>
                        
                        {loadingAppSuggestions ? (
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                            Loading app suggestions...
                          </div>
                        ) : appSuggestions.length > 0 ? (
                          <div>
                            <div className="mb-3 p-2 bg-gradient-to-r from-blue-100 to-indigo-100 rounded-lg">
                              <p className="text-xs text-blue-800 text-center">
                                💡 <strong>Smart Tracking:</strong> We'll detect when you return and help you quickly add transactions!
                              </p>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {appSuggestions.slice(0, 6).map((app, index) => (
                              <button
                                key={index}
                                id={`app-${app.name.replace(/\s+/g, '')}`}
                                type="button"
                                onClick={() => handleAppSuggestionClick(app)}
                                className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200 text-left group relative"
                              >
                                <div className="flex-shrink-0">
                                  <div className="w-8 h-8 bg-white rounded-lg border border-gray-200 flex items-center justify-center p-1">
                                    {app.logo ? (
                                      <img 
                                        src={app.logo} 
                                        alt={`${app.name} logo`}
                                        className="w-full h-full object-contain"
                                        onError={(e) => {
                                          // Hide the image and show fallback
                                          e.target.style.display = 'none';
                                          const fallback = document.createElement('div');
                                          fallback.className = 'w-full h-full bg-gradient-to-br from-blue-500 to-indigo-500 rounded flex items-center justify-center text-white text-xs font-semibold';
                                          fallback.textContent = app.name.charAt(0);
                                          e.target.parentElement.appendChild(fallback);
                                        }}
                                        style={{maxWidth: '100%', maxHeight: '100%'}}
                                      />
                                    ) : (
                                      <div className="w-full h-full bg-gradient-to-br from-blue-500 to-indigo-500 rounded flex items-center justify-center text-white text-xs font-semibold">
                                        {app.name.charAt(0)}
                                      </div>
                                    )}
                                  </div>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1">
                                    <h5 className="font-medium text-gray-900 text-sm truncate">
                                      {app.name}
                                    </h5>
                                    {app.price_comparison && (
                                      <span className="bg-orange-100 text-orange-600 text-xs px-1 rounded">💰</span>
                                    )}
                                  </div>
                                  {app.description && (
                                    <p className="text-xs text-gray-500 truncate">
                                      {app.description}
                                    </p>
                                  )}
                                  <div className="text-xs text-blue-600 capitalize">
                                    {app.type} • Click to visit & track
                                  </div>
                                </div>
                                <div className="flex flex-col items-center gap-1">
                                  <LinkIcon className="w-4 h-4 text-gray-400 group-hover:text-blue-600 transition-colors" />
                                  <div className="w-2 h-2 bg-green-400 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
                                </div>
                              </button>
                            ))}
                            </div>
                            
                            {/* Search on Google Button */}
                            <div className="mt-4 text-center">
                              <button
                                type="button"
                                onClick={() => handleGoogleSearchTransaction(formData.category)}
                                className="inline-flex items-center gap-2 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors duration-200"
                              >
                                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                                </svg>
                                Search on Google
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div>
                            <p className="text-sm text-gray-600 mb-4">No app suggestions available for this category.</p>
                            
                            {/* Search on Google Button for empty suggestions */}
                            <div className="text-center">
                              <button
                                type="button"
                                onClick={() => handleGoogleSearchTransaction(formData.category)}
                                className="inline-flex items-center gap-2 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors duration-200"
                              >
                                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                                </svg>
                                Search on Google
                              </button>
                            </div>
                          </div>
                        )}
                        
                        {formData.category.toLowerCase() === 'shopping' && appSuggestions.some(app => app.price_comparison) && (
                          <div className="mt-3 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-orange-600">💰</span>
                              <h6 className="text-sm font-semibold text-orange-800">Price Comparison Tips</h6>
                            </div>
                            <p className="text-xs text-orange-700">
                              Compare prices across multiple apps to get the best deals. Check for coupons and cashback offers!
                            </p>
                          </div>
                        )}
                      </div>
                    )
                  }
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Amount
                  </label>
                  <input
                    type="number"
                    name="amount"
                    value={formData.amount}
                    onChange={handleChange}
                    className="input-modern"
                    placeholder="0.00"
                    step="0.01"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Description
                  </label>
                  <input
                    type="text"
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    className="input-modern"
                    placeholder="Brief description"
                    required
                  />
                </div>

                {formData.type === 'income' && (
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Source (Optional)
                    </label>
                    <input
                      type="text"
                      name="source"
                      value={formData.source}
                      onChange={handleChange}
                      className="input-modern"
                      placeholder="e.g., Upwork, Company Name"
                    />
                  </div>
                )}

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    name="is_hustle_related"
                    checked={formData.is_hustle_related}
                    onChange={handleChange}
                    className="w-4 h-4 text-emerald-600 rounded mr-2"
                  />
                  <label className="text-sm text-gray-700">
                    This is related to a side hustle
                  </label>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="btn-secondary flex-1"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary flex-1"
                    disabled={submitting}
                  >
                    {submitting ? 'Adding...' : 'Add Transaction'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Transactions List */}
      <div className="space-y-6">
        {Object.keys(groupedTransactions).length > 0 ? (
          Object.entries(groupedTransactions)
            .sort(([a], [b]) => new Date(b) - new Date(a))
            .map(([date, dayTransactions]) => (
              <div key={date} className="slide-up">
                <div className="flex items-center gap-3 mb-3">
                  <CalendarIcon className="w-5 h-5 text-gray-400" />
                  <h3 className="font-semibold text-gray-700">
                    {new Date(date).toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </h3>
                </div>
                
                <div className="space-y-2">
                  {dayTransactions.map((transaction) => (
                    <div
                      key={transaction.id}
                      className={`transaction-item card-hover ${
                        transaction.type === 'income' ? 'transaction-income' : 'transaction-expense'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`p-2 rounded-full ${
                            transaction.type === 'income' 
                              ? 'bg-emerald-100' 
                              : 'bg-red-100'
                          }`}>
                            {transaction.type === 'income' ? (
                              <ArrowTrendingUpIcon className="w-5 h-5 text-emerald-600" />
                            ) : (
                              <ArrowTrendingDownIcon className="w-5 h-5 text-red-500" />
                            )}
                          </div>
                          
                          <div>
                            <h4 className="font-semibold text-gray-900">{transaction.description}</h4>
                            <div className="flex items-center gap-3 mt-1">
                              <div className="flex items-center gap-1">
                                <TagIcon className="w-4 h-4 text-gray-400" />
                                <span className="text-sm text-gray-500">{transaction.category}</span>
                              </div>
                              
                              {transaction.source && (
                                <span className="text-sm text-gray-500">
                                  • {transaction.source}
                                </span>
                              )}
                              
                              {transaction.is_hustle_related && (
                                <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                                  Side Hustle
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        <div className="text-right">
                          <p className={`font-bold text-lg ${
                            transaction.type === 'income' ? 'text-emerald-600' : 'text-red-500'
                          }`}>
                            {transaction.type === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
                          </p>
                          <p className="text-sm text-gray-500">
                            {formatDate(transaction.date)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
        ) : (
          <div className="text-center py-12 slide-up">
            <BanknotesIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-xl font-semibold text-gray-500 mb-2">No transactions yet</h3>
            <p className="text-gray-400 mb-6">Start tracking your income and expenses to see them here</p>
            <button
              onClick={() => setShowAddForm(true)}
              className="btn-primary"
            >
              Add Your First Transaction
            </button>
          </div>
        )}
      </div>

      {/* Smart Return Prompt Modal */}
      {showReturnPrompt && visitedApp && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md slide-up shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center">
                <CheckCircleIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Welcome back!</h3>
                <p className="text-sm text-gray-600">Did you make a purchase at {visitedApp.name}?</p>
              </div>
            </div>

            <div className="mb-4 p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <ClockIcon className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">Quick Add Options</span>
              </div>
              <p className="text-xs text-blue-700">
                Category: {quickAddData.category} • Merchant: {quickAddData.merchant}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 mb-4">
              {quickAddData.commonAmounts?.map((amount, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickAdd(amount)}
                  disabled={isQuickAdding}
                  className="flex items-center justify-center gap-2 p-3 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded-lg transition-all duration-200 hover:scale-105 disabled:opacity-50"
                >
                  <CurrencyRupeeIcon className="w-4 h-4" />
                  <span className="font-semibold">{amount}</span>
                </button>
              ))}
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Custom Amount
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Enter amount"
                  className="flex-1 input-modern text-sm"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && e.target.value) {
                      handleQuickAdd(null, e.target.value);
                    }
                  }}
                  disabled={isQuickAdding}
                />
                <button
                  onClick={(e) => {
                    const input = e.target.previousElementSibling;
                    if (input.value) {
                      handleQuickAdd(null, input.value);
                    }
                  }}
                  disabled={isQuickAdding}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
                >
                  {isQuickAdding ? '...' : 'Add'}
                </button>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={dismissReturnPrompt}
                disabled={isQuickAdding}
                className="flex-1 btn-secondary text-sm"
              >
                No, I didn't buy anything
              </button>
              <button
                onClick={() => {
                  dismissReturnPrompt();
                  setShowAddForm(true);
                }}
                disabled={isQuickAdding}
                className="flex-1 btn-primary text-sm"
              >
                Add Manually
              </button>
            </div>

            {isQuickAdding && (
              <div className="mt-3 flex items-center justify-center gap-2 text-sm text-emerald-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-emerald-600"></div>
                Adding transaction...
              </div>
            )}
          </div>
        </div>
      )}

      {/* Voice Command Confirmation Modal removed */}

      {/* Enhanced Celebration Modal - Phase 1 */}
      {showMilestoneCelebration && currentMilestone && (
        <EnhancedCelebration
          celebration={currentMilestone}
          onClose={() => {
            setShowMilestoneCelebration(false);
            setCurrentMilestone(null);
          }}
        />
      )}
    </div>
  );
};

export default Transactions;
