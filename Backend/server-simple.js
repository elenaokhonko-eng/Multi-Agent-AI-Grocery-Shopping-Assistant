const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB connection
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/kitchen-inventory';

mongoose.connect(MONGODB_URI)
  .then(() => {
    console.log('Connected to MongoDB');
  })
  .catch((error) => {
    console.error('MongoDB connection error:', error);
  });

// Simple Inventory Item Schema
const inventoryItemSchema = new mongoose.Schema({
  name: { type: String, required: true, trim: true },
  quantity: { type: Number, required: true, min: 0 },
  unit: { type: String, required: true },
  category: { type: String, required: true },
  expiry: { type: Date }
}, { timestamps: true });

const InventoryItem = mongoose.model('InventoryItem', inventoryItemSchema);

// Routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', message: 'Kitchen Inventory API is running' });
});

app.get('/api/inventory', async (req, res) => {
  try {
    const items = await InventoryItem.find().sort({ createdAt: -1 });
    res.json(items);
  } catch (error) {
    console.error('Error fetching inventory items:', error);
    res.status(500).json({ error: 'Failed to fetch inventory items' });
  }
});

app.post('/api/inventory', async (req, res) => {
  try {
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

app.patch('/api/inventory/:id/quantity', async (req, res) => {
  try {
    const { quantity } = req.body;
    const item = await InventoryItem.findByIdAndUpdate(
      req.params.id,
      { quantity },
      { new: true }
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

app.delete('/api/inventory/:id', async (req, res) => {
  const { id } = req.params;

  // 1) Validate ID early
  if (!mongoose.isValidObjectId(id)) {
    return res.status(400).json({ error: 'Invalid item id' });
  }

  try {
    // 2) Use deleteOne and check deletedCount
    const result = await InventoryItem.deleteOne({ _id: id });

    if (result.deletedCount === 0) {
      return res.status(404).json({ error: 'Item not found' });
    }

    // 3) Return 200 with a body; many UIs dislike 204 No Content
    return res.status(200).json({ ok: true, deletedId: id });
  } catch (error) {
    console.error('Error deleting inventory item:', error);
    return res.status(500).json({ error: 'Failed to delete inventory item' });
  }
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/api/health`);
});
