import React from 'react';

/**
 * Skeleton Loader Component
 * Provides animated loading placeholders for async content
 */
export const Skeleton = ({ className = '', variant = 'default', ...props }) => {
  const variants = {
    default: 'bg-gray-200',
    card: 'bg-white shadow-sm',
    text: 'bg-gray-200 h-4 rounded',
    title: 'bg-gray-300 h-6 rounded',
    avatar: 'bg-gray-300 rounded-full',
    button: 'bg-gray-300 h-10 rounded-lg'
  };

  return (
    <div
      className={`animate-pulse ${variants[variant]} ${className}`}
      {...props}
    />
  );
};

/**
 * Table Skeleton Loader
 */
export const TableSkeleton = ({ rows = 5, columns = 4 }) => {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={`header-${i}`} variant="title" className="h-5" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={`row-${rowIndex}`} className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={`cell-${rowIndex}-${colIndex}`} variant="text" />
          ))}
        </div>
      ))}
    </div>
  );
};

/**
 * Card Skeleton Loader
 */
export const CardSkeleton = ({ showImage = false }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
      {showImage && <Skeleton className="h-48 w-full rounded-lg" />}
      <Skeleton variant="title" className="w-3/4" />
      <Skeleton variant="text" className="w-full" />
      <Skeleton variant="text" className="w-5/6" />
      <div className="flex gap-2 mt-4">
        <Skeleton variant="button" className="w-24" />
        <Skeleton variant="button" className="w-24" />
      </div>
    </div>
  );
};

/**
 * List Item Skeleton Loader
 */
export const ListItemSkeleton = () => {
  return (
    <div className="flex items-center space-x-4 p-4 bg-white rounded-lg shadow-sm">
      <Skeleton variant="avatar" className="w-12 h-12" />
      <div className="flex-1 space-y-2">
        <Skeleton variant="text" className="w-3/4" />
        <Skeleton variant="text" className="w-1/2" />
      </div>
      <Skeleton variant="button" className="w-20" />
    </div>
  );
};

/**
 * Dashboard Stats Skeleton
 */
export const DashboardStatsSkeleton = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="bg-white rounded-lg shadow-md p-6">
          <Skeleton variant="text" className="w-1/2 mb-2" />
          <Skeleton variant="title" className="w-3/4 mb-4" />
          <Skeleton variant="text" className="w-full" />
        </div>
      ))}
    </div>
  );
};

/**
 * Form Skeleton Loader
 */
export const FormSkeleton = ({ fields = 5 }) => {
  return (
    <div className="space-y-4">
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton variant="text" className="w-1/4 h-4" />
          <Skeleton className="w-full h-10 rounded-lg" />
        </div>
      ))}
      <Skeleton variant="button" className="w-full mt-6" />
    </div>
  );
};

/**
 * Profile Skeleton Loader
 */
export const ProfileSkeleton = () => {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center space-x-6">
          <Skeleton variant="avatar" className="w-24 h-24" />
          <div className="flex-1 space-y-3">
            <Skeleton variant="title" className="w-1/2" />
            <Skeleton variant="text" className="w-3/4" />
            <Skeleton variant="text" className="w-2/3" />
          </div>
        </div>
      </div>
      {/* Content */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  );
};

/**
 * Notification Skeleton Loader
 */
export const NotificationSkeleton = ({ count = 3 }) => {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-white rounded-lg shadow-sm p-4 flex items-start space-x-4">
          <Skeleton variant="avatar" className="w-10 h-10" />
          <div className="flex-1 space-y-2">
            <Skeleton variant="text" className="w-full" />
            <Skeleton variant="text" className="w-3/4" />
            <Skeleton variant="text" className="w-1/4 h-3" />
          </div>
        </div>
      ))}
    </div>
  );
};
