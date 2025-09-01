# Kitchen Inventory Management System - Full Stack Integration

## 🎯 Project Overview

A complete full-stack kitchen inventory management system with real-time data synchronization between a React frontend and Node.js backend connected to MongoDB.

## 🏗️ System Architecture

### Frontend (React + TypeScript + Vite)
- **Location**: `/Frontend`
- **Port**: `http://localhost:8080`
- **Tech Stack**: 
  - React 18 + TypeScript
  - Vite (build tool)
  - Tailwind CSS + Shadcn/ui components
  - React Query (TanStack Query) for state management
  - Sonner for toast notifications

### Backend (Node.js + Express)
- **Location**: `/backend`
- **Port**: `http://localhost:3001`
- **Tech Stack**:
  - Node.js + Express.js
  - Mongoose (MongoDB ODM)
  - CORS enabled for cross-origin requests
  - Express Validator for input validation
  - dotenv for environment configuration

### Database (MongoDB)
- **Port**: `27017`
- **Database**: `kitchen-inventory`
- **Collections**: `inventoryitems`

## 🚀 Setup Instructions

### Prerequisites
```bash
# Required software
- Node.js (v16 or higher)
- MongoDB (running on port 27017)
- npm or yarn package manager
```

### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install dependencies
npm install

# Create environment file
echo "MONGODB_URI=mongodb://localhost:27017/kitchen-inventory
PORT=3001
NODE_ENV=development" > .env

# Start the server
npm run dev
# OR for production
npm start
```

### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd Frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Verify Setup
```bash
# Test backend health
curl http://localhost:3001/api/health

# Expected response:
# {"status":"OK","message":"Kitchen Inventory API is running"}
```

## 📋 API Documentation

### Base URL
```
http://localhost:3001/api
```

### Endpoints

#### Health Check
```http
GET /api/health
```
**Response**: `{"status":"OK","message":"Kitchen Inventory API is running"}`

#### Inventory Operations

##### Get All Items
```http
GET /api/inventory
```
**Response**: Array of inventory items

##### Create New Item
```http
POST /api/inventory
Content-Type: application/json

{
  "name": "Rice",
  "quantity": 5,
  "unit": "kg",
  "category": "Grains",
  "expiry": "2024-12-01"  // Optional
}
```

##### Update Item Quantity
```http
PATCH /api/inventory/:id/quantity
Content-Type: application/json

{
  "quantity": 3
}
```

##### Delete Item
```http
DELETE /api/inventory/:id
```

### Sample API Usage

```bash
# Add new inventory item
curl -X POST http://localhost:3001/api/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tomatoes",
    "quantity": 2.5,
    "unit": "kg",
    "category": "Vegetables",
    "expiry": "2025-09-10"
  }'

# Update quantity
curl -X PATCH http://localhost:3001/api/inventory/ITEM_ID/quantity \
  -H "Content-Type: application/json" \
  -d '{"quantity": 1.5}'

# Get all items
curl http://localhost:3001/api/inventory
```

## 🗄️ Database Schema

### InventoryItem Model
```javascript
{
  _id: ObjectId,              // MongoDB auto-generated ID
  name: String,               // Item name (required)
  quantity: Number,           // Current stock level (min: 0)
  unit: String,               // Measurement unit (enum)
  category: String,           // Item category (enum)
  expiry: Date,               // Optional expiry date
  createdAt: Date,            // Auto-generated timestamp
  updatedAt: Date,            // Auto-generated timestamp
  __v: Number                 // Mongoose version key
}
```

### Available Categories
- Grains
- Dairy
- Vegetables
- Fruits
- Meat
- Seafood
- Spices
- Beverages
- Snacks
- Other

### Available Units
- pieces
- kg
- grams
- liters
- ml
- cups
- tbsp (tablespoons)
- tsp (teaspoons)
- lbs (pounds)
- oz (ounces)

## 🎨 Frontend Features

### Responsive Design
- **Desktop**: Full sidebar with detailed inventory management
- **Mobile**: Collapsible sidebar for space efficiency
- **Tablet**: Adaptive layout with touch-friendly controls

### Core Features
- ✅ **Real-time Inventory Display**: Live sync with MongoDB
- ✅ **Add Items**: Form with validation for all fields
- ✅ **Update Quantities**: Increment/decrement with +/- buttons
- ✅ **Delete Items**: Remove items with confirmation
- ✅ **Expiry Tracking**: Visual warnings for expiring items
- ✅ **Category Organization**: Items grouped by category
- ✅ **Loading States**: Smooth UX with loading indicators
- ✅ **Error Handling**: User-friendly error messages
- ✅ **Toast Notifications**: Success/error feedback

### UI Components
```typescript
// Key React components
- KitchenInventory.tsx     // Main inventory management
- api.ts                   // API service layer
- useInventory.ts          // React Query hooks
- Header.tsx               // Navigation header
- Index.tsx                // Main page layout
```

## 🔧 Recent Updates & Fixes

### v1.1.0 - API Service Context Binding Fix
**Issue**: "this.request is not a function" error when adding items
**Fix**: Changed class methods to arrow functions for proper `this` binding

```typescript
// Before (broken)
async createInventoryItem(item) { ... }

