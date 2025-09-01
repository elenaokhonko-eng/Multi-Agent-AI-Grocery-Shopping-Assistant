const mongoose = require('mongoose');

const inventoryItemSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true
  },
  quantity: {
    type: Number,
    required: true,
    min: 0
  },
  unit: {
    type: String,
    required: true,
    enum: ['pieces', 'kg', 'grams', 'liters', 'ml', 'cups', 'tbsp', 'tsp', 'lbs', 'oz']
  },
  category: {
    type: String,
    required: true,
    enum: ['Grains', 'Dairy', 'Vegetables', 'Fruits', 'Meat', 'Seafood', 'Spices', 'Beverages', 'Snacks', 'Other']
  },
  expiry: {
    type: Date
  }
}, {
  timestamps: true
});

// Index for better query performance
inventoryItemSchema.index({ category: 1 });
inventoryItemSchema.index({ expiry: 1 });
inventoryItemSchema.index({ quantity: 1 });

module.exports = mongoose.model('InventoryItem', inventoryItemSchema);
