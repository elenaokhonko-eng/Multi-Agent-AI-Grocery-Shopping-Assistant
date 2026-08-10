const express = require('express');
const { body, validationResult } = require('express-validator');

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
  
  // Secure payment fields
  body('payment.cardholderName').trim().notEmpty().withMessage('Cardholder Name is required'),
  body('payment.cardNumber').trim().matches(/^[\d\s-]{13,19}$/).withMessage('Valid credit card number is required'),
  body('payment.expiryDate').trim().matches(/^(0[1-9]|1[0-2])\/?([2-9][0-9])$/).withMessage('Expiry Date must be MM/YY'),
  body('payment.cvv').trim().matches(/^\d{3,4}$/).withMessage('CVV must be 3 or 4 digits')
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
    const { userId, items, payment } = req.body;

    // Validate store
    const storeConfig = STORE_CONFIGS[store.toLowerCase()];
    if (!storeConfig) {
      return res.status(400).json({
        success: false,
        message: `Unsupported store: ${store}. Supported stores: ${Object.keys(STORE_CONFIGS).join(', ')}`
      });
    }

    // Calculate order subtotal
    const orderSubtotal = items.reduce((total, item) => total + (item.price * item.quantity), 0);

    // Check minimum order requirement
    if (orderSubtotal < storeConfig.min_order) {
      return res.status(400).json({
        success: false,
        message: `Minimum order for ${storeConfig.name} is SGD ${storeConfig.min_order}. Current total: SGD ${orderSubtotal}`
      });
    }

    // Determine delivery charge based on SGD 100 cutoff
    const deliveryFee = orderSubtotal >= storeConfig.free_shipping_threshold ? 0 : storeConfig.delivery_fee;
    const orderTotal = orderSubtotal + deliveryFee;

    // Generate masked card number for receipt logs (last 4 digits only)
    const rawCard = payment.cardNumber.replace(/[\s-]/g, '');
    const maskedCard = `•••• •••• •••• ${rawCard.slice(-4)}`;

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
      orderSubtotal,
      deliveryFee,
      orderTotal,
      estimatedDelivery: storeConfig.delivery_time,
      status: 'confirmed',
      createdAt: new Date(),
      paymentMethod: 'credit_card',
      cardDetailsMasked: maskedCard
    };

    // Log the transaction securely (NEVER log raw CC or CVV details)
    console.log(`🔒 Secure CC order authorized for ${userId} with card ${maskedCard}`);
    console.log(`📦 Order placed with ${storeConfig.name}:`, {
      orderId: order.orderId,
      total: order.orderTotal,
      items: order.items.length
    });

    // Simulate merchant payment gateway response
    const simulatePaymentGateway = () => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: true,
            authCode: `AUTH-SG-${Math.floor(100000 + Math.random() * 900000)}`,
            transactionId: `TXN-PAY-${Date.now()}`
          });
        }, 800);
      });
    };

    const paymentResponse = await simulatePaymentGateway();

    // Simulate API call to store order placement
    const simulateStoreResponse = () => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: true,
            storeOrderId: `${store.toUpperCase()}-STORE-${Math.random().toString(36).substr(2, 8)}`,
            trackingNumber: `TRK-SG-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`
          });
        }, 500);
      });
    };

    const storeResponse = await simulateStoreResponse();

    // Return success response
    res.status(201).json({
      success: true,
      message: `Order successfully placed and authorized with ${storeConfig.name}`,
      paymentAuth: {
        authorized: true,
        authCode: paymentResponse.authCode,
        transactionId: paymentResponse.transactionId,
        cardLastFour: rawCard.slice(-4)
      },
      order: {
        ...order,
        storeOrderId: storeResponse.storeOrderId,
        trackingNumber: storeResponse.trackingNumber
      },
      store: {
        name: storeConfig.name,
        delivery_time: storeConfig.delivery_time,
        min_order: storeConfig.min_order,
        delivery_fee: storeConfig.delivery_fee,
        free_shipping_threshold: storeConfig.free_shipping_threshold
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

module.exports = router;