// After (fixed)  
createInventoryItem = async (item) => { ... }
```

### v1.0.0 - Initial Full Stack Integration
- ✅ Backend API server with Express.js
- ✅ MongoDB connection with Mongoose
- ✅ Frontend React Query integration
- ✅ CORS configuration
- ✅ Real-time UI updates
- ✅ Complete CRUD operations

## 🧪 Testing

### Manual Testing Checklist
```bash
# Backend tests
□ curl http://localhost:3001/api/health
□ curl http://localhost:3001/api/inventory
□ Add item via curl POST request
□ Update item quantity via curl PATCH
□ Delete item via curl DELETE

# Frontend tests  
□ Open http://localhost:8080
□ Expand inventory sidebar (chef hat icon)
□ Add new inventory item
□ Update item quantities with +/- buttons
□ Delete items with X button
□ Check expiry date warnings
□ Verify real-time updates
```

### Expected Behavior
1. **Adding Items**: Form clears, item appears in list, success toast
2. **Updating Quantities**: Immediate UI update, database sync
3. **Deleting Items**: Item disappears, confirmation toast
4. **Expiry Warnings**: Red "Expired" or orange "Soon" badges
5. **Loading States**: Buttons show "Adding..." during operations

## 🚨 Troubleshooting

### Common Issues

**Backend not starting**
```bash
# Check if MongoDB is running
brew services list | grep mongodb
# OR
sudo systemctl status mongod

# Check port availability
lsof -i :3001
```

**Frontend API connection failed**
```bash
# Verify backend is running
curl http://localhost:3001/api/health

# Check browser console for CORS errors
# Check Network tab in DevTools
```

**Database connection issues**
```bash
# Verify MongoDB connection
mongo --eval "db.stats()"

# Check environment variables
cat backend/.env
```

## 📈 Future Enhancements

### Planned Features
- [ ] User authentication system
- [ ] Multi-user inventory sharing
- [ ] Barcode scanning integration
- [ ] Recipe suggestions based on inventory
- [ ] Low stock email alerts
- [ ] Inventory analytics dashboard
- [ ] Export/import functionality
- [ ] Mobile app (React Native)

### Technical Improvements
- [ ] API rate limiting
- [ ] Database indexing optimization
- [ ] Redis caching layer
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Unit and integration tests
- [ ] API documentation with Swagger

## 🌐 Production Deployment

### Backend Deployment (Recommended: Railway/Render)
```bash
# Environment variables needed:
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/kitchen-inventory
PORT=8080
NODE_ENV=production
```

### Frontend Deployment (Recommended: Vercel/Netlify)
```bash
# Update API base URL in src/services/api.ts
const API_BASE_URL = 'https://your-backend-domain.com/api';

# Build for production
npm run build
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review browser console errors
3. Verify all services are running on correct ports
4. Check MongoDB connection and data

---

## ✅ Current Status

- 🟢 **Backend API**: Running on http://localhost:3001
- 🟢 **Frontend**: Running on http://localhost:8080  
- 🟢 **Database**: MongoDB connected on port 27017
- 🟢 **Integration**: Full CRUD operations working
- 🟢 **Real-time Sync**: React Query managing state
- 🟢 **Error Handling**: Proper user feedback
- 🟢 **UI/UX**: Responsive design with loading states

**System is fully operational and ready for use! 🎉**
