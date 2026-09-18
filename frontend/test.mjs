/**
 * @fileoverview High-performance, deterministic Vitest runner for Páramo Urbano frontend.
 * Executes Vitest programmatically with in-memory configuration to eliminate child process
 * bundling latency and esbuild deadlocks in non-interactive CI environments.
 */

import { createVitest } from 'vitest/node';
import react from '@vitejs/plugin-react';

async function runTests() {
  const vitest = await createVitest(
    'test',
    {
      config: false,
      run: true,
      watch: false,
      passWithNoTests: false,
    },
    {
      plugins: [react()],
      test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: ['./tests/setup.ts'],
        css: false,
      },
    }
  );

  await vitest.start();
  await vitest.close();

  const failedTests = vitest.state.getFailedFilepaths();
  if (failedTests.length > 0) {
    console.error(`\n❌ [Vitest] Tests failed in ${failedTests.length} file(s).`);
    process.exit(1);
  } else {
    console.log('\n✅ [Vitest] All frontend test suites passed successfully.');
    process.exit(0);
  }
}

runTests().catch((err) => {
  console.error('[Vitest] Runner encountered an unhandled exception:', err);
  process.exit(1);
});
