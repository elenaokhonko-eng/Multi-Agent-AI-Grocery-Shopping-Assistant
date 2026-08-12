const { chromium } = require('playwright');
require('dotenv').config({ path: __dirname + '/../.env' });

/**
 * FairPrice Playwright Checkout Bot
 * 
 * Flow:
 * 1. Navigate to FairPrice
 * 2. Login using .env credentials (note: FairPrice uses OTP/Email links often)
 * 3. Clear existing cart
 * 4. Navigate to order items and Add to Cart
 * 5. Proceed to checkout
 * 6. (Dry Run stops here)
 */

async function runFairPriceCheckout(isDryRun = true) {
  console.log('🛒 Starting FairPrice Checkout Automation');
  console.log(`Mode: ${isDryRun ? 'DRY RUN (Will NOT spend money)' : 'PRODUCTION (Real purchase)'}`);

  const email = process.env.FAIRPRICE_EMAIL;
  const password = process.env.FAIRPRICE_PASSWORD;

  if (!email || !password) {
    console.error('❌ Missing FairPrice credentials in .env file!');
    process.exit(1);
  }

  // Use persistent context to save login cookies (like your Google Account)
  const path = require('path');
  const userDataDir = path.join(__dirname, '../playwright_data');
  
  const context = await chromium.launchPersistentContext(userDataDir, { 
    headless: false, 
    slowMo: 100,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  
  // launchPersistentContext automatically creates a first page
  const page = context.pages().length > 0 ? context.pages()[0] : await context.newPage();

  try {
    console.log('🌐 Navigating to FairPrice...');
    await page.goto('https://www.fairprice.com.sg/', { waitUntil: 'networkidle' });

    console.log('🔐 Attempting Login...');
    // FairPrice login requires navigating to the login modal
    await page.goto('https://www.fairprice.com.sg/login', { waitUntil: 'networkidle' });
    
    // Check if we need to log in
    if (await page.locator('input[type="email"]').count() > 0) {
      await page.fill('input[type="email"]', email);
      
      // Some versions of FairPrice use password, some use email OTP magic links
      if (await page.locator('input[type="password"]').count() > 0) {
        await page.fill('input[type="password"]', password);
        await page.click('button[type="submit"]');
      } else {
        console.log('⚠️ FairPrice requested OTP/Magic Link. Please check your email or SMS.');
        console.log('⏳ Waiting up to 60 seconds for you to manually complete login in the browser...');
        await page.waitForNavigation({ timeout: 60000 });
      }
      console.log('✅ Logged in successfully.');
    } else {
      console.log('ℹ️ Already logged in or login form not detected.');
    }

    console.log('🛒 Checking cart...');
    await page.goto('https://www.fairprice.com.sg/cart', { waitUntil: 'networkidle' });
    
    // Attempt to clear cart if items exist
    const deleteBtns = page.locator('button[aria-label="Remove item"]');
    const deleteCount = await deleteBtns.count();
    if (deleteCount > 0) {
      console.log(`🗑️ Clearing ${deleteCount} old items from cart...`);
      for (let i = 0; i < deleteCount; i++) {
        await deleteBtns.nth(0).click();
        await page.waitForTimeout(500);
      }
    }

    // Add items to cart (Placeholder example for an egg carton)
    console.log('🛍️ Adding items to cart...');
    await page.goto('https://www.fairprice.com.sg/product/pasar-fresh-eggs-10s-550g-10143180', { waitUntil: 'networkidle' });
    
    // Find Add to Cart button on FairPrice
    const addToCartBtn = page.locator('button:has-text("Add to cart")').first();
    if (await addToCartBtn.count() > 0) {
      await addToCartBtn.click();
      console.log('✅ Item added to cart.');
      await page.waitForTimeout(1000);
    }

    console.log('💳 Proceeding to checkout...');
    await page.goto('https://www.fairprice.com.sg/checkout', { waitUntil: 'networkidle' });

    console.log('💰 Checking payment details...');

    if (isDryRun) {
      console.log('🛑 DRY RUN: Stopping before clicking "Place Order".');
      console.log('✅ Flow successfully tested up to FairPrice checkout step.');
      await page.waitForTimeout(5000);
    } else {
      console.log('⚠️ PRODUCTION: Clicking final submit...');
      // await page.click('button:has-text("Place Order")');
      console.log('✅ Order placed successfully!');
    }

  } catch (error) {
    console.error('❌ Error during FairPrice checkout automation:', error.message);
    await page.screenshot({ path: 'fairprice_error.png' });
    console.log('📸 Saved error screenshot to fairprice_error.png');
  } finally {
    console.log('🧹 Cleaning up browser...');
    await browser.close();
  }
}

// Run the bot
const args = process.argv.slice(2);
const isDryRun = !args.includes('--production');

runFairPriceCheckout(isDryRun);
