const express = require('express');
const { body, validationResult } = require('express-validator');

const router = express.Router();

// Store configurations
const STORE_CONFIGS = {
  onlinekade: {
    name: 'OnlineKade',
    api_url: 'https://onlinekade.lk/api',
    delivery_time: '24-48 hours',
    min_order: 500
  },
  kapruka: {
    name: 'Kapruka',
    api_url: 'https://www.kapruka.com/api',
    delivery_time: '12-24 hours',
    min_order: 1000
  },
  glowmark: {
    name: 'Glowmark',
    api_url: 'https://glomark.lk/api',
    delivery_time: '6-12 hours',
    min_order: 750
  }
};

// Validation middleware for orders
const validateOrder = [
  body('userId').trim().notEmpty().withMessage('User ID is required'),
  body('items').isArray({ min: 1 }).withMessage('Items array is required and must contain at least one item'),
  body('items.*.productId').trim().notEmpty().withMessage('Product ID is required for each item'),
  body('items.*.title').trim().notEmpty().withMessage('Product title is required for each item'),
  body('items.*.price').isFloat({ min: 0 }).withMessage('Product price must be a positive number'),
  body('items.*.quantity').isInt({ min: 1 }).withMessage('Product quantity must be a positive integer'),
];

// POST /api/orders/:store - Place an order with a specific store
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

    // Calculate order total
    const orderTotal = items.reduce((total, item) => total + (item.price * item.quantity), 0);

    // Check minimum order requirement
    if (orderTotal < storeConfig.min_order) {
      return res.status(400).json({
        success: false,
        message: `Minimum order for ${storeConfig.name} is LKR ${storeConfig.min_order}. Current total: LKR ${orderTotal}`
      });
    }

    // Generate order ID
    const orderId = `${store.toUpperCase()}-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`;

    // Create order object
    const order = {
      orderId,
      userId,
      store: storeConfig.name,
      items: items.map(item => ({
        productId: item.productId,
        title: item.title,
        price: item.price,
        quantity: item.quantity,
        subtotal: item.price * item.quantity,
        source_url: item.source_url || '',
        collection: item.collection || store
      })),
      orderTotal,
      estimatedDelivery: storeConfig.delivery_time,
      status: 'confirmed',
      createdAt: new Date(),
      paymentMethod: 'cash_on_delivery' // Default payment method
    };

    // Log the order (in a real app, this would be saved to database)
    console.log(`📦 Order placed with ${storeConfig.name}:`, {
      orderId: order.orderId,
      userId: order.userId,
      itemCount: order.items.length,
      total: order.orderTotal,
      store: store
    });

    // Simulate API call to store (in a real app, this would call the actual store API)
    // For now, we'll just simulate success
    const simulateStoreResponse = () => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: true,
            storeOrderId: `${store.toUpperCase()}-STORE-${Math.random().toString(36).substr(2, 8)}`,
            estimatedDelivery: storeConfig.delivery_time,
            trackingNumber: `TRK-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`
          });
        }, 1000); // Simulate 1 second API call
      });
    };

    const storeResponse = await simulateStoreResponse();

    // Return success response
    res.status(201).json({
      success: true,
      message: `Order successfully placed with ${storeConfig.name}`,
      order: {
        ...order,
        storeOrderId: storeResponse.storeOrderId,
        trackingNumber: storeResponse.trackingNumber,
        estimatedDelivery: storeResponse.estimatedDelivery
      },
      store: {
        name: storeConfig.name,
        delivery_time: storeConfig.delivery_time,
        min_order: storeConfig.min_order
      }
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

    // Simulate order status check
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
      min_order: config.min_order
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

module.exports = router;
