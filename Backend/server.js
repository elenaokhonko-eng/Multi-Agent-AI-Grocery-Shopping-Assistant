const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const inventoryRoutes = require('./routes/inventory');
const orderRoutes = require('./routes/orders');

const app = express();
const PORT = process.env.PORT || 3005;

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB connection
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb+srv://yasirunipunbasnayake2_db_user:hFIS1XVxBmbaC5Ro@techtitans0.c5azljc.mongodb.net/kitchen-inventory';

mongoose.connect(MONGODB_URI)
  .then(() => {
    console.log('Connected to MongoDB');
  })
  .catch((error) => {
    console.error('MongoDB connection error:', error);
  });

// Routes
app.use('/api/inventory', inventoryRoutes);
app.use('/api/orders', orderRoutes);

// Health check route
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    message: 'Kitchen Inventory & Order API is running',
    timestamp: new Date().toISOString(),
    port: PORT
  });
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error(error);
  res.status(500).json({ error: 'Internal server error' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

app.listen(PORT, () => {
  console.log(`🚀 Server is running on port ${PORT}`);
  console.log(`📋 Health check: http://localhost:${PORT}/api/health`);
  console.log(`📦 Inventory API: http://localhost:${PORT}/api/inventory`);
  console.log(`🛒 Orders API: http://localhost:${PORT}/api/orders`);
  console.log(`🏪 Available stores: http://localhost:${PORT}/api/orders/stores`);
});
