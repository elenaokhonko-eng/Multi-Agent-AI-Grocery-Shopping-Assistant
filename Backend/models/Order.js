const mongoose = require('mongoose');

const orderItemSchema = new mongoose.Schema({
  productId: { type: String, required: true },
  title: { type: String, required: true },
  price: { type: Number, required: true },
  quantity: { type: Number, required: true },
  subtotal: { type: Number, required: true },
  source_url: { type: String },
  collection: { type: String }
});

const statusHistorySchema = new mongoose.Schema({
  status: { type: String, required: true },
  timestamp: { type: Date, default: Date.now },
  note: { type: String }
});

const orderSchema = new mongoose.Schema({
  orderId: { type: String, required: true, unique: true },
  userId: { type: String, required: true },
  store: { type: String, required: true },
  items: [orderItemSchema],
  orderSubtotal: { type: Number, required: true },
  deliveryFee: { type: Number, required: true },
  orderTotal: { type: Number, required: true },
  totalAmount: { type: Number, required: true }, // Alias for frontend compatibility
  estimatedDelivery: { type: String },
  status: { 
    type: String, 
    enum: ['pending', 'in_transit', 'store_pickup', 'completed', 'cancelled'],
    default: 'pending' 
  },
  statusHistory: [statusHistorySchema],
  paymentMethod: { type: String, default: 'credit_card' },
  cardDetailsMasked: { type: String },
  storeOrderId: { type: String },
  trackingNumber: { type: String }
}, { timestamps: true });

// Ensure status changes are tracked
orderSchema.pre('save', function(next) {
  if (this.isModified('status')) {
    this.statusHistory.push({
      status: this.status,
      note: `Status updated to ${this.status}`
    });
  } else if (this.isNew) {
    this.statusHistory.push({
      status: this.status,
      note: 'Order created'
    });
  }
  next();
});

module.exports = mongoose.model('Order', orderSchema);
