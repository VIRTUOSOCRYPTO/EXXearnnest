import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Users } from 'lucide-react';

const GroupExpenses = () => {
  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <Users className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-800">Group Expenses</h1>
        </div>
        <p className="text-gray-600 text-lg">
          Manage shared expenses with friends and groups.
        </p>
      </div>

      <div className="text-center py-12">
        <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-600 mb-2">Coming Soon</h3>
        <p className="text-gray-500">Group expense management features will be available soon!</p>
      </div>
    </div>
  );
};

export default GroupExpenses;
