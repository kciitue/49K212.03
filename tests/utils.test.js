// ========================================
// TESTS: Example Unit Tests
// ========================================

import { isValidEmail, formatDate, formatCurrency } from '../src/utils.js';

// Test Suite
const tests = [
  {
    name: 'isValidEmail - Valid email',
    test: () => isValidEmail('test@example.com') === true,
  },
  {
    name: 'isValidEmail - Invalid email',
    test: () => isValidEmail('invalid-email') === false,
  },
  {
    name: 'formatCurrency - Positive amount',
    test: () => formatCurrency(1000000).includes('1.000.000'),
  },
  {
    name: 'formatDate - Valid date',
    test: () => formatDate(new Date('2026-03-07')).length > 0,
  },
];

// Run tests
function runTests() {
  console.log('🧪 Running tests...');
  let passed = 0;
  let failed = 0;

  tests.forEach((test) => {
    try {
      if (test.test()) {
        console.log(`✅ ${test.name}`);
        passed++;
      } else {
        console.log(`❌ ${test.name}`);
        failed++;
      }
    } catch (error) {
      console.log(`❌ ${test.name} - ${error.message}`);
      failed++;
    }
  });

  console.log(`\n📊 Results: ${passed} passed, ${failed} failed`);
}

// Export for use
export { runTests };

// Run if executed directly
if (typeof window === 'undefined') {
  runTests();
}
