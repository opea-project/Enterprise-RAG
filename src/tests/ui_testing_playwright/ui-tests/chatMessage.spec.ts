import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Read test data from JSON file
const testData = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'testData.json'), 'utf-8'));

test('login and interact with the page', async ({ page }) => {
  // Load the URL from test data
  await page.goto(testData.url);
  await page.waitForTimeout(10000);

  // Resize window to the dimensions from test data
  await page.setViewportSize(testData.viewport);

  // Click on <button> "Login"
  await Promise.all([
    page.click('button'),
    page.waitForNavigation()
  ]);

  // Fill username from test data
  await page.fill('#username', testData.username);

  // Fill password from test data
  await page.fill('#password', testData.password);

  // Click on <button> "Sign In"
  await Promise.all([
    page.click('#kc-login'),
    page.waitForNavigation()
  ]);

  // Click on <textarea> .prompt-input
  await page.click('.prompt-input');

  // Fill prompt input from test data
  await page.fill('[name="prompt-input"]', testData.promptInput);

  // Click on <button> .prompt-input__button
  await page.click('.prompt-input__button');

  // Check if <p> "Hello. If you have a ques..." is present
  const isElementPresent = await page.$('.bot-message__text p') !== null;
  expect(isElementPresent).toBe(true);
});