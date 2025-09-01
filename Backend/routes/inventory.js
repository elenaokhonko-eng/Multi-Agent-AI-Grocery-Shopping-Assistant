const express = require('express');
const { body, validationResult } = require('express-validator');
const InventoryItem = require('../models/InventoryItem');

const router = express.Router();

// Validation middleware
const validateInventoryItem = [
  body('name').trim().notEmpty().withMessage('Name is required'),
  body('quantity').isFloat({ min: 0 }).withMessage('Quantity must be a positive number'),
  body('unit').isIn(['pieces', 'kg', 'grams', 'liters', 'ml', 'cups', 'tbsp', 'tsp', 'lbs', 'oz']).withMessage('Invalid unit'),
  body('category').isIn(['Grains', 'Dairy', 'Vegetables', 'Fruits', 'Meat', 'Seafood', 'Spices', 'Beverages', 'Snacks', 'Other']).withMessage('Invalid category'),
  body('expiry').optional().isISO8601().withMessage('Invalid expiry date format')
];

// GET /api/inventory/low-stock - Get low stock items (MUST be before /:id route)
router.get('/low-stock', async (req, res) => {
  try {
    const threshold = parseFloat(req.query.threshold) || 2;
    const items = await InventoryItem.find({ quantity: { $lte: threshold } }).sort({ quantity: 1 });
    res.json(items);
  } catch (error) {
    console.error('Error fetching low stock items:', error);
    res.status(500).json({ error: 'Failed to fetch low stock items' });
  }
});

// GET /api/inventory/expiring - Get expiring items (MUST be before /:id route)
router.get('/expiring', async (req, res) => {
  try {
    const days = parseInt(req.query.days) || 7;
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() + days);
    
    const items = await InventoryItem.find({
      expiry: { $lte: cutoffDate, $gte: new Date() }
    }).sort({ expiry: 1 });
    
    res.json(items);
  } catch (error) {
    console.error('Error fetching expiring items:', error);
    res.status(500).json({ error: 'Failed to fetch expiring items' });
  }
});

// GET /api/inventory/category/:category - Get items by category (MUST be before /:id route)
router.get('/category/:category', async (req, res) => {
  try {
    const items = await InventoryItem.find({ category: req.params.category }).sort({ createdAt: -1 });
    res.json(items);
  } catch (error) {
    console.error('Error fetching items by category:', error);
    res.status(500).json({ error: 'Failed to fetch items by category' });
  }
});

// GET /api/inventory - Get all inventory items
router.get('/', async (req, res) => {
  try {
    const items = await InventoryItem.find().sort({ createdAt: -1 });
    res.json(items);
  } catch (error) {
    console.error('Error fetching inventory items:', error);
    res.status(500).json({ error: 'Failed to fetch inventory items' });
  }
});

// GET /api/inventory/:id - Get a single inventory item
router.get('/:id', async (req, res) => {
  try {
    const item = await InventoryItem.findById(req.params.id);
    if (!item) {
      return res.status(404).json({ error: 'Item not found' });
    }
    res.json(item);
  } catch (error) {
    console.error('Error fetching inventory item:', error);
    res.status(500).json({ error: 'Failed to fetch inventory item' });
  }
});

// POST /api/inventory - Create a new inventory item
router.post('/', validateInventoryItem, async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { name, quantity, unit, category, expiry } = req.body;
    const item = new InventoryItem({
      name,
      quantity,
      unit,
      category,
      ...(expiry && { expiry: new Date(expiry) })
    });

    const savedItem = await item.save();
    res.status(201).json(savedItem);
  } catch (error) {
    console.error('Error creating inventory item:', error);
    res.status(500).json({ error: 'Failed to create inventory item' });
  }
});

// PUT /api/inventory/:id - Update an inventory item
router.put('/:id', validateInventoryItem, async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { name, quantity, unit, category, expiry } = req.body;
    const updateData = {
      name,
      quantity,
      unit,
      category,
      ...(expiry && { expiry: new Date(expiry) })
    };

    const item = await InventoryItem.findByIdAndUpdate(
      req.params.id,
      updateData,
      { new: true, runValidators: true }
    );

    if (!item) {
      return res.status(404).json({ error: 'Item not found' });
    }

    res.json(item);
  } catch (error) {
    console.error('Error updating inventory item:', error);
    res.status(500).json({ error: 'Failed to update inventory item' });
  }
});

// PATCH /api/inventory/:id/quantity - Update only the quantity
router.patch('/:id/quantity', async (req, res) => {
  try {
    const { quantity } = req.body;
    
    if (typeof quantity !== 'number' || quantity < 0) {
      return res.status(400).json({ error: 'Invalid quantity' });
    }

    const item = await InventoryItem.findByIdAndUpdate(
      req.params.id,
      { quantity },
      { new: true, runValidators: true }
    );

    if (!item) {
      return res.status(404).json({ error: 'Item not found' });
    }

    res.json(item);
  } catch (error) {
    console.error('Error updating quantity:', error);
    res.status(500).json({ error: 'Failed to update quantity' });
  }
});

// DELETE /api/inventory/:id - Delete an inventory item
router.delete('/:id', async (req, res) => {
  try {
    const item = await InventoryItem.findByIdAndDelete(req.params.id);
    if (!item) {
      return res.status(404).json({ error: 'Item not found' });
    }
    res.status(204).send();
  } catch (error) {
    console.error('Error deleting inventory item:', error);
    res.status(500).json({ error: 'Failed to delete inventory item' });
  }
});

module.exports = router;
