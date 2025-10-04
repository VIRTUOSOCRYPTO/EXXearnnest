import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import {
  UserGroupIcon,
  CurrencyRupeeIcon,
  PlusIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  DocumentIcon,
  ShareIcon,
  CalendarIcon,
  TagIcon,
  UsersIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const GroupExpenses = () => {
  const [groupExpenses, setGroupExpenses] = useState([]);
  const [friends, setFriends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newExpense, setNewExpense] = useState({
    title: '',
    description: '',
    total_amount: '',
    category: 'Food',
    settlement_method: 'equal',
    participants: []
  });
  const { user } = useAuth();

  useEffect(() => {
    fetchGroupExpenses();
    fetchFriends();
  }, []);

  const fetchGroupExpenses = async () => {
    try {
      const response = await axios.get(`${API}/expenses/group`);
      setGroupExpenses(response.data.group_expenses);
    } catch (error) {
      console.error('Error fetching group expenses:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFriends = async () => {
    try {
      const response = await axios.get(`${API}/friends`);
      setFriends(response.data.friends || []);
    } catch (error) {
      console.error('Error fetching friends:', error);
    }
  };

  const addParticipant = (friend) => {
    if (!newExpense.participants.find(p => p.user_id === friend.user_id)) {
      const amount = newExpense.settlement_method === 'equal' 
        ? parseFloat(newExpense.total_amount) / (newExpense.participants.length + 2) // +2 for creator and new participant
        : 0;

      setNewExpense({
        ...newExpense,
        participants: [
          ...newExpense.participants,
          {
            user_id: friend.user_id,
            name: friend.name,
            amount: amount,
            paid: false
          }
        ]
      });
    }
  };

  const removeParticipant = (userId) => {
    setNewExpense({
      ...newExpense,
      participants: newExpense.participants.filter(p => p.user_id !== userId)
    });
  };

  const updateParticipantAmount = (userId, amount) => {
    setNewExpense({
      ...newExpense,
      participants: newExpense.participants.map(p =>
        p.user_id === userId ? { ...p, amount: parseFloat(amount) || 0 } : p
      )
    });
  };

  const recalculateEqualAmounts = () => {
    const totalParticipants = newExpense.participants.length + 1; // +1 for creator
    const amountPerPerson = parseFloat(newExpense.total_amount) / totalParticipants;
    
    setNewExpense({
      ...newExpense,
      participants: newExpense.participants.map(p => ({
        ...p,
        amount: amountPerPerson || 0
      }))
    });
  };

  const createGroupExpense = async () => {
    try {
      // Validate inputs
      if (!newExpense.title || !newExpense.total_amount || newExpense.participants.length === 0) {
        alert('Please fill in all required fields and add at least one participant.');
        return;
      }

      const totalParticipantAmount = newExpense.participants.reduce((sum, p) => sum + p.amount, 0);
      const tolerance = 0.01; // Allow small rounding differences
      
      if (newExpense.settlement_method === 'custom' && 
          Math.abs(totalParticipantAmount - parseFloat(newExpense.total_amount)) > tolerance) {
        alert('The sum of participant amounts must equal the total amount.');
        return;
      }

      const response = await axios.post(`${API}/expenses/group/create`, newExpense);
      
      alert(`Group expense "${newExpense.title}" created successfully! ${response.data.participants_notified} participants notified.`);
      
      // Reset form and close modal
      setNewExpense({
        title: '',
        description: '',
        total_amount: '',
        category: 'Food',
        settlement_method: 'equal',
        participants: []
      });
      setShowCreateModal(false);
      
      // Refresh group expenses
      fetchGroupExpenses();
      
    } catch (error) {
      console.error('Error creating group expense:', error);
      alert(error.response?.data?.detail || 'Failed to create group expense');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-emerald-500" />;
      case 'pending':
        return <ClockIcon className="w-5 h-5 text-yellow-500" />;
      case 'disputed':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <UserGroupIcon className="w-8 h-8 text-emerald-500 mx-auto mb-4 animate-pulse" />
          <p className="text-gray-600">Loading group expenses...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Group Expenses</h1>
            <p className="text-gray-600 mt-1">Split bills and track settlements with friends</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors"
          >
            <PlusIcon className="w-5 h-5" />
            <span>Split Bill</span>
          </button>
        </div>
      </div>

      {/* Group Expenses List */}
      <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-200">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Your Group Expenses</h2>

        {groupExpenses.length === 0 ? (
          <div className="text-center py-12">
            <UserGroupIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No group expenses yet</h3>
            <p className="text-gray-600 mb-6">Create your first group expense to split bills with friends</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors"
            >
              Split Your First Bill
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {groupExpenses.map((expense) => (
              <div key={expense.id} className="border border-gray-200 rounded-xl p-6 hover:border-emerald-300 hover:shadow-md transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{expense.title}</h3>
                    {expense.description && (
                      <p className="text-sm text-gray-600 mt-1">{expense.description}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="flex items-center space-x-2 mb-2">
                      <CurrencyRupeeIcon className="w-5 h-5 text-emerald-500" />
                      <span className="text-2xl font-bold text-gray-900">₹{expense.total_amount}</span>
                    </div>
                    <div className={`flex items-center space-x-1 px-3 py-1 rounded-full text-sm ${
                      expense.settled 
                        ? 'bg-emerald-100 text-emerald-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {getStatusIcon(expense.user_status)}
                      <span>{expense.settled ? 'Settled' : 'Pending'}</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="flex items-center text-sm text-gray-600">
                    <TagIcon className="w-4 h-4 mr-2" />
                    <span>{expense.category}</span>
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-600">
                    <UsersIcon className="w-4 h-4 mr-2" />
                    <span>{expense.participant_count} participant{expense.participant_count !== 1 ? 's' : ''}</span>
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-600">
                    <CalendarIcon className="w-4 h-4 mr-2" />
                    <span>{formatDate(expense.created_at)}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {expense.is_creator && (
                      <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                        Created by you
                      </span>
                    )}
                    
                    {expense.user_amount > 0 && (
                      <div className="flex items-center text-sm">
                        <span className="text-gray-600 mr-2">Your share:</span>
                        <span className="font-semibold text-gray-900">₹{expense.user_amount}</span>
                      </div>
                    )}
                    
                    {expense.receipt_available && (
                      <div className="flex items-center text-sm text-emerald-600">
                        <DocumentIcon className="w-4 h-4 mr-1" />
                        <span>Receipt attached</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    <button className="px-3 py-2 text-emerald-600 hover:text-emerald-800 hover:bg-emerald-100 rounded-lg transition-colors text-sm">
                      View Details
                    </button>
                    
                    {!expense.settled && expense.user_amount > 0 && expense.user_status === 'pending' && (
                      <button className="px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors text-sm">
                        Settle Now
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Group Expense Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-gray-900">Split Group Expense</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>

              <form className="space-y-6">
                {/* Basic Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Expense Title *
                    </label>
                    <input
                      type="text"
                      value={newExpense.title}
                      onChange={(e) => setNewExpense({...newExpense, title: e.target.value})}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                      placeholder="Dinner at restaurant"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Total Amount *
                    </label>
                    <div className="relative">
                      <CurrencyRupeeIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="number"
                        value={newExpense.total_amount}
                        onChange={(e) => {
                          setNewExpense({...newExpense, total_amount: e.target.value});
                          if (newExpense.settlement_method === 'equal') {
                            setTimeout(recalculateEqualAmounts, 100);
                          }
                        }}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                        placeholder="0.00"
                        required
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description (Optional)
                  </label>
                  <textarea
                    value={newExpense.description}
                    onChange={(e) => setNewExpense({...newExpense, description: e.target.value})}
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="Additional details about the expense..."
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Category
                    </label>
                    <select
                      value={newExpense.category}
                      onChange={(e) => setNewExpense({...newExpense, category: e.target.value})}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    >
                      <option value="Food">Food & Dining</option>
                      <option value="Transportation">Transportation</option>
                      <option value="Entertainment">Entertainment</option>
                      <option value="Shopping">Shopping</option>
                      <option value="Utilities">Utilities</option>
                      <option value="Travel">Travel</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Split Method
                    </label>
                    <select
                      value={newExpense.settlement_method}
                      onChange={(e) => {
                        setNewExpense({...newExpense, settlement_method: e.target.value});
                        if (e.target.value === 'equal') {
                          setTimeout(recalculateEqualAmounts, 100);
                        }
                      }}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    >
                      <option value="equal">Split Equally</option>
                      <option value="custom">Custom Amounts</option>
                    </select>
                  </div>
                </div>

                {/* Add Participants */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Add Participants ({newExpense.participants.length} selected)
                  </label>
                  
                  {friends.length === 0 ? (
                    <div className="text-center py-6 bg-gray-50 rounded-lg border border-gray-200">
                      <UsersIcon className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                      <p className="text-sm text-gray-600">No friends available. Add friends first to split expenses.</p>
                    </div>
                  ) : (
                    <div className="space-y-3 max-h-40 overflow-y-auto border border-gray-200 rounded-lg p-4">
                      {friends.map((friend) => (
                        <div key={friend.user_id} className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
                              <span className="text-sm font-medium text-emerald-600">
                                {friend.name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <span className="text-sm text-gray-900">{friend.name}</span>
                          </div>
                          
                          {newExpense.participants.find(p => p.user_id === friend.user_id) ? (
                            <button
                              type="button"
                              onClick={() => removeParticipant(friend.user_id)}
                              className="text-red-600 hover:text-red-800 text-sm"
                            >
                              Remove
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => addParticipant(friend)}
                              className="text-emerald-600 hover:text-emerald-800 text-sm"
                            >
                              Add
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Participant Amounts */}
                {newExpense.participants.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      Participant Amounts
                    </label>
                    
                    <div className="space-y-3">
                      {/* Creator (You) */}
                      <div className="flex items-center justify-between p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-emerald-500 rounded-full flex items-center justify-center">
                            <span className="text-sm font-medium text-white">You</span>
                          </div>
                          <span className="text-sm text-gray-900">{user?.full_name || 'You'} (Creator)</span>
                        </div>
                        <div className="text-sm text-emerald-700 font-medium">
                          ₹{newExpense.settlement_method === 'equal' && newExpense.total_amount
                            ? (parseFloat(newExpense.total_amount) - newExpense.participants.reduce((sum, p) => sum + p.amount, 0)).toFixed(2)
                            : '0.00'
                          }
                        </div>
                      </div>

                      {/* Participants */}
                      {newExpense.participants.map((participant) => (
                        <div key={participant.user_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center">
                              <span className="text-sm font-medium text-white">
                                {participant.name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <span className="text-sm text-gray-900">{participant.name}</span>
                          </div>
                          
                          {newExpense.settlement_method === 'custom' ? (
                            <div className="relative">
                              <CurrencyRupeeIcon className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                              <input
                                type="number"
                                value={participant.amount}
                                onChange={(e) => updateParticipantAmount(participant.user_id, e.target.value)}
                                className="w-24 pl-6 pr-2 py-1 border border-gray-300 rounded text-sm"
                                placeholder="0.00"
                              />
                            </div>
                          ) : (
                            <div className="text-sm text-gray-700 font-medium">
                              ₹{participant.amount.toFixed(2)}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                    {newExpense.settlement_method === 'custom' && (
                      <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <div className="text-sm text-blue-700">
                          Total assigned: ₹{newExpense.participants.reduce((sum, p) => sum + p.amount, 0).toFixed(2)} of ₹{newExpense.total_amount}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-end space-x-4 pt-6 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-6 py-3 text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={createGroupExpense}
                    disabled={!newExpense.title || !newExpense.total_amount || newExpense.participants.length === 0}
                    className="px-8 py-3 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Create & Split
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GroupExpenses;
