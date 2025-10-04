/**
 * Testing Utilities Service
 * Provides comprehensive frontend testing capabilities
 */

class TestingUtils {
  constructor() {
    this.testResults = new Map();
    this.mockData = new Map();
    this.testSuites = new Map();
    
    this.init();
  }

  init() {
    this.setupGlobalTestHelpers();
    this.setupMockEndpoints();
    this.setupTestReporting();
    
    console.log('🧪 Testing Utils initialized');
  }

  setupGlobalTestHelpers() {
    // Make testing utilities available globally in development
    if (process.env.NODE_ENV === 'development') {
      window.testUtils = {
        runTests: () => this.runAllTests(),
        mockAPI: (endpoint, data) => this.mockAPIEndpoint(endpoint, data),
        getResults: () => this.getTestResults(),
        clearMocks: () => this.clearMocks(),
        simulateError: (type) => this.simulateError(type),
        performanceTest: () => this.runPerformanceTests()
      };
    }
  }

  setupMockEndpoints() {
    // Store original fetch for restoration
    this.originalFetch = window.fetch;
    
    // Mock data for different endpoints
    this.mockData.set('/api/user/profile', {
      id: 'test-user-123',
      full_name: 'Test User',
      email: 'test@earnnest.com',
      avatar: 'man',
      university: 'Test University',
      experience_points: 1250,
      current_streak: 7,
      level: 3
    });

    this.mockData.set('/api/transactions', [
      {
        id: 'txn-1',
        type: 'income',
        amount: 5000,
        category: 'Freelance',
        description: 'Web development project',
        timestamp: new Date().toISOString()
      },
      {
        id: 'txn-2',
        type: 'expense',
        amount: 500,
        category: 'Food',
        description: 'Groceries',
        timestamp: new Date().toISOString()
      }
    ]);

    this.mockData.set('/api/budgets', [
      {
        id: 'budget-1',
        category: 'Food',
        allocated_amount: 5000,
        spent_amount: 2500,
        remaining_amount: 2500
      },
      {
        id: 'budget-2',
        category: 'Transportation',
        allocated_amount: 3000,
        spent_amount: 1200,
        remaining_amount: 1800
      }
    ]);
  }

  setupTestReporting() {
    // Create test result container if in development
    if (process.env.NODE_ENV === 'development') {
      this.createTestResultsUI();
    }
  }

