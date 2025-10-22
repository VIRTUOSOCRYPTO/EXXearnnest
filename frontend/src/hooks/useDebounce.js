import { useState, useEffect } from 'react';

/**
 * Custom hook for debouncing values
 * Delays updating the value until after a specified delay
 * 
 * @param {any} value - The value to debounce
 * @param {number} delay - Delay in milliseconds (default: 500ms)
 * @returns {any} - The debounced value
 */
export function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    // Set up a timeout to update the debounced value
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Clean up the timeout if value changes before delay expires
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Custom hook for debounced search with loading state
 * 
 * @param {function} searchFunction - Async function to execute search
 * @param {number} delay - Debounce delay in milliseconds
 * @returns {object} - { searchTerm, setSearchTerm, isSearching, results, error }
 */
export function useDebouncedSearch(searchFunction, delay = 500) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  
  const debouncedSearchTerm = useDebounce(searchTerm, delay);

  useEffect(() => {
    const performSearch = async () => {
      if (!debouncedSearchTerm.trim()) {
        setResults([]);
        setIsSearching(false);
        return;
      }

      setIsSearching(true);
      setError(null);
      
      try {
        const searchResults = await searchFunction(debouncedSearchTerm);
        setResults(searchResults);
      } catch (err) {
        setError(err.message || 'Search failed');
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    };

    performSearch();
  }, [debouncedSearchTerm, searchFunction]);

  return {
    searchTerm,
    setSearchTerm,
    isSearching,
    results,
    error,
    hasSearchTerm: searchTerm.trim().length > 0
  };
}

export default useDebounce;
