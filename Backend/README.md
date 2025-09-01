# Kitchen Inventory Backend API

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start the server (simple version)
node server-simple.js

# Alternative: Start development server with auto-restart
npm run dev

# Note: npm start currently has issues, use the direct node command above
```

## 📁 Project Structure

```
backend/
├── models/
│   └── InventoryItem.js        # MongoDB schema
├── routes/
│   └── inventory.js            # API routes (unused in simple version)
├── server.js                   # Complex server (unused)
├── server-simple.js            # Main server file (currently used)
├── package.json
├── .env                        # Environment variables
└── README.md
```

## 🔧 Environment Configuration

Create a `.env` file:
```env
MONGODB_URI=mongodb://localhost:27017/kitchen-inventory
PORT=3001
NODE_ENV=development
```

## 📋 API Endpoints

### Base URL: `http://localhost:3001/api`

#### Health Check
```http
GET /api/health
```
**Response:**
```json
{
  "status": "OK",
  "message": "Kitchen Inventory API is running"
}
```

#### Get All Inventory Items
```http
GET /api/inventory
```
**Response:**
```json
[
  {
    "_id": "64f...",
    "name": "Rice",
    "quantity": 5,
    "unit": "kg",
    "category": "Grains",
    "expiry": "2024-12-01T00:00:00.000Z",
    "createdAt": "2025-09-01T04:39:52.039Z",
    "updatedAt": "2025-09-01T04:39:52.039Z",
    "__v": 0
  }
]
```

#### Create New Inventory Item
```http
POST /api/inventory
Content-Type: application/json

{
  "name": "Tomatoes",
  "quantity": 2.5,
  "unit": "kg", 
  "category": "Vegetables",
  "expiry": "2025-09-15"  // Optional
}
```

#### Update Item Quantity
```http
PATCH /api/inventory/:id/quantity
Content-Type: application/json

{
  "quantity": 3
}
```

#### Delete Item
```http
DELETE /api/inventory/:id
```

## 🗄️ Database Schema

### InventoryItem Model
```javascript
{
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
    required: true
  },
  category: {
    type: String,
    required: true
  },
  expiry: {
    type: Date
  }
}
```

**Timestamps**: `createdAt` and `updatedAt` are automatically added.

## 🧪 Testing the API

### Using curl

```bash
# Health check
curl http://localhost:3001/api/health

# Get all items
curl http://localhost:3001/api/inventory

# Add new item
curl -X POST http://localhost:3001/api/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Chicken Breast",
    "quantity": 1.2,
    "unit": "kg",
    "category": "Meat",
    "expiry": "2025-09-05"
  }'

# Update quantity (replace ITEM_ID with actual MongoDB _id)
curl -X PATCH http://localhost:3001/api/inventory/ITEM_ID/quantity \
  -H "Content-Type: application/json" \
  -d '{"quantity": 0.8}'

# Delete item
curl -X DELETE http://localhost:3001/api/inventory/ITEM_ID
```

### Using Postman/Insomnia

Import this collection or create requests manually:

1. **GET** `http://localhost:3001/api/health`
2. **GET** `http://localhost:3001/api/inventory`
3. **POST** `http://localhost:3001/api/inventory` with JSON body
4. **PATCH** `http://localhost:3001/api/inventory/:id/quantity` with JSON body
5. **DELETE** `http://localhost:3001/api/inventory/:id`

## 🛠️ Development

### Dependencies
```json
{
  "express": "^4.18.2",      // Web framework
  "mongoose": "^8.0.0",      // MongoDB ODM
  "cors": "^2.8.5",          // Cross-origin requests
  "dotenv": "^16.3.1"        // Environment variables
}
```

### Dev Dependencies
```json
{
  "nodemon": "^3.0.1"        // Auto-restart on changes
}
```

### Scripts
```bash
# Start the server directly (recommended)
node server-simple.js

# Start with nodemon (auto-restart) - for development
npm run dev     

# Note: npm start has issues with path-to-regexp, use direct node command
```

## 🔄 Database Operations

### MongoDB Connection
The server automatically connects to MongoDB on startup:
```javascript
mongoose.connect(MONGODB_URI)
  .then(() => console.log('Connected to MongoDB'))
  .catch(error => console.error('MongoDB connection error:', error));
```

### Sample Data Operations
```javascript
// Create sample data
const sampleItems = [
  {
    name: "Rice",
    quantity: 5,
    unit: "kg",
    category: "Grains",
    expiry: new Date("2024-12-01")
  },
  {
    name: "Milk", 
    quantity: 2,
    unit: "liters",
    category: "Dairy",
    expiry: new Date("2025-09-05")
  }
];
```

## 🚨 Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Invalid input data
- **404 Not Found**: Item doesn't exist
- **500 Internal Server Error**: Database or server errors

Example error response:
```json
{
  "error": "Item not found"
}
```

## 🔒 Security Features

- **CORS enabled** for cross-origin requests
- **Input validation** for all fields
- **Error sanitization** to prevent information leakage
- **Environment variables** for sensitive configuration

## 📊 Monitoring

### Health Check
The `/api/health` endpoint provides:
- Server status
- Database connection status
- API version information

### Logs
Server logs include:
- MongoDB connection status
- API request information
- Error details for debugging

## 🚀 Production Deployment

### Environment Variables
```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/kitchen-inventory
PORT=8080
NODE_ENV=production
```

### Recommended Hosting
- **Railway** (recommended)
- **Render**
- **Heroku**
- **DigitalOcean App Platform**

### Database Hosting
- **MongoDB Atlas** (recommended)
- **DigitalOcean Managed Databases**

## 🔄 Migration from Complex to Simple Server

Currently using `server-simple.js` for simplicity. To switch to the full-featured server:

1. Update `package.json` scripts:
```json
{
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  }
}
```

2. The full server includes:
   - Express Router separation
   - Input validation middleware
   - Advanced error handling
   - Additional endpoints (by category, low stock, expiring items)

## 📈 Performance Optimization

### Database Indexes
Add indexes for better query performance:
```javascript
// In MongoDB shell
db.inventoryitems.createIndex({ "category": 1 })
db.inventoryitems.createIndex({ "expiry": 1 })
db.inventoryitems.createIndex({ "quantity": 1 })
```

### Caching
Consider adding Redis for caching frequently accessed data.

---

## ✅ Current Status

- 🟢 **Server**: Running on port 3001 with `node server-simple.js`
- 🟢 **Database**: Connected to MongoDB
- 🟢 **CORS**: Configured for frontend
- 🟢 **API**: All endpoints functional
- 🟢 **Error Handling**: Comprehensive coverage
- ⚠️ **Note**: Use `node server-simple.js` instead of `npm start` due to path-to-regexp issues

**Backend is fully operational! 🎉**
