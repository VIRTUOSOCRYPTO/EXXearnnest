/**
 * Mobile Optimizations Component
 * Provides mobile-specific UI enhancements and native-like experience
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion, PanGestureHandler } from 'framer-motion';
import pwaService from '../services/PWAService';

// Mobile-optimized form input component
export const MobileInput = ({ 
  type = 'text', 
  placeholder, 
  value, 
  onChange, 
  onFocus,
  className = '',
  label,
  error,
  leftIcon,
  rightIcon,
  ...props 
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef(null);

  const handleFocus = (e) => {
    setIsFocused(true);
    if (onFocus) onFocus(e);
    
    // Haptic feedback
    pwaService.hapticFeedback?.('light');
    
    // Scroll input into view with padding
    setTimeout(() => {
      inputRef.current?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center' 
      });
    }, 100);
  };

  const handleBlur = () => {
    setIsFocused(false);
  };

  return (
    <motion.div 
      className={`mobile-input-wrapper ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {label && (
        <label className={`mobile-input-label ${isFocused || value ? 'focused' : ''}`}>
          {label}
        </label>
      )}
      
      <div className={`mobile-input-container ${isFocused ? 'focused' : ''} ${error ? 'error' : ''}`}>
        {leftIcon && (
          <div className="mobile-input-icon left">
            {leftIcon}
          </div>
        )}
        
        <input
          ref={inputRef}
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          className="mobile-input"
          autoComplete="off"
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck="false"
          {...props}
        />
        
        {rightIcon && (
          <div className="mobile-input-icon right">
            {rightIcon}
          </div>
        )}
      </div>
      
      {error && (
        <motion.div 
          className="mobile-input-error"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
        >
          {error}
        </motion.div>
      )}
    </motion.div>
  );
};

// Mobile-optimized button component
export const MobileButton = ({ 
  children, 
  onClick, 
  variant = 'primary', 
  size = 'medium',
  disabled = false,
  loading = false,
  haptic = 'medium',
  className = '',
  ...props 
}) => {
  const handleClick = (e) => {
    if (disabled || loading) return;
    
    // Haptic feedback
    pwaService.hapticFeedback?.(haptic);
    
    if (onClick) onClick(e);
  };

  return (
    <motion.button
      className={`mobile-button ${variant} ${size} ${className} ${disabled ? 'disabled' : ''}`}
      onClick={handleClick}
      disabled={disabled || loading}
      whileTap={{ scale: 0.95 }}
      whileHover={{ scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 400, damping: 17 }}
      {...props}
    >
      {loading ? (
        <div className="mobile-button-spinner">
          <div className="spinner"></div>
        </div>
      ) : (
        children
      )}
    </motion.button>
  );
};

// Swipeable card component
export const SwipeableCard = ({ 
  children, 
  onSwipeLeft, 
  onSwipeRight, 
  className = '',
  threshold = 100 
}) => {
  const [dragX, setDragX] = useState(0);

  const handleDragEnd = (event, info) => {
    const { offset, velocity } = info;
    
    if (Math.abs(offset.x) > threshold || Math.abs(velocity.x) > 500) {
      if (offset.x > 0 && onSwipeRight) {
        onSwipeRight();
        pwaService.hapticFeedback?.('success');
      } else if (offset.x < 0 && onSwipeLeft) {
        onSwipeLeft();
        pwaService.hapticFeedback?.('success');
      }
    }
    
    setDragX(0);
  };

  return (
    <motion.div
      className={`swipeable-card ${className}`}
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.2}
      onDrag={(event, info) => setDragX(info.offset.x)}
      onDragEnd={handleDragEnd}
      animate={{ x: dragX > threshold ? 20 : dragX < -threshold ? -20 : 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
    >
      {children}
      
      {/* Swipe indicators */}
      {onSwipeRight && (
        <div 
          className={`swipe-indicator right ${dragX > threshold ? 'active' : ''}`}
          style={{ opacity: Math.min(Math.abs(dragX) / threshold, 1) }}
        >
          ✓
        </div>
      )}
      
      {onSwipeLeft && (
        <div 
          className={`swipe-indicator left ${dragX < -threshold ? 'active' : ''}`}
          style={{ opacity: Math.min(Math.abs(dragX) / threshold, 1) }}
        >
          ✗
        </div>
      )}
    </motion.div>
  );
};