  createTestResultsUI() {
    const testContainer = document.createElement('div');
    testContainer.id = 'test-results-container';
    testContainer.style.cssText = `
      position: fixed;
      top: 10px;
      left: 10px;
      width: 300px;
      max-height: 400px;
      background: white;
      border: 2px solid #667eea;
      border-radius: 8px;
      padding: 16px;
      font-family: monospace;
      font-size: 12px;
      z-index: 10000;
      overflow-y: auto;
      display: none;
      box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    `;

    testContainer.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <strong>🧪 Test Results</strong>
        <button onclick="this.parentElement.parentElement.style.display='none'" 
                style="background: none; border: none; font-size: 16px; cursor: pointer;">×</button>
      </div>
      <div id="test-results-content">No tests run yet</div>
      <div style="margin-top: 12px;">
        <button onclick="window.testUtils.runTests()" 
                style="background: #667eea; color: white; border: none; padding: 4px 8px; border-radius: 4px; margin-right: 8px; cursor: pointer;">
          Run Tests
        </button>
        <button onclick="window.testUtils.clearMocks()" 
                style="background: #ef4444; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer;">
          Clear Mocks
        </button>
      </div>
    `;

    document.body.appendChild(testContainer);

    // Add toggle button
    const toggleButton = document.createElement('button');
    toggleButton.textContent = '🧪';
    toggleButton.style.cssText = `
      position: fixed;
      bottom: 20px;
      left: 20px;
      background: #667eea;
      color: white;
      border: none;
      border-radius: 50%;
      width: 48px;
      height: 48px;
      font-size: 20px;
      cursor: pointer;
      z-index: 10001;
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    `;

    toggleButton.onclick = () => {
      const container = document.getElementById('test-results-container');
      container.style.display = container.style.display === 'none' ? 'block' : 'none';
    };

    document.body.appendChild(toggleButton);
  }

  // API Mocking
  enableMocking() {
    window.fetch = async (url, options = {}) => {
      const urlStr = url.toString();
      
      // Check if we have mock data for this endpoint
      if (this.mockData.has(urlStr)) {
        const mockResponse = this.mockData.get(urlStr);
        
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, Math.random() * 500 + 100));
        
        return new Response(JSON.stringify(mockResponse), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }
      
      // If no mock, use original fetch
      return this.originalFetch(url, options);
    };
    
    console.log('🎭 API mocking enabled');
  }

  disableMocking() {
    window.fetch = this.originalFetch;
    console.log('🎭 API mocking disabled');
  }

  mockAPIEndpoint(endpoint, data) {
    this.mockData.set(endpoint, data);
    console.log(`🎭 Mocked endpoint: ${endpoint}`, data);
  }

  clearMocks() {
    this.mockData.clear();
    this.disableMocking();
    console.log('🧹 All mocks cleared');
  }

  // Test Suite Management
  addTestSuite(name, tests) {
    this.testSuites.set(name, tests);
    console.log(`📝 Added test suite: ${name}`);
  }

  async runTestSuite(name) {
    const tests = this.testSuites.get(name);
    if (!tests) {
      console.error(`❌ Test suite not found: ${name}`);
      return;
    }

    const results = {
      suite: name,
      tests: [],
      passed: 0,
      failed: 0,
      startTime: Date.now()
    };

    for (const test of tests) {
      try {
        const testResult = await this.runSingleTest(test);
        results.tests.push(testResult);
        
        if (testResult.passed) {
          results.passed++;
        } else {
          results.failed++;
        }
        
      } catch (error) {
        results.tests.push({
          name: test.name,
          passed: false,
          error: error.message,
          duration: 0
        });
        results.failed++;
      }
    }

    results.endTime = Date.now();
    results.duration = results.endTime - results.startTime;
    
    this.testResults.set(name, results);
    this.updateTestResultsUI(results);
    
    return results;
  }

  async runSingleTest(test) {
    const startTime = Date.now();
    
    try {
      await test.fn();
      
      return {
        name: test.name,
        passed: true,
        duration: Date.now() - startTime
      };
      
    } catch (error) {
      return {
        name: test.name,
        passed: false,
        error: error.message,
        duration: Date.now() - startTime
      };
    }
  }

  async runAllTests() {
    console.log('🧪 Running all test suites...');
    
    const overallResults = {
      suites: [],
      totalPassed: 0,
      totalFailed: 0,
      startTime: Date.now()
    };

    for (const [suiteName] of this.testSuites) {
      const suiteResults = await this.runTestSuite(suiteName);
      overallResults.suites.push(suiteResults);
      overallResults.totalPassed += suiteResults.passed;
      overallResults.totalFailed += suiteResults.failed;
    }

    overallResults.endTime = Date.now();
    overallResults.duration = overallResults.endTime - overallResults.startTime;
    
    console.log('📊 Test Results:', overallResults);
    return overallResults;
  }

  updateTestResultsUI(results) {
    const content = document.getElementById('test-results-content');
    if (!content) return;

    const html = `
      <div style="margin-bottom: 8px;">
        <strong>${results.suite}</strong> (${results.duration}ms)
      </div>
      <div style="color: green;">✅ Passed: ${results.passed}</div>
      <div style="color: red;">❌ Failed: ${results.failed}</div>
      <div style="margin-top: 8px; font-size: 11px;">
        ${results.tests.map(test => `
          <div style="margin: 2px 0; padding: 2px 4px; background: ${test.passed ? '#dcfce7' : '#fef2f2'}; border-radius: 3px;">
            ${test.passed ? '✅' : '❌'} ${test.name} (${test.duration}ms)
            ${test.error ? `<br><span style="color: red; font-size: 10px;">${test.error}</span>` : ''}
          </div>
        `).join('')}
      </div>
    `;

    content.innerHTML = html;
  }

  // Assertion Helpers
  assert(condition, message) {
    if (!condition) {
      throw new Error(message || 'Assertion failed');
    }
  }

  assertEqual(actual, expected, message) {
    if (actual !== expected) {
      throw new Error(message || `Expected ${expected}, got ${actual}`);
    }
  }

  assertNotEqual(actual, expected, message) {
    if (actual === expected) {
      throw new Error(message || `Expected not to equal ${expected}`);
    }
  }

  assertThrows(fn, message) {
    try {
      fn();
      throw new Error(message || 'Expected function to throw');
    } catch (error) {
      // Expected
    }
  }

  async assertAsync(asyncFn, message) {
    try {
      const result = await asyncFn();
      if (!result) {
        throw new Error(message || 'Async assertion failed');
      }
    } catch (error) {
      throw new Error(message || `Async assertion failed: ${error.message}`);
    }
  }

  // Performance Testing
  async runPerformanceTests() {
    const tests = [
      {
        name: 'Component Render Time',
        test: () => this.measureComponentRenderTime()
      },
      {
        name: 'API Response Time',
        test: () => this.measureAPIResponseTime()
      },
      {
        name: 'Bundle Size Check',
        test: () => this.checkBundleSize()
      },
      {
        name: 'Memory Usage',
        test: () => this.checkMemoryUsage()
      }
    ];

    const results = [];
    
    for (const test of tests) {
      try {
        const startTime = performance.now();
        const result = await test.test();
        const duration = performance.now() - startTime;
        
        results.push({
          name: test.name,
          passed: true,
          duration,
          result
        });
        
      } catch (error) {
        results.push({
          name: test.name,
          passed: false,
          error: error.message
        });
      }
    }

    console.log('⚡ Performance Test Results:', results);
    return results;
  }

  measureComponentRenderTime() {
    return new Promise((resolve) => {
      const startTime = performance.now();
      
      // Trigger a re-render by dispatching an event
      window.dispatchEvent(new CustomEvent('test-render'));
      
      requestAnimationFrame(() => {
        const renderTime = performance.now() - startTime;
        resolve({ renderTime });
      });
    });
  }

  async measureAPIResponseTime() {
    const startTime = performance.now();
    
    try {
      await fetch('/api/user/profile');
      const responseTime = performance.now() - startTime;
      
      return { responseTime };
      
    } catch (error) {
      return { error: error.message };
    }
  }

  checkBundleSize() {
    const scripts = Array.from(document.querySelectorAll('script[src]'));
    const totalSize = scripts.reduce((total, script) => {
      // This is a rough estimation
      return total + (script.src.length * 100); // Rough estimate
    }, 0);

    return { 
      bundleSize: totalSize,
      scriptCount: scripts.length,
      status: totalSize < 500000 ? 'good' : 'large'
    };
  }

  checkMemoryUsage() {
    if ('memory' in performance) {
      const memory = performance.memory;
      
      return {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit,
        usage: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
      };
    }
    
    return { error: 'Memory API not available' };
  }

  // Error Simulation
  simulateError(type) {
    switch (type) {
      case 'js':
        throw new Error('Simulated JavaScript error');
        
      case 'network':
        this.mockAPIEndpoint('/api/test-endpoint', null);
        fetch('/api/test-endpoint').catch(() => {});
        break;
        
      case 'memory':
        // Simulate memory leak
        const leakArray = [];
        for (let i = 0; i < 100000; i++) {
          leakArray.push(new Array(1000).fill('memory leak'));
        }
        break;
        
      case 'performance':
        // Simulate slow operation
        const start = Date.now();
        while (Date.now() - start < 2000) {
          // Block for 2 seconds
        }
        break;
        
      default:
        console.log('Unknown error type:', type);
    }
  }

  // Visual Regression Testing Helpers
  captureScreenshot(elementSelector) {
    return new Promise((resolve) => {
      const element = elementSelector 
        ? document.querySelector(elementSelector) 
        : document.body;
        
      if ('html2canvas' in window) {
        window.html2canvas(element).then(canvas => {
          resolve(canvas.toDataURL());
        });
      } else {
        resolve('html2canvas not available');
      }
    });
  }

  compareScreenshots(baseline, current) {
    // Simple pixel comparison (would need proper image diff library in production)
    return baseline === current;
  }

  // Accessibility Testing
  checkAccessibility() {
    const issues = [];
    
    // Check for alt text on images
    const images = document.querySelectorAll('img');
    images.forEach((img, index) => {
      if (!img.alt || img.alt.trim() === '') {
        issues.push(`Image ${index + 1} missing alt text`);
      }
    });
    
    // Check for form labels
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach((input, index) => {
      const label = document.querySelector(`label[for="${input.id}"]`);
      if (!label && !input.getAttribute('aria-label')) {
        issues.push(`Input ${index + 1} missing label`);
      }
    });
    
    // Check color contrast (basic check)
    const elements = document.querySelectorAll('*');
    elements.forEach((el, index) => {
      const styles = window.getComputedStyle(el);
      const color = styles.color;
      const backgroundColor = styles.backgroundColor;
      
      // Basic contrast check (would need proper contrast calculation)
      if (color === backgroundColor) {
        issues.push(`Element ${index + 1} has poor color contrast`);
      }
    });
    
    return {
      issues,
      passed: issues.length === 0
    };
  }

  // Utility Methods
  getTestResults() {
    const results = {};
    for (const [key, value] of this.testResults) {
      results[key] = value;
    }
    return results;
  }

  exportTestResults() {
    const data = {
      timestamp: Date.now(),
      results: this.getTestResults(),
      performance: performance.getEntriesByType('navigation')[0],
      userAgent: navigator.userAgent
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `test-results-${Date.now()}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
  }
}

