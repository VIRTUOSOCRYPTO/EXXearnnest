/**
 * Frontend Performance Monitoring Service
 * Tracks performance metrics, user experience, and provides analytics
 */

class PerformanceMonitor {
  constructor() {
    this.metrics = new Map();
    this.observers = new Map();
    this.thresholds = {
      FCP: 1500,    // First Contentful Paint
      LCP: 2500,    // Largest Contentful Paint
      FID: 100,     // First Input Delay
      CLS: 0.1,     // Cumulative Layout Shift
      TTI: 3000     // Time to Interactive
    };
    
    this.init();
  }

  init() {
    this.setupWebVitals();
    this.setupNavigationTiming();
    this.setupResourceTiming();
    this.setupUserTiming();
    this.setupErrorTracking();
    this.setupCustomMetrics();
    
    console.log('📊 Performance Monitor initialized');
  }

  setupWebVitals() {
    // First Contentful Paint
    this.observePerformanceEntry('paint', (entries) => {
      entries.forEach(entry => {
        if (entry.name === 'first-contentful-paint') {
          this.recordMetric('FCP', entry.startTime, {
            threshold: this.thresholds.FCP,
            timestamp: Date.now()
          });
        }
      });
    });

    // Largest Contentful Paint
    this.observePerformanceEntry('largest-contentful-paint', (entries) => {
      const lastEntry = entries[entries.length - 1];
      this.recordMetric('LCP', lastEntry.startTime, {
        element: lastEntry.element?.tagName,
        threshold: this.thresholds.LCP,
        timestamp: Date.now()
      });
    });

    // First Input Delay
    this.observePerformanceEntry('first-input', (entries) => {
      entries.forEach(entry => {
        this.recordMetric('FID', entry.processingStart - entry.startTime, {
          eventType: entry.name,
          threshold: this.thresholds.FID,
          timestamp: Date.now()
        });
      });
    });

    // Cumulative Layout Shift
    let cumulativeLayoutShift = 0;
    this.observePerformanceEntry('layout-shift', (entries) => {
      entries.forEach(entry => {
        if (!entry.hadRecentInput) {
          cumulativeLayoutShift += entry.value;
          this.recordMetric('CLS', cumulativeLayoutShift, {
            threshold: this.thresholds.CLS,
            timestamp: Date.now()
          });
        }
      });
    });
  }

  setupNavigationTiming() {
    if ('performance' in window && 'getEntriesByType' in performance) {
      const navigationEntry = performance.getEntriesByType('navigation')[0];
      
      if (navigationEntry) {
        const metrics = {
          DNS: navigationEntry.domainLookupEnd - navigationEntry.domainLookupStart,
          TCP: navigationEntry.connectEnd - navigationEntry.connectStart,
          TLS: navigationEntry.secureConnectionStart > 0 
            ? navigationEntry.connectEnd - navigationEntry.secureConnectionStart 
            : 0,
          TTFB: navigationEntry.responseStart - navigationEntry.requestStart,
          DOMLoad: navigationEntry.domContentLoadedEventEnd - navigationEntry.navigationStart,
          WindowLoad: navigationEntry.loadEventEnd - navigationEntry.navigationStart
        };

        Object.entries(metrics).forEach(([key, value]) => {
          this.recordMetric(`NAV_${key}`, value, {
            type: 'navigation',
            timestamp: Date.now()
          });
        });
      }
    }
  }

  setupResourceTiming() {
    this.observePerformanceEntry('resource', (entries) => {
      entries.forEach(entry => {
        const resourceType = this.getResourceType(entry.name);
        const loadTime = entry.responseEnd - entry.startTime;
        
        this.recordMetric(`RESOURCE_${resourceType.toUpperCase()}`, loadTime, {
          url: entry.name,
          size: entry.transferSize || 0,
          cached: entry.transferSize === 0 && entry.decodedBodySize > 0,
          timestamp: Date.now()
        });
      });
    });
  }

  setupUserTiming() {
    // Custom timing marks and measures
    this.observePerformanceEntry('mark', (entries) => {
      entries.forEach(entry => {
        this.recordMetric(`MARK_${entry.name}`, entry.startTime, {
          type: 'mark',
          timestamp: Date.now()
        });
      });
    });

    this.observePerformanceEntry('measure', (entries) => {
      entries.forEach(entry => {
        this.recordMetric(`MEASURE_${entry.name}`, entry.duration, {
          type: 'measure',
          timestamp: Date.now()
        });
      });
    });
  }

  setupErrorTracking() {
    // JavaScript errors
    window.addEventListener('error', (event) => {
      this.recordError('JS_ERROR', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        timestamp: Date.now()
      });
    });

    // Promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.recordError('PROMISE_REJECTION', {
        reason: event.reason,
        promise: event.promise,
        timestamp: Date.now()
      });
    });

    // Resource loading errors
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.recordError('RESOURCE_ERROR', {
          element: event.target.tagName,
          source: event.target.src || event.target.href,
          timestamp: Date.now()
        });
      }
    }, true);
  }

  setupCustomMetrics() {
    // React component render times
    this.measureReactRenders();
    
    // API response times
    this.measureAPIRequests();
    
    // User interaction times
    this.measureUserInteractions();
    
    // Memory usage
    this.measureMemoryUsage();
  }

  observePerformanceEntry(entryType, callback) {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          callback(list.getEntries());
        });
        
        observer.observe({ entryTypes: [entryType] });
        this.observers.set(entryType, observer);
        
      } catch (error) {
        console.warn(`Performance observer for ${entryType} not supported:`, error);
      }
    }
  }

  recordMetric(name, value, metadata = {}) {
    const metric = {
      name,
      value,
      metadata,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent
    };

    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    
    this.metrics.get(name).push(metric);
    
    // Check thresholds and alert if needed
    if (metadata.threshold && value > metadata.threshold) {
      this.alertPerformanceIssue(name, value, metadata.threshold);
    }
    
    // Send to analytics
    this.sendMetricToAnalytics(metric);
  }

  recordError(type, details) {
    const error = {
      type,
      details,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent
    };

    if (!this.metrics.has('ERRORS')) {
      this.metrics.set('ERRORS', []);
    }
    
    this.metrics.get('ERRORS').push(error);
    
    // Send to error tracking
    this.sendErrorToTracking(error);
  }

  measureReactRenders() {
    // Hook into React DevTools if available
    if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
      const hook = window.__REACT_DEVTOOLS_GLOBAL_HOOK__;
      
      hook.onCommitFiberRoot = (id, root, priorityLevel) => {
        performance.mark('react-render-start');
      };
      
      hook.onCommitFiberUnmount = () => {
        performance.mark('react-render-end');
        performance.measure('react-render', 'react-render-start', 'react-render-end');
      };
    }
  }

  measureAPIRequests() {
    // Monkey patch fetch
    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      const startTime = performance.now();
      const url = args[0];
      
      try {
        const response = await originalFetch(...args);
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.recordMetric('API_REQUEST', duration, {
          url: url.toString(),
          status: response.status,
          method: args[1]?.method || 'GET',
          success: response.ok,
          timestamp: Date.now()
        });
        
        return response;
        
      } catch (error) {
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.recordMetric('API_REQUEST', duration, {
          url: url.toString(),
          method: args[1]?.method || 'GET',
          success: false,
          error: error.message,
          timestamp: Date.now()
        });
        
        throw error;
      }
    };
  }

  measureUserInteractions() {
    // Click tracking
    document.addEventListener('click', (event) => {
      const startTime = performance.now();
      
      requestAnimationFrame(() => {
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.recordMetric('INTERACTION_CLICK', duration, {
          element: event.target.tagName,
          className: event.target.className,
          timestamp: Date.now()
        });
      });
    });

    // Form submission tracking
    document.addEventListener('submit', (event) => {
      performance.mark('form-submit-start');
      
      setTimeout(() => {
        performance.mark('form-submit-end');
        performance.measure('form-submit', 'form-submit-start', 'form-submit-end');
      }, 0);
    });
  }

  measureMemoryUsage() {
    if ('memory' in performance) {
      setInterval(() => {
        const memory = performance.memory;
        
        this.recordMetric('MEMORY_USED', memory.usedJSHeapSize, {
          total: memory.totalJSHeapSize,
          limit: memory.jsHeapSizeLimit,
          timestamp: Date.now()
        });
      }, 30000); // Every 30 seconds
    }
  }

  getResourceType(url) {
    if (url.match(/\.(css)$/)) return 'css';
    if (url.match(/\.(js)$/)) return 'js';
    if (url.match(/\.(png|jpg|jpeg|gif|svg|webp)$/)) return 'image';
    if (url.match(/\.(woff|woff2|ttf)$/)) return 'font';
    if (url.includes('/api/')) return 'api';
    return 'other';
  }

  alertPerformanceIssue(metric, value, threshold) {
    console.warn(`⚠️ Performance issue detected: ${metric} (${value}ms) exceeds threshold (${threshold}ms)`);
    
    // You could send alerts to monitoring services here
    this.sendAlert({
      type: 'PERFORMANCE_THRESHOLD_EXCEEDED',
      metric,
      value,
      threshold,
      timestamp: Date.now()
    });
  }

  sendMetricToAnalytics(metric) {
    // Send to your analytics service
    if (navigator.sendBeacon) {
      const data = JSON.stringify(metric);
      navigator.sendBeacon('/api/analytics/performance', data);
    }
  }

  sendErrorToTracking(error) {
    // Send to error tracking service
    if (navigator.sendBeacon) {
      const data = JSON.stringify(error);
      navigator.sendBeacon('/api/analytics/errors', data);
    }
  }

  sendAlert(alert) {
    // Send alerts to monitoring service
    if (navigator.sendBeacon) {
      const data = JSON.stringify(alert);
      navigator.sendBeacon('/api/monitoring/alerts', data);
    }
  }

  // Public API methods
  mark(name) {
    performance.mark(name);
  }

  measure(name, startMark, endMark) {
    performance.measure(name, startMark, endMark);
  }

  getMetrics(filter = null) {
    if (filter) {
      return this.metrics.get(filter) || [];
    }
    
    const allMetrics = {};
    for (const [key, value] of this.metrics) {
      allMetrics[key] = value;
    }
    
    return allMetrics;
  }

  getPerformanceSummary() {
    const summary = {
      pageLoad: {},
      userExperience: {},
      resources: {},
      errors: [],
      recommendations: []
    };

    // Page load metrics
    const fcpMetrics = this.metrics.get('FCP') || [];
    const lcpMetrics = this.metrics.get('LCP') || [];
    const ttfbMetrics = this.metrics.get('NAV_TTFB') || [];

    if (fcpMetrics.length > 0) {
      const avgFCP = fcpMetrics.reduce((sum, m) => sum + m.value, 0) / fcpMetrics.length;
      summary.pageLoad.FCP = avgFCP;
      summary.pageLoad.FCPGrade = avgFCP < 1500 ? 'Good' : avgFCP < 2500 ? 'Needs Improvement' : 'Poor';
    }

    if (lcpMetrics.length > 0) {
      const avgLCP = lcpMetrics.reduce((sum, m) => sum + m.value, 0) / lcpMetrics.length;
      summary.pageLoad.LCP = avgLCP;
      summary.pageLoad.LCPGrade = avgLCP < 2500 ? 'Good' : avgLCP < 4000 ? 'Needs Improvement' : 'Poor';
    }

    // User experience metrics
    const fidMetrics = this.metrics.get('FID') || [];
    const clsMetrics = this.metrics.get('CLS') || [];

    if (fidMetrics.length > 0) {
      const avgFID = fidMetrics.reduce((sum, m) => sum + m.value, 0) / fidMetrics.length;
      summary.userExperience.FID = avgFID;
      summary.userExperience.FIDGrade = avgFID < 100 ? 'Good' : avgFID < 300 ? 'Needs Improvement' : 'Poor';
    }

    if (clsMetrics.length > 0) {
      const latestCLS = clsMetrics[clsMetrics.length - 1].value;
      summary.userExperience.CLS = latestCLS;
      summary.userExperience.CLSGrade = latestCLS < 0.1 ? 'Good' : latestCLS < 0.25 ? 'Needs Improvement' : 'Poor';
    }

    // Resource metrics
    const resourceMetrics = Array.from(this.metrics.keys())
      .filter(key => key.startsWith('RESOURCE_'))
      .reduce((acc, key) => {
        const metrics = this.metrics.get(key) || [];
        const type = key.replace('RESOURCE_', '').toLowerCase();
        
        if (metrics.length > 0) {
          acc[type] = {
            count: metrics.length,
            averageLoadTime: metrics.reduce((sum, m) => sum + m.value, 0) / metrics.length,
            totalSize: metrics.reduce((sum, m) => sum + (m.metadata.size || 0), 0)
          };
        }
        
        return acc;
      }, {});

    summary.resources = resourceMetrics;

    // Errors
    summary.errors = this.metrics.get('ERRORS') || [];

    // Generate recommendations
    summary.recommendations = this.generateRecommendations(summary);

    return summary;
  }

  generateRecommendations(summary) {
    const recommendations = [];

    if (summary.pageLoad.LCP && summary.pageLoad.LCP > 2500) {
      recommendations.push({
        type: 'LCP',
        priority: 'high',
        message: 'Largest Contentful Paint is slow. Consider optimizing images and critical resources.'
      });
    }

    if (summary.userExperience.FID && summary.userExperience.FID > 100) {
      recommendations.push({
        type: 'FID',
        priority: 'high',
        message: 'First Input Delay is high. Consider reducing JavaScript execution time.'
      });
    }

    if (summary.userExperience.CLS && summary.userExperience.CLS > 0.1) {
      recommendations.push({
        type: 'CLS',
        priority: 'medium',
        message: 'Cumulative Layout Shift is high. Ensure images and ads have dimensions set.'
      });
    }

    if (summary.resources.image && summary.resources.image.averageLoadTime > 1000) {
      recommendations.push({
        type: 'IMAGES',
        priority: 'medium',
        message: 'Image load times are slow. Consider using WebP format and lazy loading.'
      });
    }

    if (summary.errors.length > 0) {
      recommendations.push({
        type: 'ERRORS',
        priority: 'high',
        message: `${summary.errors.length} JavaScript errors detected. Check console for details.`
      });
    }

    return recommendations;
  }

  exportMetrics() {
    const data = {
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      metrics: this.getMetrics(),
      summary: this.getPerformanceSummary()
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `performance-metrics-${Date.now()}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
  }

  clearMetrics() {
    this.metrics.clear();
    console.log('📊 Performance metrics cleared');
  }

  destroy() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
    this.metrics.clear();
    console.log('📊 Performance Monitor destroyed');
  }
}

// Create global performance monitor instance
const performanceMonitor = new PerformanceMonitor();

// Export for use in React components
export default performanceMonitor;
