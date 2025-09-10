#!/usr/bin/env node

/**
 * Seed script to populate the kitchen inventory database with sample products
 * Usage: node scripts/seed_inventory.js
 */

const axios = require('axios');

// Configuration
const API_BASE_URL = 'http://localhost:3001/api';
const INVENTORY_ENDPOINT = `${API_BASE_URL}/inventory`;

// Sample inventory data with various categories and realistic quantities
const sampleInventoryData = [
  // Grains
  {
    name: 'Basmati Rice',
    quantity: 5.5,
    unit: 'kg',
    category: 'Grains',
    expiry: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString() // 1 year from now
  },
  {
    name: 'Red Rice',
    quantity: 2.0,
    unit: 'kg',
    category: 'Grains',
    expiry: new Date(Date.now() + 300 * 24 * 60 * 60 * 1000).toISOString() // 10 months from now
  },
  {
    name: 'Wheat Flour',
    quantity: 3.5,
    unit: 'kg',
    category: 'Grains',
    expiry: new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString() // 6 months from now
  },
  {
    name: 'Quinoa',
    quantity: 1.2,
    unit: 'kg',
    category: 'Grains',
    expiry: new Date(Date.now() + 400 * 24 * 60 * 60 * 1000).toISOString() // 13 months from now
  },
  
  // Dairy
  {
    name: 'Whole Milk',
    quantity: 2,
    unit: 'liters',
    category: 'Dairy',
    expiry: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString() // 5 days from now
  },
  {
    name: 'Greek Yogurt',
    quantity: 500,
    unit: 'grams',
    category: 'Dairy',
    expiry: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString() // 1 week from now
  },
  {
    name: 'Cheddar Cheese',
    quantity: 400,
    unit: 'grams',
    category: 'Dairy',
    expiry: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() // 1 month from now
  },
  {
    name: 'Butter',
    quantity: 250,
    unit: 'grams',
    category: 'Dairy',
    expiry: new Date(Date.now() + 45 * 24 * 60 * 60 * 1000).toISOString() // 45 days from now
  },
  
  // Vegetables
  {
    name: 'Tomatoes',
    quantity: 1.5,
    unit: 'kg',
    category: 'Vegetables',
    expiry: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString() // 1 week from now
  },
  {
    name: 'Onions',
    quantity: 2.0,
    unit: 'kg',
    category: 'Vegetables',
    expiry: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000).toISOString() // 3 weeks from now
  },
  {
    name: 'Carrots',
    quantity: 1.0,
    unit: 'kg',
    category: 'Vegetables',
    expiry: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString() // 2 weeks from now
  },
  {
    name: 'Bell Peppers',
    quantity: 6,
    unit: 'pieces',
    category: 'Vegetables',
    expiry: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString() // 10 days from now
  },
  {
    name: 'Potatoes',
    quantity: 3.0,
    unit: 'kg',
    category: 'Vegetables',
    expiry: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() // 1 month from now
  },
  
  // Fruits
  {
    name: 'Bananas',
    quantity: 12,
    unit: 'pieces',
    category: 'Fruits',
    expiry: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString() // 5 days from now
  },
  {
    name: 'Apples',
    quantity: 2.0,
    unit: 'kg',
    category: 'Fruits',
    expiry: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString() // 2 weeks from now
  },
  {
    name: 'Oranges',
    quantity: 1.5,
    unit: 'kg',
    category: 'Fruits',
    expiry: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString() // 10 days from now
  },
  {
    name: 'Mango',
    quantity: 4,
    unit: 'pieces',
    category: 'Fruits',
    expiry: new Date(Date.now() + 6 * 24 * 60 * 60 * 1000).toISOString() // 6 days from now
  },
  
  // Meat
  {
    name: 'Chicken Breast',
    quantity: 1.5,
    unit: 'kg',
    category: 'Meat',
    expiry: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString() // 3 days from now
  },
  {
    name: 'Ground Beef',
    quantity: 800,
    unit: 'grams',
    category: 'Meat',
    expiry: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString() // 2 days from now
  },
  {
    name: 'Pork Chops',
    quantity: 6,
    unit: 'pieces',
    category: 'Meat',
    expiry: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString() // 4 days from now
  },
  
  // Seafood
  {
    name: 'Salmon Fillet',
    quantity: 600,
    unit: 'grams',
    category: 'Seafood',
    expiry: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString() // 2 days from now
  },
  {
    name: 'Prawns',
    quantity: 500,
    unit: 'grams',
    category: 'Seafood',
    expiry: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString() // 1 day from now
  },
  
  // Spices
  {
    name: 'Black Pepper',
    quantity: 100,
    unit: 'grams',
    category: 'Spices',
    expiry: new Date(Date.now() + 730 * 24 * 60 * 60 * 1000).toISOString() // 2 years from now
  },
  {
    name: 'Turmeric Powder',
    quantity: 150,
    unit: 'grams',
    category: 'Spices',
    expiry: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString() // 1 year from now
  },
  {
    name: 'Cinnamon Sticks',
    quantity: 50,
    unit: 'grams',
    category: 'Spices',
    expiry: new Date(Date.now() + 1095 * 24 * 60 * 60 * 1000).toISOString() // 3 years from now
  },
  {
    name: 'Cumin Seeds',
    quantity: 80,
    unit: 'grams',
    category: 'Spices',
    expiry: new Date(Date.now() + 730 * 24 * 60 * 60 * 1000).toISOString() // 2 years from now
  },
  
  // Beverages
  {
    name: 'Orange Juice',
    quantity: 1,
    unit: 'liters',
    category: 'Beverages',
    expiry: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString() // 1 week from now
  },
  {
    name: 'Green Tea',
    quantity: 100,
    unit: 'grams',
    category: 'Beverages',
    expiry: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString() // 1 year from now
  },
  {
    name: 'Coffee Beans',
    quantity: 500,
    unit: 'grams',
    category: 'Beverages',
    expiry: new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString() // 6 months from now
  },
  
  // Snacks
  {
    name: 'Mixed Nuts',
    quantity: 300,
    unit: 'grams',
    category: 'Snacks',
    expiry: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString() // 3 months from now
  },
  {
    name: 'Dark Chocolate',
    quantity: 200,
    unit: 'grams',
    category: 'Snacks',
    expiry: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString() // 1 year from now
  },
  {
    name: 'Crackers',
    quantity: 2,
    unit: 'pieces',
    category: 'Snacks',
    expiry: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString() // 2 months from now
  },
  
  // Other
  {
    name: 'Olive Oil',
    quantity: 500,
    unit: 'ml',
    category: 'Other',
    expiry: new Date(Date.now() + 730 * 24 * 60 * 60 * 1000).toISOString() // 2 years from now
  },
  {
    name: 'Honey',
    quantity: 250,
    unit: 'grams',
    category: 'Other'
    // No expiry for honey
  },
  {
    name: 'Sea Salt',
    quantity: 1,
    unit: 'kg',
    category: 'Other'
    // No expiry for salt
  }
];

