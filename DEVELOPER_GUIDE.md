# EarnAura Developer Guide - Code Quality & Architecture

## 🎯 Quick Start

This guide helps you leverage the new architecture improvements in the EarnAura application.

---

## 📁 New Architecture Overview

```
/app/frontend/src/
├── stores/              # Zustand state management
│   ├── authStore.js
│   ├── dashboardStore.js
│   └── notificationStore.js
├── hooks/               # Custom React hooks
│   ├── useFetch.js     # NEW
│   ├── usePagination.js # NEW
│   ├── useWebSocket.js
│   ├── useDebounce.js
│   └── ...
├── utils/
│   ├── apiClient.js    # NEW - Centralized API client
│   ├── axiosConfig.js  # Legacy - being phased out
│   └── formValidation.js
└── components/
    └── ...
```

---

## 🏪 State Management with Zustand

### Why Zustand?
- Simpler than Redux
- No boilerplate
- Built-in persistence
- Excellent TypeScript support
- Small bundle size (~1KB)

### Using Auth Store

```javascript
import useAuthStore from '../stores/authStore';

function MyComponent() {
  // Get state and actions
  const { user, isAuthenticated, setUser, logout } = useAuthStore();
  
  // Use in your component
  if (!isAuthenticated) {
    return <LoginPrompt />;
  }
  
  return (
    <div>
      <h1>Welcome, {user.full_name}</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### Using Dashboard Store

```javascript
import useDashboardStore from '../stores/dashboardStore';

function Dashboard() {
  const { 
    summary,
    recentTransactions,
    leaderboard,
    loading,
    refreshing,
    fetchDashboard 
  } = useDashboardStore();
  
  useEffect(() => {
    // Fetch dashboard data (auto-cached for 30s)
    fetchDashboard();
  }, [fetchDashboard]);
  
  // Manual refresh
  const handleRefresh = () => {
    fetchDashboard(true); // Force refresh
  };
  
  if (loading) return <Loader />;
  
  return (
    <div>
      <button onClick={handleRefresh} disabled={refreshing}>
        {refreshing ? 'Refreshing...' : 'Refresh'}
      </button>
      <SummaryCard summary={summary} />
      <TransactionList transactions={recentTransactions} />
      <Leaderboard data={leaderboard} />
    </div>
  );
}
```

### Using Notification Store

```javascript
import useNotificationStore from '../stores/notificationStore';

function NotificationBell() {
  const { 
    notifications, 
    unreadCount, 
    markAsRead,
    markAllAsRead 
  } = useNotificationStore();
  
  return (
    <div>
      <Badge count={unreadCount} />
      <NotificationList 
        items={notifications}
        onMarkRead={markAsRead}
      />
      <button onClick={markAllAsRead}>
        Mark All Read
      </button>
    </div>
  );
}
```

---

## 🌐 API Client

### Benefits
- Automatic token injection
- Automatic token refresh
- Centralized error handling
- Type-safe endpoints
- No repetitive code

### Basic Usage

```javascript
import { api } from '../utils/apiClient';

async function MyComponent() {
  try {
    // GET request
    const transactions = await api.transactions.getAll({ limit: 10 });
    
    // POST request
    const newTransaction = await api.transactions.create({
      type: 'income',
      amount: 5000,
      description: 'Freelance work'
    });
    
    // PUT request
    const updated = await api.transactions.update(id, { amount: 6000 });
    
    // DELETE request
    await api.transactions.delete(id);
    
  } catch (error) {
    console.error('API Error:', error);
    // Error already handled by interceptor
  }
}
```

### Available API Endpoints

```javascript
// Auth
api.auth.login(credentials)
api.auth.register(userData)
api.auth.refreshToken()
api.auth.logout()

// Transactions
api.transactions.getAll(params)
api.transactions.getSummary()
api.transactions.create(data)
api.transactions.update(id, data)
api.transactions.delete(id)

// Analytics
api.analytics.getLeaderboard(params)
api.analytics.getInsights()

// Gamification
api.gamification.getProfile()
api.gamification.claimReward(rewardId)

