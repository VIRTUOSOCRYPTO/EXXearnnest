import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import {
  PhotoIcon,
  DocumentIcon,
  ShareIcon,
  EyeIcon,
  CalendarIcon,
  CurrencyRupeeIcon,
  TagIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  CloudArrowUpIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ExpenseReceipts = () => {
  const [receipts, setReceipts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [selectedReceipt, setSelectedReceipt] = useState(null);
  const [shareCaption, setShareCaption] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const { user } = useAuth();

  useEffect(() => {
    fetchReceipts();
  }, []);

  const fetchReceipts = async () => {
    try {
      const response = await axios.get(`${API}/expenses/receipts`);
      setReceipts(response.data.receipts);
    } catch (error) {
      console.error('Error fetching receipts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (files) => {
    const file = files[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
      if (!allowedTypes.includes(file.type)) {
        alert('Please select a valid image (JPG, PNG) or PDF file.');
        return;
      }

      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB.');
        return;
      }

      setSelectedFile(file);
      uploadReceipt(file);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  const uploadReceipt = async (file) => {
    try {
      setUploading(true);
      
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API}/expenses/upload-receipt`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Add the new receipt to the list
      await fetchReceipts();
      
      // Show success message with OCR results
      const { extracted_data } = response.data;
      let message = 'Receipt uploaded successfully!';
      
      if (extracted_data.merchant_name) {
        message += `\n\nDetected: ${extracted_data.merchant_name}`;
      }
      if (extracted_data.amount) {
        message += `\nAmount: ₹${extracted_data.amount}`;
      }
      if (extracted_data.category) {
        message += `\nCategory: ${extracted_data.category}`;
      }

      alert(message);
      setSelectedFile(null);
      
    } catch (error) {
      console.error('Error uploading receipt:', error);
      alert('Failed to upload receipt. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const shareReceipt = async () => {
    if (!selectedReceipt || selectedPlatforms.length === 0) {
      alert('Please select at least one platform to share.');
      return;
    }

    try {
      const response = await axios.post(`${API}/expenses/share-receipt/${selectedReceipt.id}`, {
        platforms: selectedPlatforms,
        caption: shareCaption
      });

      alert(`Receipt shared successfully on ${selectedPlatforms.join(', ')}!`);
      setShowShareModal(false);
      setSelectedReceipt(null);
      setShareCaption('');
      setSelectedPlatforms([]);
      
      // Refresh receipts to update sharing stats
      fetchReceipts();
      
    } catch (error) {
      console.error('Error sharing receipt:', error);
      alert('Failed to share receipt. Please try again.');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <DocumentIcon className="w-8 h-8 text-emerald-500 mx-auto mb-4 animate-bounce" />
          <p className="text-gray-600">Loading receipts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Expense Receipts</h1>
        <p className="text-gray-600 mt-1">Upload and share your expense receipts with OCR processing</p>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-200 mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Upload Receipt</h2>
        
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
            dragActive 
              ? 'border-emerald-400 bg-emerald-50' 
              : 'border-gray-300 hover:border-emerald-400 hover:bg-emerald-50'
          }`}
        >
          <input
            type="file"
            accept="image/*,.pdf"
            onChange={(e) => handleFileSelect(e.target.files)}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={uploading}
          />
          
          <div className="space-y-4">
            {uploading ? (
              <>
                <CloudArrowUpIcon className="w-12 h-12 text-emerald-500 mx-auto animate-bounce" />
                <div>
                  <p className="text-lg font-medium text-gray-900">Processing receipt...</p>
                  <p className="text-sm text-gray-600">OCR scanning in progress</p>
                </div>
              </>
            ) : selectedFile ? (
              <>
                <DocumentIcon className="w-12 h-12 text-emerald-500 mx-auto" />
                <div>
                  <p className="text-lg font-medium text-gray-900">{selectedFile.name}</p>
                  <p className="text-sm text-gray-600">Ready to upload</p>
                </div>
              </>
            ) : (
              <>
                <PhotoIcon className="w-12 h-12 text-gray-400 mx-auto" />
                <div>
                  <p className="text-lg font-medium text-gray-900">Drop your receipt here</p>
                  <p className="text-sm text-gray-600">Or click to browse files</p>
                  <p className="text-xs text-gray-500 mt-2">Supports JPG, PNG, PDF (Max 10MB)</p>
                </div>
              </>
            )}
          </div>
          
          <div className="mt-6 flex items-center justify-center space-x-4">
            <div className="flex items-center text-sm text-emerald-600">
              <MagnifyingGlassIcon className="w-4 h-4 mr-1" />
              <span>OCR Processing</span>
            </div>
            <div className="flex items-center text-sm text-blue-600">
              <ShareIcon className="w-4 h-4 mr-1" />
              <span>Smart Sharing</span>
            </div>
          </div>
        </div>
      </div>

      {/* Receipts Grid */}
      <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Your Receipts</h2>
          <span className="text-sm text-gray-600">{receipts.length} receipts uploaded</span>
        </div>

        {receipts.length === 0 ? (
          <div className="text-center py-12">
            <DocumentIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No receipts yet</h3>
            <p className="text-gray-600">Upload your first expense receipt to get started</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {receipts.map((receipt) => (
              <div key={receipt.id} className="border border-gray-200 rounded-xl p-6 hover:border-emerald-300 hover:shadow-md transition-all">
                {/* Receipt Preview */}
                <div className="mb-4">
                  <div className="aspect-square bg-gray-100 rounded-lg mb-3 overflow-hidden">
                    <img
                      src={receipt.file_url}
                      alt={receipt.original_filename}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                    <div className="w-full h-full bg-gray-200 items-center justify-center hidden">
                      <DocumentIcon className="w-12 h-12 text-gray-400" />
                    </div>
                  </div>
                  
                  <h3 className="font-semibold text-gray-900 truncate" title={receipt.original_filename}>
                    {receipt.original_filename}
                  </h3>
                </div>

                {/* Receipt Details */}
                <div className="space-y-2 mb-4">
                  {receipt.merchant_name && (
                    <div className="flex items-center text-sm">
                      <TagIcon className="w-4 h-4 text-gray-400 mr-2" />
                      <span className="text-gray-600">{receipt.merchant_name}</span>
                    </div>
                  )}
                  
                  {receipt.amount && (
                    <div className="flex items-center text-sm">
                      <CurrencyRupeeIcon className="w-4 h-4 text-emerald-500 mr-2" />
                      <span className="text-emerald-600 font-medium">₹{receipt.amount}</span>
                    </div>
                  )}
                  
                  {receipt.category && (
                    <div className="flex items-center text-sm">
                      <TagIcon className="w-4 h-4 text-blue-500 mr-2" />
                      <span className="text-blue-600">{receipt.category}</span>
                    </div>
                  )}
                  
                  <div className="flex items-center text-sm">
                    <CalendarIcon className="w-4 h-4 text-gray-400 mr-2" />
                    <span className="text-gray-600">{formatDate(receipt.uploaded_at)}</span>
                  </div>
                </div>

                {/* Sharing Stats */}
                {receipt.shared_count > 0 && (
                  <div className="mb-4 p-3 bg-purple-50 rounded-lg border border-purple-200">
                    <div className="flex items-center text-sm">
                      <ShareIcon className="w-4 h-4 text-purple-500 mr-2" />
                      <span className="text-purple-700">
                        Shared {receipt.shared_count} time{receipt.shared_count !== 1 ? 's' : ''}
                      </span>
                    </div>
                    {receipt.shared_platforms.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {receipt.shared_platforms.map((platform, idx) => (
                          <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                            {platform}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Transaction Status */}
                {receipt.has_transaction ? (
                  <div className="flex items-center text-sm mb-4">
                    <CheckCircleIcon className="w-4 h-4 text-emerald-500 mr-2" />
                    <span className="text-emerald-600">Linked to transaction</span>
                  </div>
                ) : (
                  <div className="flex items-center text-sm mb-4">
                    <ExclamationTriangleIcon className="w-4 h-4 text-yellow-500 mr-2" />
                    <span className="text-yellow-600">No transaction created</span>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => window.open(receipt.file_url, '_blank')}
                    className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors text-sm"
                  >
                    <EyeIcon className="w-4 h-4 mr-1" />
                    View
                  </button>
                  
                  <button
                    onClick={() => {
                      setSelectedReceipt(receipt);
                      setShowShareModal(true);
                    }}
                    className="flex items-center px-3 py-2 text-emerald-600 hover:text-emerald-800 hover:bg-emerald-100 rounded-lg transition-colors text-sm"
                  >
                    <ShareIcon className="w-4 h-4 mr-1" />
                    Share
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Share Modal */}
      {showShareModal && selectedReceipt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-900">Share Receipt</h3>
                <button
                  onClick={() => setShowShareModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>

              {/* Receipt Info */}
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900">{selectedReceipt.original_filename}</h4>
                {selectedReceipt.merchant_name && (
                  <p className="text-sm text-gray-600">From: {selectedReceipt.merchant_name}</p>
                )}
                {selectedReceipt.amount && (
                  <p className="text-sm text-gray-600">Amount: ₹{selectedReceipt.amount}</p>
                )}
              </div>

              {/* Platform Selection */}
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-3">Select Platforms</h4>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { id: 'instagram', name: 'Instagram', color: 'purple' },
                    { id: 'twitter', name: 'Twitter', color: 'sky' },
                    { id: 'linkedin', name: 'LinkedIn', color: 'blue' },
                    { id: 'facebook', name: 'Facebook', color: 'blue' }
                  ].map((platform) => (
                    <label key={platform.id} className="flex items-center space-x-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedPlatforms.includes(platform.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedPlatforms([...selectedPlatforms, platform.id]);
                          } else {
                            setSelectedPlatforms(selectedPlatforms.filter(p => p !== platform.id));
                          }
                        }}
                        className="w-4 h-4 text-emerald-600"
                      />
                      <span className="text-sm text-gray-700">{platform.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Caption */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Caption (Optional)
                </label>
                <textarea
                  value={shareCaption}
                  onChange={(e) => setShareCaption(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="Add a caption to your receipt share..."
                />
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end space-x-3">
                <button
                  onClick={() => setShowShareModal(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={shareReceipt}
                  disabled={selectedPlatforms.length === 0}
                  className="px-6 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Share Receipt
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExpenseReceipts;
