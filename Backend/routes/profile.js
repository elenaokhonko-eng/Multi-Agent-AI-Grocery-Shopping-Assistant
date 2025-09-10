const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const router = express.Router();

const PROFILES_DIR = path.join(__dirname, '..', '.profiles');
const DEFAULT_USER_FILE = path.join(PROFILES_DIR, 'default_user.json');

// Ensure profiles directory exists
const ensureProfilesDir = async () => {
  try {
    await fs.access(PROFILES_DIR);
  } catch (error) {
    await fs.mkdir(PROFILES_DIR, { recursive: true });
  }
};

// Get user profile
router.get('/user/:userId', async (req, res) => {
  try {
    const userId = req.params.userId || 'default_user';
    const profileFile = userId === 'default_user' ? DEFAULT_USER_FILE : path.join(PROFILES_DIR, `${userId}.json`);
    
    try {
      const profileData = await fs.readFile(profileFile, 'utf8');
      const profile = JSON.parse(profileData);
      res.json(profile);
    } catch (error) {
      // If file doesn't exist, return default profile
      const defaultProfile = {
        user_id: userId,
        budget_limit_lkr: 5000.0,
        location: "Colombo, Sri Lanka",
        dietary_needs: {
          vegetarian: false,
          vegan: false,
          gluten_free: false,
          dairy_free: false,
          organic_only: false,
          low_sodium: false,
          sugar_free: false,
          halal: false,
          kosher: false,
          allergies: []
        },
        brand_preferences: {
          preferred_brands: [],
          disliked_brands: [],
          premium_brands_only: false,
          local_brands_priority: false
        },
        household_inventory: {
          current_items: {},
          expiry_dates: {},
          low_stock_threshold: 2
        },
        loyalty_membership: {
          memberships: {},
          points_balance: {},
          preferred_stores: []
        },
        delivery_preferences: {
          max_delivery_time_hours: 24,
          max_delivery_radius_km: 10,
          preferred_time_slots: ["09:00-12:00", "14:00-18:00"],
          avoid_weekends: false
        },
        _saved_at: Date.now() / 1000
      };
      res.json(defaultProfile);
    }
  } catch (error) {
    console.error('Error getting user profile:', error);
    res.status(500).json({ error: 'Failed to get user profile' });
  }
});

// Get default user profile (without user ID)
router.get('/user', async (req, res) => {
  try {
    try {
      const profileData = await fs.readFile(DEFAULT_USER_FILE, 'utf8');
      const profile = JSON.parse(profileData);
      res.json(profile);
    } catch (error) {
      // If file doesn't exist, return default profile
      const defaultProfile = {
        user_id: 'default_user',
        budget_limit_lkr: 5000.0,
        location: "Colombo, Sri Lanka",
        dietary_needs: {
          vegetarian: false,
          vegan: false,
          gluten_free: false,
          dairy_free: false,
          organic_only: false,
          low_sodium: false,
          sugar_free: false,
          halal: false,
          kosher: false,
          allergies: []
        },
        brand_preferences: {
          preferred_brands: [],
          disliked_brands: [],
          premium_brands_only: false,
          local_brands_priority: false
        },
        household_inventory: {
          current_items: {},
          expiry_dates: {},
          low_stock_threshold: 2
        },
        loyalty_membership: {
          memberships: {},
          points_balance: {},
          preferred_stores: []
        },
        delivery_preferences: {
          max_delivery_time_hours: 24,
          max_delivery_radius_km: 10,
          preferred_time_slots: ["09:00-12:00", "14:00-18:00"],
          avoid_weekends: false
        },
        _saved_at: Date.now() / 1000
      };
      res.json(defaultProfile);
    }
  } catch (error) {
    console.error('Error getting default user profile:', error);
    res.status(500).json({ error: 'Failed to get user profile' });
  }
});

// Save/update user profile
router.post('/user/:userId', async (req, res) => {
  try {
    await ensureProfilesDir();
    
    const userId = req.params.userId || 'default_user';
    const profileFile = userId === 'default_user' ? DEFAULT_USER_FILE : path.join(PROFILES_DIR, `${userId}.json`);
    
    const profileData = {
      ...req.body,
      user_id: userId,
      _saved_at: Date.now() / 1000
    };
    
    // Validate required fields
    if (!profileData.budget_limit_lkr && profileData.budget_limit_lkr !== 0) {
      return res.status(400).json({ error: 'budget_limit_lkr is required' });
    }
    
    // Write profile to file
    await fs.writeFile(profileFile, JSON.stringify(profileData, null, 2), 'utf8');
    
    console.log(`Profile saved for user: ${userId}`);
    res.json({ 
      success: true, 
      message: 'Profile saved successfully',
      user_id: userId,
      saved_at: profileData._saved_at
    });
  } catch (error) {
    console.error('Error saving user profile:', error);
    res.status(500).json({ error: 'Failed to save user profile' });
  }
});

// Save/update default user profile (without user ID)
router.post('/user', async (req, res) => {
  try {
    await ensureProfilesDir();
    
    const profileData = {
      ...req.body,
      user_id: 'default_user',
      _saved_at: Date.now() / 1000
    };
    
    // Validate required fields
    if (!profileData.budget_limit_lkr && profileData.budget_limit_lkr !== 0) {
      return res.status(400).json({ error: 'budget_limit_lkr is required' });
    }
    
    // Write profile to file
    await fs.writeFile(DEFAULT_USER_FILE, JSON.stringify(profileData, null, 2), 'utf8');
    
    console.log('Default profile saved');
    res.json({ 
      success: true, 
      message: 'Profile saved successfully',
      user_id: 'default_user',
      saved_at: profileData._saved_at
    });
  } catch (error) {
    console.error('Error saving default user profile:', error);
    res.status(500).json({ error: 'Failed to save user profile' });
  }
});

// Delete user profile
router.delete('/user/:userId', async (req, res) => {
  try {
    const userId = req.params.userId;
    if (userId === 'default_user') {
      return res.status(400).json({ error: 'Cannot delete default user profile' });
    }
    
    const profileFile = path.join(PROFILES_DIR, `${userId}.json`);
    await fs.unlink(profileFile);
    
    res.json({ success: true, message: 'Profile deleted successfully' });
  } catch (error) {
    console.error('Error deleting user profile:', error);
    res.status(500).json({ error: 'Failed to delete user profile' });
  }
});

// List all user profiles
router.get('/users', async (req, res) => {
  try {
    await ensureProfilesDir();
    const files = await fs.readdir(PROFILES_DIR);
    const profiles = [];
    
    for (const file of files) {
      if (file.endsWith('.json')) {
        try {
          const filePath = path.join(PROFILES_DIR, file);
          const data = await fs.readFile(filePath, 'utf8');
          const profile = JSON.parse(data);
          profiles.push({
            user_id: profile.user_id,
            saved_at: profile._saved_at,
            file: file
          });
        } catch (error) {
          console.warn(`Error reading profile file ${file}:`, error);
        }
      }
    }
    
    res.json(profiles);
  } catch (error) {
    console.error('Error listing user profiles:', error);
    res.status(500).json({ error: 'Failed to list user profiles' });
  }
});

module.exports = router;
