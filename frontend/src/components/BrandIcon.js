import React from 'react';

const BrandIcon = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'w-6 h-6 text-sm',
    md: 'w-8 h-8 text-lg',
    lg: 'w-12 h-12 text-xl',
    xl: 'w-16 h-16 text-2xl'
  };

  return (
    <div className={`bg-gradient-to-br from-emerald-500 via-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg ${sizeClasses[size]} ${className}`}>
      <span className="text-white font-bold">₹</span>
      <div className="absolute -inset-1 bg-gradient-to-br from-emerald-400 to-green-400 rounded-xl opacity-20 blur -z-10"></div>
    </div>
  );
};

export default BrandIcon;