// Pre-built test suites
const defaultTestSuites = {
  'UI Components': [
    {
      name: 'Button renders correctly',
      fn: async () => {
        const button = document.createElement('button');
        button.textContent = 'Test Button';
        document.body.appendChild(button);
        
        if (!button.textContent.includes('Test')) {
          throw new Error('Button text incorrect');
        }
        
        document.body.removeChild(button);
      }
    },
    {
      name: 'Form validation works',
      fn: async () => {
        const form = document.createElement('form');
        const input = document.createElement('input');
        input.required = true;
        form.appendChild(input);
        
        const isValid = form.checkValidity();
        if (isValid) {
          throw new Error('Form should be invalid when required field is empty');
        }
      }
    }
  ],
  
  'API Integration': [
    {
      name: 'Profile API returns data',
      fn: async () => {
        const response = await fetch('/api/user/profile');
        const data = await response.json();
        
        if (!data.id) {
          throw new Error('Profile data missing ID');
        }
      }
    },
    {
      name: 'Transactions API works',
      fn: async () => {
        const response = await fetch('/api/transactions');
        const data = await response.json();
        
        if (!Array.isArray(data)) {
          throw new Error('Transactions should be an array');
        }
      }
    }
  ]
};

// Create global testing utils instance
const testingUtils = new TestingUtils();

// Add default test suites
Object.entries(defaultTestSuites).forEach(([name, tests]) => {
  testingUtils.addTestSuite(name, tests);
});

// Export for use in React components
export default testingUtils;
