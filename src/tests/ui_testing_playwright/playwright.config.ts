import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Directory where the tests are located
  testDir: './ui-tests',
  
  // Run tests in parallel
  fullyParallel: true,
  
  // Fail the build if test.only is left in the code
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Limit the number of workers on CI
  workers: process.env.CI ? 1 : undefined,
  
  // Set a global timeout for each test
  timeout: 300000,
  
  // Use HTML reporter to generate test reports
  reporter: 'html',
  
  use: {
    // Collect trace on first retry
    trace: 'on-first-retry',
    
    // Run tests in headful mode. Set to "true" to run in headless mode
    headless: false,
    
    // Ignore HTTPS errors
    ignoreHTTPSErrors: true, 
  },

  projects: [
    {
      // Run tests on Firefox browser
      name: 'firefox',
      use: { 
        ...devices['Desktop Firefox'],
        // No need to specify proxy settings to use system proxy
      },
    },
  ],
});