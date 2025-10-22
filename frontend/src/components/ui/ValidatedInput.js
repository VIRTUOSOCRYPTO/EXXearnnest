import React, { useState, useEffect } from 'react';
import { CheckCircleIcon, XCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/solid';

/**
 * Validated Input Component
 * Real-time validation with visual feedback
 */
const ValidatedInput = ({
  label,
  name,
  type = 'text',
  value,
  onChange,
  validator,
  placeholder = '',
  required = false,
  disabled = false,
  helperText = '',
  showValidation = true,
  validateOnChange = true,
  validateOnBlur = true,
  className = ''
}) => {
  const [errors, setErrors] = useState([]);
  const [touched, setTouched] = useState(false);
  const [validationState, setValidationState] = useState('idle'); // idle, valid, invalid

  useEffect(() => {
    if (validateOnChange && touched && value) {
      validateField();
    }
  }, [value, touched, validateOnChange]);

  const validateField = () => {
    if (!validator) {
      setValidationState('idle');
      return;
    }

    const result = validator(value);
    
    if (result.valid) {
      setErrors([]);
      setValidationState('valid');
    } else {
      setErrors(result.errors || []);
      setValidationState('invalid');
    }
  };

  const handleChange = (e) => {
    const newValue = e.target.value;
    onChange(e);
    
    if (!touched) {
      setTouched(true);
    }
  };

  const handleBlur = () => {
    setTouched(true);
    if (validateOnBlur) {
      validateField();
    }
  };

  const getInputBorderClass = () => {
    if (!showValidation || !touched) {
      return 'border-gray-300 focus:border-purple-500 focus:ring-purple-500';
    }
    
    if (validationState === 'valid') {
      return 'border-green-500 focus:border-green-500 focus:ring-green-500';
    }
    
    if (validationState === 'invalid') {
      return 'border-red-500 focus:border-red-500 focus:ring-red-500';
    }
    
    return 'border-gray-300 focus:border-purple-500 focus:ring-purple-500';
  };

  const getValidationIcon = () => {
    if (!showValidation || !touched || validationState === 'idle') {
      return null;
    }
    
    if (validationState === 'valid') {
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
    }
    
    if (validationState === 'invalid') {
      return <XCircleIcon className="h-5 w-5 text-red-500" />;
    }
    
    return null;
  };

  return (
    <div className={`mb-4 ${className}`}>
      {/* Label */}
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      {/* Input with Icon */}
      <div className="relative">
        <input
          type={type}
          name={name}
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          className={`
            w-full px-3 py-2 border rounded-lg
            focus:outline-none focus:ring-2
            disabled:bg-gray-100 disabled:cursor-not-allowed
            transition duration-150 ease-in-out
            ${getInputBorderClass()}
            ${showValidation && touched && validationState !== 'idle' ? 'pr-10' : ''}
          `}
        />
        
        {/* Validation Icon */}
        {getValidationIcon() && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            {getValidationIcon()}
          </div>
        )}
      </div>
      
      {/* Helper Text */}
      {helperText && !errors.length && (
        <p className="mt-1 text-sm text-gray-500">{helperText}</p>
      )}
      
      {/* Error Messages */}
      {touched && errors.length > 0 && (
        <div className="mt-1 space-y-1">
          {errors.map((error, index) => (
            <p key={index} className="text-sm text-red-600 flex items-center gap-1">
              <ExclamationCircleIcon className="h-4 w-4" />
              {error}
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Validated Textarea Component
 */
export const ValidatedTextarea = ({
  label,
  name,
  value,
  onChange,
  validator,
  placeholder = '',
  required = false,
  disabled = false,
  rows = 4,
  maxLength,
  helperText = '',
  showValidation = true,
  className = ''
}) => {
  const [errors, setErrors] = useState([]);
  const [touched, setTouched] = useState(false);
  const [validationState, setValidationState] = useState('idle');

  const validateField = () => {
    if (!validator) return;

    const result = validator(value);
    
    if (result.valid) {
      setErrors([]);
      setValidationState('valid');
    } else {
      setErrors(result.errors || []);
      setValidationState('invalid');
    }
  };

  const handleBlur = () => {
    setTouched(true);
    validateField();
  };

  const getBorderClass = () => {
    if (!showValidation || !touched) {
      return 'border-gray-300 focus:border-purple-500 focus:ring-purple-500';
    }
    
    if (validationState === 'valid') {
      return 'border-green-500 focus:border-green-500 focus:ring-green-500';
    }
    
    if (validationState === 'invalid') {
      return 'border-red-500 focus:border-red-500 focus:ring-red-500';
    }
    
    return 'border-gray-300 focus:border-purple-500 focus:ring-purple-500';
  };

  return (
    <div className={`mb-4 ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <textarea
        name={name}
        value={value}
        onChange={onChange}
        onBlur={handleBlur}
        placeholder={placeholder}
        disabled={disabled}
        rows={rows}
        maxLength={maxLength}
        className={`
          w-full px-3 py-2 border rounded-lg
          focus:outline-none focus:ring-2
          disabled:bg-gray-100 disabled:cursor-not-allowed
          transition duration-150 ease-in-out
          ${getBorderClass()}
        `}
      />
      
      {/* Character Count */}
      {maxLength && (
        <div className="mt-1 flex justify-between text-sm text-gray-500">
          <span>{helperText}</span>
          <span>{value.length}/{maxLength}</span>
        </div>
      )}
      
      {/* Error Messages */}
      {touched && errors.length > 0 && (
        <div className="mt-1 space-y-1">
          {errors.map((error, index) => (
            <p key={index} className="text-sm text-red-600 flex items-center gap-1">
              <ExclamationCircleIcon className="h-4 w-4" />
              {error}
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Password Input with Strength Meter
 */
export const PasswordInput = ({
  label = 'Password',
  name,
  value,
  onChange,
  required = false,
  showStrengthMeter = true,
  className = ''
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const [strength, setStrength] = useState('weak');
  const [errors, setErrors] = useState([]);

  useEffect(() => {
    if (value) {
      const calculateStrength = () => {
        let score = 0;
        if (value.length >= 8) score += 20;
        if (value.length >= 12) score += 20;
        if (/[a-z]/.test(value)) score += 15;
        if (/[A-Z]/.test(value)) score += 15;
        if (/[0-9]/.test(value)) score += 15;
        if (/[!@#$%^&*(),.?":{}|<>]/.test(value)) score += 15;
        
        if (score <= 40) setStrength('weak');
        else if (score <= 70) setStrength('medium');
        else setStrength('strong');
      };
      
      calculateStrength();
    }
  }, [value]);

  const getStrengthColor = () => {
    switch (strength) {
      case 'weak': return 'bg-red-500';
      case 'medium': return 'bg-yellow-500';
      case 'strong': return 'bg-green-500';
      default: return 'bg-gray-300';
    }
  };

  const getStrengthWidth = () => {
    switch (strength) {
      case 'weak': return 'w-1/3';
      case 'medium': return 'w-2/3';
      case 'strong': return 'w-full';
      default: return 'w-0';
    }
  };

  return (
    <div className={`mb-4 ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        <input
          type={showPassword ? 'text' : 'password'}
          name={name}
          value={value}
          onChange={onChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent pr-10"
        />
        
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
        >
          {showPassword ? '👁️' : '👁️‍🗨️'}
        </button>
      </div>
      
      {/* Strength Meter */}
      {showStrengthMeter && value && (
        <div className="mt-2">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-600">Password Strength:</span>
            <span className={`font-semibold ${
              strength === 'weak' ? 'text-red-600' :
              strength === 'medium' ? 'text-yellow-600' :
              'text-green-600'
            }`}>
              {strength.charAt(0).toUpperCase() + strength.slice(1)}
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className={`h-full ${getStrengthColor()} ${getStrengthWidth()} transition-all duration-300`}></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ValidatedInput;
