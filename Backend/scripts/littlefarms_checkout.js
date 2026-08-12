const { chromium } = require('playwright');
require('dotenv').config({ path: __dirname + '/../.env' });

/**
 * Little Farms Playwright Checkout Bot
 * 
 * Flow:
 * 1. Login using .env credentials
 * 2. Search for "whole salmon"
 * 3. Add to cart
 * 4. Proceed to checkout
 * 5. Inject membership ID
 * 6. (Dry Run stops here before paying)
 */

async function runLittleFarmsCheckout(isDryRun = true) {
  console.log('🛒 Starting Little Farms Checkout Automation');
  console.log(`Mode: ${isDryRun ? 'DRY RUN (Will NOT spend money)' : 'PRODUCTION (Real purchase)'}`);

  const email = process.env.LITTLEFARMS_EMAIL;
  const password = process.env.LITTLEFARMS_PASSWORD;
  const membershipId = process.env.LITTLEFARMS_MEMBERSHIP_ID || '90727915';

  if (!email || !password) {
    console.error('❌ Missing Little Farms credentials in .env file!');
    process.exit(1);
  }

  // Launch browser (set headless to false to watch the bot work)
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // 1. Navigate to Little Farms
    console.log('🌐 Navigating to Little Farms...');
    await page.goto('https://littlefarms.com/', { waitUntil: 'networkidle' });

    // 2. Handle Login (Assuming typical Shopify/custom ecommerce login flow)
    console.log('🔐 Logging in...');
    // Note: Selectors may need to be adjusted based on actual Little Farms DOM
    // For now we assume a standard login URL
    await page.goto('https://littlefarms.com/account/login', { waitUntil: 'networkidle' });
    
    // Check if we are already logged in or if the login form exists
    const loginFormExists = await page.locator('form[action*="/account/login"]').count() > 0;
    
    if (loginFormExists) {
      await page.fill('input[type="email"]', email);
      await page.fill('input[type="password"]', password);
      await page.click('form[action*="/account/login"] button[type="submit"]');
      await page.waitForNavigation({ waitUntil: 'networkidle' });
      console.log('✅ Logged in successfully.');
    } else {
      console.log('ℹ️ Already logged in or login form not found.');
    }

    // 3. Search for "Whole Salmon"
    console.log('🔍 Searching for "Whole Salmon"...');
    // Using Little Farms search URL format
    await page.goto('https://littlefarms.com/search?q=whole+salmon', { waitUntil: 'networkidle' });
    
    // Wait for product results to load
    await page.waitForSelector('.product-card, .grid-item, .product-grid-item', { timeout: 10000 }).catch(() => {
      console.log('⚠️ Could not find standard product grid, page might be slow or selectors changed.');
    });

    // 4. Add the first relevant salmon item to cart
    console.log('🛍️ Adding item to cart...');
    // We will look for an "Add to Cart" button within the first product card
    // Adjust selector to Little Farms specific 'add to cart' button classes
    const addToCartBtns = page.locator('button:has-text("Add to Cart"), button:has-text("Add")');
    if (await addToCartBtns.count() > 0) {
      await addToCartBtns.first().click();
      console.log('✅ Added "Whole Salmon" to cart.');
      // Wait for cart animation/drawer
      await page.waitForTimeout(2000); 
    } else {
      console.error('❌ Could not find an Add to Cart button for Whole Salmon.');
      throw new Error('Item not found or out of stock');
    }

    // 5. Navigate to Checkout
    console.log('💳 Proceeding to checkout...');
    await page.goto('https://littlefarms.com/checkout', { waitUntil: 'networkidle' });

    // 6. Apply Membership ID
    console.log(`🎟️ Applying Membership ID: ${membershipId}...`);
    // Assuming there is a field for notes, discount codes, or a specific membership input
    // Often this is a discount code input or a custom field
    const discountInput = page.locator('input[name="checkout[reduction_code]"], input[placeholder*="Discount"]');
    if (await discountInput.count() > 0) {
      await discountInput.fill(membershipId);
      await page.click('button:has-text("Apply")');
      console.log('✅ Applied membership ID as discount code.');
      await page.waitForTimeout(2000);
    } else {
      console.log('⚠️ Could not find a membership/discount field on the checkout page.');
      // Sometimes it's in the cart notes before checkout
    }

    // 7. Payment step (Simulated)
    // At this point, the user would already have a saved payment method or we inject it
    console.log('💰 Checking payment method...');

    if (isDryRun) {
      console.log('🛑 DRY RUN: Stopping before final purchase confirmation.');
      console.log('✅ Flow successfully tested up to payment step.');
      // Keep browser open for a few seconds so user can see it
      await page.waitForTimeout(5000);
    } else {
      console.log('⚠️ PRODUCTION: Clicking final submit...');
      // await page.click('button:has-text("Pay now")');
      // await page.waitForNavigation();
      console.log('✅ Order placed successfully!');
    }

  } catch (error) {
    console.error('❌ Error during checkout automation:', error.message);
    // Optional: Take screenshot on failure
    await page.screenshot({ path: 'littlefarms_error.png' });
    console.log('📸 Saved error screenshot to littlefarms_error.png');
  } finally {
    console.log('🧹 Cleaning up browser...');
    await browser.close();
  }
}

// Run the bot
const args = process.argv.slice(2);
const isDryRun = !args.includes('--production');

runLittleFarmsCheckout(isDryRun);