/**
 * Check if the server is running
 */
async function checkServerHealth() {
  try {
    const response = await axios.get(`${API_BASE_URL}/health`);
    console.log('✅ Server is running:', response.data.message);
    return true;
  } catch (error) {
    console.error('❌ Server is not running or not accessible');
    console.error('Please make sure the backend server is running on port 3005');
    return false;
  }
}

/**
 * Clear existing inventory (optional)
 */
async function clearInventory() {
  try {
    const response = await axios.get(INVENTORY_ENDPOINT);
    const existingItems = response.data;
    
    if (existingItems.length > 0) {
      console.log(`\n🧹 Found ${existingItems.length} existing items. Clearing inventory...`);
      
      for (const item of existingItems) {
        await axios.delete(`${INVENTORY_ENDPOINT}/${item._id}`);
      }
      
      console.log('✅ Inventory cleared successfully');
    } else {
      console.log('📋 Inventory is already empty');
    }
  } catch (error) {
    console.error('❌ Error clearing inventory:', error.response?.data || error.message);
  }
}

/**
 * Add a single inventory item
 */
async function addInventoryItem(item) {
  try {
    const response = await axios.post(INVENTORY_ENDPOINT, item);
    return response.data;
  } catch (error) {
    console.error(`❌ Error adding ${item.name}:`, error.response?.data || error.message);
    return null;
  }
}