// Engagement
api.engagement.getDailyTip()
api.engagement.getCountdownAlerts()
api.engagement.getLimitedOffers()
```

### Adding New Endpoints

Edit `/app/frontend/src/utils/apiClient.js`:

```javascript
export const api = {
  // ... existing endpoints
  
  // Add your new section
  goals: {
    getAll: () => apiClient.get('/goals'),
    create: (data) => apiClient.post('/goals', data),
    update: (id, data) => apiClient.put(`/goals/${id}`, data),
    delete: (id) => apiClient.delete(`/goals/${id}`),
  },
};
```

---

## 🎣 Custom Hooks

### useFetch - Data Fetching Made Simple

```javascript
import useFetch from '../hooks/useFetch';

function TransactionList() {
  const { data, loading, error, refetch } = useFetch('/transactions', {
    dependencies: [], // Refetch when these change
    onSuccess: (data) => console.log('Loaded:', data),
    onError: (error) => console.error('Error:', error),
  });
  
  if (loading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;
  
  return (
    <>
      <List items={data} />
      <button onClick={refetch}>Refresh</button>
    </>
  );
}
```

### usePagination - Easy Pagination

```javascript
import usePagination from '../hooks/usePagination';

function PaginatedList({ items }) {
  const {
    currentItems,    // Current page items
    currentPage,     // Current page number
    totalPages,      // Total pages
    goToPage,        // Jump to specific page
    nextPage,        // Go to next page
    prevPage,        // Go to previous page
    hasNext,         // Can go forward?
    hasPrev,         // Can go back?
    reset,           // Reset to page 1
  } = usePagination(items, 20); // 20 items per page
  
  return (
    <>
      <List items={currentItems} />
      
      <div className="pagination">
        <button onClick={prevPage} disabled={!hasPrev}>
          Previous
        </button>
        
        <span>Page {currentPage} of {totalPages}</span>
        
        <button onClick={nextPage} disabled={!hasNext}>
          Next
        </button>
      </div>
    </>
  );
}
```

---

## 🌍 Environment Configuration

### Development
File: `.env.development`
```bash
REACT_APP_ENV=development
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_WS_URL=ws://localhost:8001
REACT_APP_DEBUG=true
```

### Production
File: `.env.production`
```bash
REACT_APP_ENV=production
REACT_APP_BACKEND_URL=https://api.earnaura.com
REACT_APP_WS_URL=wss://api.earnaura.com
REACT_APP_DEBUG=false
```

### Usage in Code

```javascript
const isDevelopment = process.env.REACT_APP_ENV === 'development';
const backendURL = process.env.REACT_APP_BACKEND_URL;
const debug = process.env.REACT_APP_DEBUG === 'true';

if (debug) {
  console.log('Debug mode enabled');
}
```

---

## 📱 Mobile Responsiveness

### Tailwind Breakpoints
```javascript
// Mobile first approach
<div className="
  w-full          // Mobile: full width
  sm:w-1/2        // Small screens: half width
  md:w-1/3        // Medium screens: third width
  lg:w-1/4        // Large screens: quarter width
  xl:w-1/5        // Extra large: fifth width
">
```

### Common Patterns

```javascript
// Responsive Grid
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

// Responsive Padding
<div className="px-3 sm:px-4 lg:px-6 py-4 sm:py-8">

// Hide on Mobile
<div className="hidden lg:block">

// Show only on Mobile
<div className="block lg:hidden">

// Responsive Text
<h1 className="text-xl sm:text-2xl lg:text-3xl">

// Responsive Flex Direction
<div className="flex flex-col lg:flex-row">
```

---

## 🎨 Component Best Practices

### Keep Components Small
```javascript
// ❌ Bad: 1500 line component
function SuperAdminInterface() {
  // 1500 lines of code...
}

// ✅ Good: Break into smaller components
function SuperAdminInterface() {
  return (
    <Tabs>
      <DashboardTab />        // ~200 lines
      <RequestsTab />         // ~250 lines
      <AdminsTab />           // ~200 lines
      <AuditLogsTab />        // ~300 lines
    </Tabs>
  );
}
```

### Extract Business Logic

```javascript
// ❌ Bad: Logic in component
function Dashboard() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    fetch('/api/dashboard')
      .then(res => res.json())
      .then(data => setData(data))
      .catch(error => console.error(error));
  }, []);
  
  // ... more logic
}