// Pull-to-refresh component
export const PullToRefresh = ({ onRefresh, children, threshold = 80 }) => {
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [startY, setStartY] = useState(0);

  const handleTouchStart = (e) => {
    if (window.scrollY === 0) {
      setStartY(e.touches[0].clientY);
    }
  };

  const handleTouchMove = (e) => {
    if (window.scrollY === 0 && startY > 0) {
      const currentY = e.touches[0].clientY;
      const distance = Math.max(0, currentY - startY) * 0.5; // Reduce sensitivity
      
      setPullDistance(Math.min(distance, threshold * 1.5));
      
      if (distance > threshold) {
        pwaService.hapticFeedback?.('light');
      }
    }
  };

  const handleTouchEnd = async () => {
    if (pullDistance > threshold && !isRefreshing) {
      setIsRefreshing(true);
      pwaService.hapticFeedback?.('success');
      
      try {
        await onRefresh();
      } finally {
        setIsRefreshing(false);
        setPullDistance(0);
      }
    } else {
      setPullDistance(0);
    }
    
    setStartY(0);
  };

  return (
    <div 
      className="pull-to-refresh-container"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <motion.div
        className="pull-to-refresh-indicator"
        animate={{ 
          height: pullDistance,
          opacity: pullDistance > 0 ? 1 : 0 
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      >
        <div className={`refresh-icon ${isRefreshing ? 'spinning' : ''} ${pullDistance > threshold ? 'ready' : ''}`}>
          {isRefreshing ? '↻' : '↓'}
        </div>
      </motion.div>
      
      <motion.div
        animate={{ y: pullDistance }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      >
        {children}
      </motion.div>
    </div>
  );
};

// Mobile-optimized modal
export const MobileModal = ({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  fullScreen = false,
  className = '' 
}) => {
  const modalRef = useRef(null);

  useEffect(() => {
    const handleBackButton = (e) => {
      if (isOpen) {
        e.preventDefault();
        onClose();
      }
    };

    if (isOpen) {
      window.addEventListener('popstate', handleBackButton);
      // Prevent body scroll
      document.body.style.overflow = 'hidden';
    }

    return () => {
      window.removeEventListener('popstate', handleBackButton);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <motion.div
      className="mobile-modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        ref={modalRef}
        className={`mobile-modal ${fullScreen ? 'full-screen' : ''} ${className}`}
        initial={{ y: '100%' }}
        animate={{ y: 0 }}
        exit={{ y: '100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mobile-modal-header">
          <h3 className="mobile-modal-title">{title}</h3>
          <button 
            className="mobile-modal-close"
            onClick={onClose}
            onTouchStart={() => pwaService.hapticFeedback?.('light')}
          >
            ×
          </button>
        </div>
        
        <div className="mobile-modal-content">
          {children}
        </div>
      </motion.div>
    </motion.div>
  );
};

// Touch-friendly number input
export const MobileNumberInput = ({ 
  value, 
  onChange, 
  min = 0, 
  max = Infinity,
  step = 1,
  prefix = '',
  suffix = '',
  className = '' 
}) => {
  const [inputValue, setInputValue] = useState(value?.toString() || '');

  const handleIncrement = () => {
    const newValue = Math.min(parseFloat(value || 0) + step, max);
    onChange(newValue);
    pwaService.hapticFeedback?.('light');
  };

  const handleDecrement = () => {
    const newValue = Math.max(parseFloat(value || 0) - step, min);
    onChange(newValue);
    pwaService.hapticFeedback?.('light');
  };

  const handleInputChange = (e) => {
    const val = e.target.value;
    setInputValue(val);
    
    const numValue = parseFloat(val);
    if (!isNaN(numValue) && numValue >= min && numValue <= max) {
      onChange(numValue);
    }
  };

  useEffect(() => {
    setInputValue(value?.toString() || '');
  }, [value]);

  return (
    <div className={`mobile-number-input ${className}`}>
      <button 
        className="number-button decrement"
        onClick={handleDecrement}
        disabled={value <= min}
        type="button"
      >
        −
      </button>
      
      <div className="number-input-wrapper">
        {prefix && <span className="input-prefix">{prefix}</span>}
        <input
          type="number"
          value={inputValue}
          onChange={handleInputChange}
          min={min}
          max={max}
          step={step}
          className="number-input"
        />
        {suffix && <span className="input-suffix">{suffix}</span>}
      </div>
      
      <button 
        className="number-button increment"
        onClick={handleIncrement}
        disabled={value >= max}
        type="button"
      >
        +
      </button>
    </div>
  );
};

// Mobile-optimized loading spinner
export const MobileSpinner = ({ size = 'medium', color = 'primary' }) => {
  return (
    <div className={`mobile-spinner ${size} ${color}`}>
      <div className="spinner-ring"></div>
    </div>
  );
};

// Connection status indicator
export const ConnectionStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showStatus, setShowStatus] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setShowStatus(true);
      setTimeout(() => setShowStatus(false), 3000);
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowStatus(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!showStatus) return null;

  return (
    <motion.div
      className={`connection-status ${isOnline ? 'online' : 'offline'}`}
      initial={{ opacity: 0, y: -50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -50 }}
    >
      <span className="status-icon">{isOnline ? '🟢' : '🔴'}</span>
      <span className="status-text">
        {isOnline ? 'Back online' : 'You\'re offline'}
      </span>
    </motion.div>
  );
};

// PWA install button
export const PWAInstallButton = () => {
  const [showInstall, setShowInstall] = useState(false);

  useEffect(() => {
    const handleBeforeInstallPrompt = () => {
      setShowInstall(true);
    };

    const handleAppInstalled = () => {
      setShowInstall(false);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  if (!showInstall || pwaService.isStandalone()) return null;

  return (
    <motion.button
      id="pwa-install-btn"
      className="pwa-install-button"
      onClick={() => pwaService.installPWA()}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      whileTap={{ scale: 0.95 }}
    >
      <span className="install-icon">📱</span>
      <span className="install-text">Install App</span>
    </motion.button>
  );
};

export default {
  MobileInput,
  MobileButton,
  SwipeableCard,
  PullToRefresh,
  MobileModal,
  MobileNumberInput,
  MobileSpinner,
  ConnectionStatus,
  PWAInstallButton
};
