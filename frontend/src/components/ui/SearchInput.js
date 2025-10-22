import React from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';

/**
 * Reusable Search Input Component
 * Features: Search icon, clear button, loading state, customizable placeholder
 */
const SearchInput = ({
  value,
  onChange,
  onClear,
  placeholder = 'Search...',
  isSearching = false,
  className = '',
  disabled = false,
  autoFocus = false
}) => {
  const handleChange = (e) => {
    onChange(e.target.value);
  };

  const handleClear = () => {
    if (onClear) {
      onClear();
    } else {
      onChange('');
    }
  };

  return (
    <div className={`relative ${className}`}>
      {/* Search Icon */}
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <MagnifyingGlassIcon 
          className={`h-5 w-5 ${isSearching ? 'text-purple-600 animate-pulse' : 'text-gray-400'}`}
        />
      </div>

      {/* Input Field */}
      <input
        type="text"
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        disabled={disabled}
        autoFocus={autoFocus}
        className={`
          w-full pl-10 pr-10 py-2 
          border border-gray-300 rounded-lg
          focus:ring-2 focus:ring-purple-500 focus:border-transparent
          disabled:bg-gray-100 disabled:cursor-not-allowed
          transition duration-150 ease-in-out
        `}
      />

      {/* Clear Button or Loading Spinner */}
      {value && (
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
          {isSearching ? (
            <div className="animate-spin h-5 w-5 border-2 border-purple-600 border-t-transparent rounded-full"></div>
          ) : (
            <button
              onClick={handleClear}
              className="text-gray-400 hover:text-gray-600 focus:outline-none transition"
              type="button"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Advanced Search with Filters Component
 */
export const AdvancedSearchInput = ({
  value,
  onChange,
  onClear,
  filters = [],
  selectedFilter,
  onFilterChange,
  placeholder = 'Search...',
  isSearching = false,
  className = ''
}) => {
  return (
    <div className={`flex gap-2 ${className}`}>
      <SearchInput
        value={value}
        onChange={onChange}
        onClear={onClear}
        placeholder={placeholder}
        isSearching={isSearching}
        className="flex-1"
      />
      
      {filters.length > 0 && (
        <select
          value={selectedFilter}
          onChange={(e) => onFilterChange(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white"
        >
          {filters.map((filter) => (
            <option key={filter.value} value={filter.value}>
              {filter.label}
            </option>
          ))}
        </select>
      )}
    </div>
  );
};

/**
 * Search with Results Count
 */
export const SearchWithCount = ({
  value,
  onChange,
  onClear,
  placeholder = 'Search...',
  isSearching = false,
  resultCount = 0,
  totalCount = 0,
  className = ''
}) => {
  return (
    <div className={className}>
      <SearchInput
        value={value}
        onChange={onChange}
        onClear={onClear}
        placeholder={placeholder}
        isSearching={isSearching}
      />
      {value && (
        <div className="mt-2 text-sm text-gray-600">
          {isSearching ? (
            'Searching...'
          ) : (
            `Found ${resultCount} of ${totalCount} results`
          )}
        </div>
      )}
    </div>
  );
};

export default SearchInput;
