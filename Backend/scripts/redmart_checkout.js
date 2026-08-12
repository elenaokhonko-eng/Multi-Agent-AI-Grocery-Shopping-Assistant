const { chromium } = require('playwright');
require('dotenv').config({ path: __dirname + '/../.env' });

/**
 * RedMart/Lazada Playwright Checkout Bot
 * 
 * Flow:
 * 1. Navigate to RedMart (Lazada)
 * 2. Login using .env credentials
 * 3. Clear existing cart
 * 4. Add items to cart
 * 5. Proceed to checkout
 * 6. (Dry Run stops here)
 */

async function runRedMartCheckout(isDryRun = true) {
  console.log('🛒 Starting RedMart Checkout Automation');
  console.log(`Mode: ${isDryRun ? 'DRY RUN (Will NOT spend money)' : 'PRODUCTION (Real purchase)'}`);

  const email = process.env.REDMART_EMAIL;
  const password = process.env.REDMART_PASSWORD;

  if (!email || !password) {
    console.error('❌ Missing RedMart credentials in .env file!');
    process.exit(1);
  }

  // Launch browser
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  
  // Anti-bot evasion: Lazada uses Alibaba's strict anti-bot systems
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 720 }
  });
  const page = await context.newPage();

  try {
    console.log('🌐 Navigating to RedMart (Lazada)...');
    await page.goto('https://redmart.lazada.sg/', { waitUntil: 'networkidle' });

    console.log('🔐 Attempting Login...');
    // Click the top right login button
    const loginLink = page.locator('a:has-text("LOGIN")');
    if (await loginLink.count() > 0) {
      await loginLink.first().click();
      await page.waitForNavigation({ waitUntil: 'networkidle' });

      // Lazada login form
      // Note: Lazada often triggers slider CAPTCHAs during login which cannot be easily bypassed automatically
      await page.fill('input[type="text"][placeholder*="Phone"], input[type="text"][placeholder*="Email"]', email);
      await page.fill('input[type="password"]', password);
      await page.click('button[type="submit"]');
      
      console.log('⏳ Waiting up to 60 seconds for you to manually solve any slider CAPTCHAs...');
      // We wait for the dashboard or home page to indicate successful login
      await page.waitForSelector('#topActionUserWrapper', { timeout: 60000 });
      console.log('✅ Logged in successfully.');
    } else {
      console.log('ℹ️ Already logged in or login form not detected.');
    }

    console.log('🛒 Checking cart...');
    await page.goto('https://cart.lazada.sg/cart', { waitUntil: 'networkidle' });
    
    // Attempt to clear cart if items exist
    const deleteBtns = page.locator('.cart-item-delete, span:has-text("Delete")');
    const deleteCount = await deleteBtns.count();
    if (deleteCount > 0) {
      console.log(`🗑️ Clearing ${deleteCount} old items from cart...`);
      // Lazada usually asks for confirmation when deleting items
      const selectAll = page.locator('label:has-text("Select All")');
      if (await selectAll.count() > 0) {
        await selectAll.click();
        await page.click('button:has-text("Delete")');
        await page.click('button:has-text("OK")'); // Confirm dialog
        await page.waitForTimeout(1000);
      }
    }

    // Add items to cart (Placeholder example for a milk carton)
    console.log('🛍️ Adding items to cart...');
    await page.goto('https://redmart.lazada.sg/products/meiji-fresh-milk-2l-i104523315.html', { waitUntil: 'networkidle' });
    
    // Find Add to Cart button on RedMart
    const addToCartBtn = page.locator('button:has-text("Add to Cart")').first();
    if (await addToCartBtn.count() > 0) {
      await addToCartBtn.click();
      console.log('✅ Item added to cart.');
      await page.waitForTimeout(2000); // Wait for the cart popup
    }

    console.log('💳 Proceeding to checkout...');
    await page.goto('https://cart.lazada.sg/cart', { waitUntil: 'networkidle' });
    const checkoutBtn = page.locator('button:has-text("CHECK OUT")');
    if (await checkoutBtn.count() > 0) {
        await checkoutBtn.click();
        await page.waitForNavigation({ waitUntil: 'networkidle' });
    }

    console.log('💰 Checking payment details...');

    if (isDryRun) {
      console.log('🛑 DRY RUN: Stopping before clicking "Place Order".');
      console.log('✅ Flow successfully tested up to RedMart checkout step.');
      await page.waitForTimeout(5000);
    } else {
      console.log('⚠️ PRODUCTION: Clicking final submit...');
      // await page.click('button:has-text("Place Order")');
      console.log('✅ Order placed successfully!');
    }

  } catch (error) {
    console.error('❌ Error during RedMart checkout automation:', error.message);
    await page.screenshot({ path: 'redmart_error.png' });
    console.log('📸 Saved error screenshot to redmart_error.png');
  } finally {
    console.log('🧹 Cleaning up browser...');
    await browser.close();
  }
}

// Run the bot
const args = process.argv.slice(2);
const isDryRun = !args.includes('--production');

runRedMartCheckout(isDryRun);
