// @ts-check
import { defineConfig, devices } from '@playwright/test';

module.exports = defineConfig({
    testDir: './tests',
    outputDir: './test-results',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: 1,
    timeout: 60000,
    use: {
        launchOptions: {
            args: ['--start-maximized']
        },
    },
    projects: [
        {
            name: 'chromium',
            use: { 
                ...devices['Desktop Chromium'], 
                viewport: null,
                permissions: ['clipboard-read', 'clipboard-write']
            }
        },
        {
            name: 'firefox',
            use: { ...devices['Desktop Firefox'] }
        }
    ]
});