/**
 * Seed the inventory with sample data
 */
async function seedInventory() {
  console.log('\n🌱 Starting inventory seeding process...');
  console.log(`📦 Adding ${sampleInventoryData.length} sample items to inventory\n`);
  
  let successCount = 0;
  let failCount = 0;
  
  for (const [index, item] of sampleInventoryData.entries()) {
    process.stdout.write(`\r⏳ Processing item ${index + 1}/${sampleInventoryData.length}: ${item.name}`);
    
    const result = await addInventoryItem(item);
    if (result) {
      successCount++;
    } else {
      failCount++;
    }
    
    // Small delay to avoid overwhelming the server
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  console.log(`\n\n✅ Seeding completed!`);
  console.log(`   📈 Successfully added: ${successCount} items`);
  console.log(`   ❌ Failed to add: ${failCount} items`);
  
  if (successCount > 0) {
    console.log('\n📊 Sample inventory summary by category:');
    const categories = {};
    sampleInventoryData.forEach(item => {
      categories[item.category] = (categories[item.category] || 0) + 1;
    });
    
    Object.entries(categories).forEach(([category, count]) => {
      console.log(`   ${category}: ${count} items`);
    });
  }
}

/**
 * Display current inventory
 */
async function displayCurrentInventory() {
  try {
    const response = await axios.get(INVENTORY_ENDPOINT);
    const items = response.data;
    
    console.log(`\n📋 Current inventory (${items.length} items):`);
    console.log('─'.repeat(80));
    console.log('Name'.padEnd(25) + 'Quantity'.padEnd(12) + 'Category'.padEnd(15) + 'Expiry');
    console.log('─'.repeat(80));
    
    items.slice(0, 10).forEach(item => {
      const expiry = item.expiry ? new Date(item.expiry).toLocaleDateString() : 'No expiry';
      console.log(
        item.name.substring(0, 24).padEnd(25) +
        `${item.quantity} ${item.unit}`.padEnd(12) +
        item.category.padEnd(15) +
        expiry
      );
    });
    
    if (items.length > 10) {
      console.log(`... and ${items.length - 10} more items`);
    }
    
    console.log('─'.repeat(80));
  } catch (error) {
    console.error('❌ Error fetching inventory:', error.response?.data || error.message);
  }
}

/**
 * Main execution function
 */
async function main() {
  console.log('🏪 Kitchen Inventory Seeder');
  console.log('═'.repeat(50));
  
  // Check if server is running
  const isServerRunning = await checkServerHealth();
  if (!isServerRunning) {
    process.exit(1);
  }
  
  // Ask user if they want to clear existing inventory
  const args = process.argv.slice(2);
  const shouldClear = args.includes('--clear') || args.includes('-c');
  
  if (shouldClear) {
    await clearInventory();
  }
  
  // Seed the inventory
  await seedInventory();
  
  // Display current inventory
  await displayCurrentInventory();
  
  console.log('\n🎉 Inventory seeding process completed!');
  console.log('💡 You can now use the inventory API endpoints to manage these items.');
  console.log(`🌐 View all items: GET ${INVENTORY_ENDPOINT}`);
  console.log(`🔍 Low stock items: GET ${INVENTORY_ENDPOINT}/low-stock`);
  console.log(`⏰ Expiring items: GET ${INVENTORY_ENDPOINT}/expiring`);
}

// Handle uncaught errors
process.on('unhandledRejection', (error) => {
  console.error('\n❌ Unhandled error:', error.message);
  process.exit(1);
});

// Run the script
if (require.main === module) {
  main().catch(error => {
    console.error('\n❌ Script failed:', error.message);
    process.exit(1);
  });
}

module.exports = {
  seedInventory,
  sampleInventoryData,
  checkServerHealth,
  clearInventory
};