// ✅ Good: Use custom hook
function Dashboard() {
  const { data, loading, error } = useFetch('/dashboard');
  
  if (loading) return <Loader />;
  if (error) return <Error error={error} />;
  
  return <DashboardView data={data} />;
}
```

### Memoization for Performance

```javascript
import { useMemo, useCallback } from 'react';

function ExpensiveComponent({ items, onSelect }) {
  // Memoize expensive calculations
  const total = useMemo(() => {
    return items.reduce((sum, item) => sum + item.price, 0);
  }, [items]);
  
  // Memoize callbacks
  const handleSelect = useCallback((id) => {
    onSelect(id);
  }, [onSelect]);
  
  return <div>Total: {total}</div>;
}

// Memoize component itself
export default React.memo(ExpensiveComponent);
```

---

## 🚀 Performance Optimization

### Lazy Loading
```javascript
import { lazy, Suspense } from 'react';

// Lazy load heavy components
const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <HeavyComponent />
    </Suspense>
  );
}
```

### Code Splitting by Route
```javascript
const Dashboard = lazy(() => import('./Dashboard'));
const Profile = lazy(() => import('./Profile'));
const Settings = lazy(() => import('./Settings'));

<Routes>
  <Route path="/dashboard" element={
    <Suspense fallback={<Loading />}>
      <Dashboard />
    </Suspense>
  } />
</Routes>
```

### Virtualization for Long Lists
```javascript
// For lists with 1000+ items, use virtualization
import { VirtualList } from 'react-virtual';

function LongList({ items }) {
  return (
    <VirtualList
      height={600}
      itemCount={items.length}
      itemSize={50}
      renderItem={({ index }) => (
        <div>{items[index].name}</div>
      )}
    />
  );
}
```

---

## 🐛 Debugging Tips

### Zustand DevTools
```javascript
// Add to your store
import { devtools } from 'zustand/middleware';

const useStore = create(
  devtools(
    (set) => ({
      // your state
    }),
    { name: 'MyStore' }
  )
);
```

### React DevTools
1. Install React DevTools browser extension
2. Inspect component props and state
3. Profile performance
4. Highlight updates

### API Debugging
```javascript
// The API client logs errors automatically
// Check console for detailed error messages

// For manual debugging:
import apiClient from '../utils/apiClient';

apiClient.interceptors.request.use(request => {
  console.log('Request:', request);
  return request;
});

apiClient.interceptors.response.use(response => {
  console.log('Response:', response);
  return response;
});
```

---

## 📊 Performance Monitoring

### Measure Component Render Time
```javascript
import { Profiler } from 'react';

function onRenderCallback(
  id,
  phase,
  actualDuration,
  baseDuration,
  startTime,
  commitTime
) {
  console.log(`${id} took ${actualDuration}ms to render`);
}

<Profiler id="Dashboard" onRender={onRenderCallback}>
  <Dashboard />
</Profiler>
```

### Lighthouse Audit
```bash
# Run Lighthouse in Chrome DevTools
# Or use CLI
npm install -g lighthouse
lighthouse https://your-app.com --view
```

---

## ✅ Checklist for New Features

When adding a new feature:

- [ ] Use Zustand store for global state
- [ ] Use custom hooks for reusable logic
- [ ] Use API client for all API calls
- [ ] Keep components under 300 lines
- [ ] Add responsive classes (mobile-first)
- [ ] Memoize expensive calculations
- [ ] Lazy load if not critical
- [ ] Add loading states
- [ ] Add error handling
- [ ] Test on mobile device
- [ ] Check bundle size impact
- [ ] Add proper TypeScript types (if using TS)

---

## 📚 Additional Resources

### Documentation
- **Zustand**: https://zustand-demo.pmnd.rs/
- **React Performance**: https://react.dev/learn/render-and-commit
- **Tailwind CSS**: https://tailwindcss.com/docs

### Project Docs
- **Code Quality Guide**: `/app/CODE_QUALITY_IMPROVEMENTS.md`
- **Implementation Summary**: `/app/IMPLEMENTATION_SUMMARY.md`
- **This Guide**: `/app/DEVELOPER_GUIDE.md`

---

## 🤝 Contributing

When contributing code:
1. Follow the established patterns
2. Use the new architecture (Zustand, API client, hooks)
3. Write clean, readable code
4. Test thoroughly
5. Update documentation if needed

---

**Happy Coding! 🚀**
