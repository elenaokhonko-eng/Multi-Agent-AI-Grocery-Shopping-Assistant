const express = require('express');
const { body, validationResult } = require('express-validator');
const Order = require('../models/Order');

const router = express.Router();

// Singapore Store configurations
const STORE_CONFIGS = {
  littlefarms: {
    name: 'Little Farms',
    api_url: 'https://littlefarms.com/api',
    delivery_time: '12 hours',
    min_order: 50,
    delivery_fee: 12.0,
    free_shipping_threshold: 100
  },
  fairprice: {
    name: 'FairPrice',
    api_url: 'https://www.fairprice.com.sg/api',
    delivery_time: '24 hours',
    min_order: 20,
    delivery_fee: 7.0,
    free_shipping_threshold: 100
  },
  shengsiong: {
    name: 'Sheng Siong',
    api_url: 'https://shengsiong.com.sg/api',
    delivery_time: '24 hours',
    min_order: 20,
    delivery_fee: 6.0,
    free_shipping_threshold: 100
  },
  coldstorage: {
    name: 'Cold Storage',
    api_url: 'https://coldstorage.com.sg/api',
    delivery_time: '18 hours',
    min_order: 30,
    delivery_fee: 8.0,
    free_shipping_threshold: 100
  },
  lazada: {
    name: 'RedMart',
    api_url: 'https://www.lazada.sg/api',
    delivery_time: '24 hours',
    min_order: 20,
    delivery_fee: 6.99,
    free_shipping_threshold: 100
  }
};

// Validation middleware for orders including secure credit card check
const validateOrder = [
  body('userId').trim().notEmpty().withMessage('User ID is required'),
  body('items').isArray({ min: 1 }).withMessage('Items array must contain at least one item'),
  body('items.*.productId').trim().notEmpty().withMessage('Product ID is required'),
  body('items.*.title').trim().notEmpty().withMessage('Product title is required'),
  body('items.*.price').isFloat({ min: 0 }).withMessage('Price must be a positive number'),
  body('items.*.quantity').isInt({ min: 1 }).withMessage('Quantity must be a positive integer'),
  
  // [PHASE 0]: Removed raw card validation fields to prevent capturing sensitive data
];

// POST /api/orders/:store - Place an order with a specific Singapore store
router.post('/:store', validateOrder, async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ 
        success: false,
        message: 'Validation failed',
        errors: errors.array() 
      });
    }

    const { store } = req.params;
    const { userId, items } = req.body;

    // Validate store
    const storeConfig = STORE_CONFIGS[store.toLowerCase()];
    if (!storeConfig) {
      return res.status(400).json({
        success: false,
        message: `Unsupported store: ${store}. Supported stores: ${Object.keys(STORE_CONFIGS).join(', ')}`
      });
    }

    // [PHASE 0]: Refuse to execute simulated purchase
    return res.status(501).json({
      success: false,
      message: 'DEMO_ONLY: Live checkout via Node is disabled. Application is in fixture mode.'
    });

  } catch (error) {
    console.error(`Error placing order with ${req.params.store}:`, error);
    res.status(500).json({ 
      success: false,
      message: 'Failed to place order',
      error: error.message 
    });
  }
});

// GET /api/orders/:store/status/:orderId - Get order status
router.get('/:store/status/:orderId', async (req, res) => {
  try {
    const { store, orderId } = req.params;

    const storeConfig = STORE_CONFIGS[store.toLowerCase()];
    if (!storeConfig) {
      return res.status(400).json({
        success: false,
        message: `Unsupported store: ${store}`
      });
    }

    const statusOptions = ['confirmed', 'processing', 'shipped', 'out_for_delivery', 'delivered'];
    const randomStatus = statusOptions[Math.floor(Math.random() * statusOptions.length)];

    res.json({
      success: true,
      orderId,
      store: storeConfig.name,
      status: randomStatus,
      lastUpdated: new Date(),
      estimatedDelivery: storeConfig.delivery_time
    });

  } catch (error) {
    console.error(`Error checking order status:`, error);
    res.status(500).json({ 
      success: false,
      message: 'Failed to check order status',
      error: error.message 
    });
  }
});

// GET /api/orders/stores - Get available stores
router.get('/stores', (req, res) => {
  try {
    const stores = Object.entries(STORE_CONFIGS).map(([key, config]) => ({
      id: key,
      name: config.name,
      delivery_time: config.delivery_time,
      min_order: config.min_order,
      delivery_fee: config.delivery_fee,
      free_shipping_threshold: config.free_shipping_threshold
    }));

    res.json({
      success: true,
      stores
    });
  } catch (error) {
    console.error('Error fetching stores:', error);
    res.status(500).json({ 
      success: false,
      message: 'Failed to fetch stores',
      error: error.message 
    });
  }
});

// GET /api/orders/:store/user/:userId - Get all orders for a user from a store
router.get('/:store/user/:userId', async (req, res) => {
  try {
    const { store, userId } = req.params;
    
    const storeConfig = STORE_CONFIGS[store.toLowerCase()];
    if (!storeConfig) {
      return res.status(400).json({ success: false, message: `Unsupported store: ${store}` });
    }

    const orders = await Order.find({ userId, store: storeConfig.name }).sort({ createdAt: -1 });

    res.json({
      success: true,
      store: storeConfig.name,
      data: orders
    });
  } catch (error) {
    console.error('Error fetching user orders:', error);
    res.status(500).json({ success: false, message: 'Failed to fetch orders', error: error.message });
  }
});

// PUT /api/orders/:store/:orderId/cancel - Cancel an order
router.put('/:store/:orderId/cancel', async (req, res) => {
  try {
    const { store, orderId } = req.params;

    const storeConfig = STORE_CONFIGS[store.toLowerCase()];
    if (!storeConfig) {
      return res.status(400).json({ success: false, message: `Unsupported store: ${store}` });
    }

    const order = await Order.findOne({ orderId, store: storeConfig.name });
    
    if (!order) {
      return res.status(404).json({ success: false, message: 'Order not found' });
    }

    if (order.status === 'cancelled') {
      return res.status(400).json({ success: false, message: 'Order is already cancelled' });
    }

    if (order.status !== 'pending' && order.status !== 'in_transit') {
      return res.status(400).json({ success: false, message: 'Only pending or in_transit orders can be cancelled' });
    }

    order.status = 'cancelled';
    await order.save();

    res.json({
      success: true,
      message: 'Order cancelled successfully',
      order
    });
  } catch (error) {
    console.error('Error cancelling order:', error);
    res.status(500).json({ success: false, message: 'Failed to cancel order', error: error.message });
  }
});

module.exports = router;
