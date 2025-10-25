/**
 * Form Validation Utilities
 * Provides real-time validation for common form fields
 */

// Email validation
export const validateEmail = (email) => {
  const errors = [];
  
  if (!email) {
    return { valid: false, errors: ['Email is required'] };
  }
  
  if (!email.includes('@')) {
    errors.push('Email must contain @');
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    errors.push('Invalid email format');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
};

// Password validation
export const validatePassword = (password) => {
  const errors = [];
  
  if (!password) {
    return { valid: false, errors: ['Password is required'] };
  }
  
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters');
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  return {
    valid: errors.length === 0,
    errors,
    strength: calculatePasswordStrength(password)
  };
};

// Calculate password strength
const calculatePasswordStrength = (password) => {
  let strength = 0;
  
  if (password.length >= 8) strength += 20;
  if (password.length >= 12) strength += 20;
  if (/[a-z]/.test(password)) strength += 15;
  if (/[A-Z]/.test(password)) strength += 15;
  if (/[0-9]/.test(password)) strength += 15;
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength += 15;
  
  if (strength <= 40) return 'weak';
  if (strength <= 70) return 'medium';
  return 'strong';
};

// Phone number validation
export const validatePhone = (phone) => {
  const errors = [];
  
  if (!phone) {
    return { valid: false, errors: ['Phone number is required'] };
  }
  
  // Remove all non-digit characters
  const digitsOnly = phone.replace(/\D/g, '');
  
  if (digitsOnly.length !== 10) {
    errors.push('Phone number must be exactly 10 digits');
  }
  
  // Indian phone number validation (must start with 6-9)
  const indianPhoneRegex = /^[6-9]\d{9}$/;
  if (digitsOnly.length === 10 && !indianPhoneRegex.test(digitsOnly)) {
    errors.push('Invalid Indian phone number (must start with 6, 7, 8, or 9)');
  }
  
  return {
    valid: errors.length === 0,
    errors,
    formatted: formatPhone(digitsOnly)
  };
};

// Format phone number
const formatPhone = (phone) => {
  const digitsOnly = phone.replace(/\D/g, '');
  
  if (digitsOnly.length === 10) {
    return `+91 ${digitsOnly.slice(0, 5)} ${digitsOnly.slice(5)}`;
  }
  
  return digitsOnly;
};

// Amount validation
export const validateAmount = (amount, options = {}) => {
  const { min = 0, max = Infinity, required = true } = options;
  const errors = [];
  
  if (!amount && required) {
    return { valid: false, errors: ['Amount is required'] };
  }
  
  const numericAmount = parseFloat(amount);
  
  if (isNaN(numericAmount)) {
    errors.push('Amount must be a valid number');
  }
  
  if (numericAmount < min) {
    errors.push(`Amount must be at least ₹${min}`);
  }
  
  if (numericAmount > max) {
    errors.push(`Amount cannot exceed ₹${max}`);
  }
  
  if (numericAmount < 0) {
    errors.push('Amount cannot be negative');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
};

// USN validation (University Serial Number)
export const validateUSN = (usn) => {
  const errors = [];
  
  if (!usn) {
    return { valid: false, errors: ['USN is required'] };
  }
  
  // Basic USN format: 1XX19CS001
  const usnRegex = /^[1-4][A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{3}$/;
  
  if (!usnRegex.test(usn.toUpperCase())) {
    errors.push('Invalid USN format (e.g., 1XX19CS001)');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
};

// Name validation
export const validateName = (name, options = {}) => {
  const { minLength = 2, maxLength = 50 } = options;
  const errors = [];
  
  if (!name) {
    return { valid: false, errors: ['Name is required'] };
  }
  
  if (name.trim().length < minLength) {
    errors.push(`Name must be at least ${minLength} characters`);
  }
  
  if (name.length > maxLength) {
    errors.push(`Name cannot exceed ${maxLength} characters`);
  }
  
  if (!/^[a-zA-Z\s.'-]+$/.test(name)) {
    errors.push('Name can only contain letters, spaces, and basic punctuation');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
};

// Required field validation
export const validateRequired = (value, fieldName = 'Field') => {
  if (!value || (typeof value === 'string' && !value.trim())) {
    return {
      valid: false,
      errors: [`${fieldName} is required`]
    };
  }
  
  return {
    valid: true,
    errors: []
  };
};

// Generic form validation
export const validateForm = (formData, validationRules) => {
  const errors = {};
  let isValid = true;
  
  Object.keys(validationRules).forEach(field => {
    const rules = validationRules[field];
    const value = formData[field];
    const fieldErrors = [];
    
    // Required validation
    if (rules.required && !value) {
      fieldErrors.push(`${rules.label || field} is required`);
      isValid = false;
    }
    
    // Custom validators
    if (value && rules.validators) {
      rules.validators.forEach(validator => {
        const result = validator(value);
        if (!result.valid) {
          fieldErrors.push(...result.errors);
          isValid = false;
        }
      });
    }
    
    if (fieldErrors.length > 0) {
      errors[field] = fieldErrors;
    }
  });
  
  return {
    valid: isValid,
    errors
  };
};

// Export all validators
export default {
  validateEmail,
  validatePassword,
  validatePhone,
  validateAmount,
  validateUSN,
  validateName,
  validateRequired,
  validateForm
};
