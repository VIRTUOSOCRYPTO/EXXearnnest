import { useState, useEffect, useCallback } from 'react';
import apiClient from '../utils/apiClient';

/**
 * Custom hook for data fetching with loading, error states, and caching
 * @param {string} url - API endpoint
 * @param {object} options - Fetch options
 * @returns {object} { data, loading, error, refetch }
 */
const useFetch = (url, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const {
    skip = false,
    dependencies = [],
    cacheTime = 0,
    onSuccess,
    onError,
  } = options;

  const fetchData = useCallback(async () => {
    if (skip) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.get(url);
      setData(response.data);
      
      if (onSuccess) {
        onSuccess(response.data);
      }
    } catch (err) {
      const errorMessage = err.response?.data?.message || err.message || 'An error occurred';
      setError(errorMessage);
      
      if (onError) {
        onError(err);
      }
    } finally {
      setLoading(false);
    }
  }, [url, skip, onSuccess, onError]);

  useEffect(() => {
    fetchData();
  }, [fetchData, ...dependencies]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
};

export default useFetch;
