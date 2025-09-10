import { Link } from "react-router-dom";
import { 
  Facebook, 
  Twitter, 
  Instagram, 
  Linkedin, 
  Mail, 
  Phone, 
  MapPin, 
  CreditCard, 
  Truck, 
  Shield, 
  Clock,
  Heart,
  Zap
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";

export const Footer = () => {
  return (
    <footer className="bg-gradient-to-br from-slate-50 to-slate-100 border-t border-border mt-16">
      {/* Newsletter Section */}
      <div className="bg-gradient-primary text-white py-12">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <div className="flex items-center justify-center mb-4">
              <Zap className="h-8 w-8 mr-3" />
              <h3 className="text-2xl font-bold">Stay Connected with TitanStore</h3>
            </div>
            <p className="text-lg mb-6 opacity-90">
              Get exclusive deals, AI-powered recommendations, and be the first to know about new features
            </p>
            <div className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <Input 
                placeholder="Enter your email address" 
                className="bg-white/10 border-white/20 text-white placeholder:text-white/70 focus:bg-white/20"
              />
              <Button variant="secondary" className="bg-white text-primary hover:bg-white/90">
                Subscribe
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Footer Content */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Company Info */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-gradient-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">T</span>
              </div>
              <div>
                <h3 className="text-xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                  TitanStore
                </h3>
                <span className="text-xs text-accent font-medium">AI Powered</span>
              </div>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Your intelligent shopping companion powered by advanced AI technology. 
              Discover, compare, and purchase the best products with personalized recommendations.
            </p>
            <div className="flex space-x-3">
              <Button variant="ghost" size="icon" className="h-9 w-9 hover:bg-primary/10">
                <Facebook className="h-4 w-4 text-primary" />
              </Button>
              <Button variant="ghost" size="icon" className="h-9 w-9 hover:bg-primary/10">
                <Twitter className="h-4 w-4 text-primary" />
              </Button>
              <Button variant="ghost" size="icon" className="h-9 w-9 hover:bg-primary/10">
                <Instagram className="h-4 w-4 text-primary" />
              </Button>
              <Button variant="ghost" size="icon" className="h-9 w-9 hover:bg-primary/10">
                <Linkedin className="h-4 w-4 text-primary" />
              </Button>
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-foreground">Quick Links</h4>
            <div className="space-y-2">
              <Link to="/" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Home
              </Link>
              <Link to="/orders" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                My Orders
              </Link>
              <Link to="/inventory" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Kitchen Inventory
              </Link>
              <Link to="/profile" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                My Profile
              </Link>
              <Link to="/cart" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Shopping Cart
              </Link>
              <Link to="/wishlist" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Wishlist
              </Link>
            </div>
          </div>

          {/* Customer Service */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-foreground">Customer Service</h4>
            <div className="space-y-2">
              <Link to="/help" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Help Center
              </Link>
              <Link to="/contact" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Contact Us
              </Link>
              <Link to="/returns" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Returns & Refunds
              </Link>
              <Link to="/shipping" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Shipping Info
              </Link>
              <Link to="/faq" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                FAQ
              </Link>
              <Link to="/size-guide" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Size Guide
              </Link>
            </div>
          </div>

          {/* Contact Info */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-foreground">Get in Touch</h4>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <Phone className="h-4 w-4 text-primary flex-shrink-0" />
                <span className="text-sm text-muted-foreground">+1 (555) 123-4567</span>
              </div>
              <div className="flex items-center space-x-3">
                <Mail className="h-4 w-4 text-primary flex-shrink-0" />
                <span className="text-sm text-muted-foreground">support@titanstore.com</span>
              </div>
              <div className="flex items-center space-x-3">
                <MapPin className="h-4 w-4 text-primary flex-shrink-0" />
                <span className="text-sm text-muted-foreground">
                  123 AI Street, Tech Valley<br />
                  San Francisco, CA 94105
                </span>
              </div>
              <div className="flex items-center space-x-3">
                <Clock className="h-4 w-4 text-primary flex-shrink-0" />
                <span className="text-sm text-muted-foreground">
                  24/7 AI Support Available
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Separator className="mx-4" />

      {/* Features Section */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="flex items-center space-x-3 p-4 rounded-lg bg-white/50">
            <Truck className="h-8 w-8 text-primary" />
            <div>
              <h5 className="font-semibold text-sm">Free Shipping</h5>
              <p className="text-xs text-muted-foreground">On orders over $50</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 p-4 rounded-lg bg-white/50">
            <Shield className="h-8 w-8 text-primary" />
            <div>
              <h5 className="font-semibold text-sm">Secure Payment</h5>
              <p className="text-xs text-muted-foreground">100% protected</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 p-4 rounded-lg bg-white/50">
            <Heart className="h-8 w-8 text-primary" />
            <div>
              <h5 className="font-semibold text-sm">Easy Returns</h5>
              <p className="text-xs text-muted-foreground">30-day return policy</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 p-4 rounded-lg bg-white/50">
            <Zap className="h-8 w-8 text-primary" />
            <div>
              <h5 className="font-semibold text-sm">AI Powered</h5>
              <p className="text-xs text-muted-foreground">Smart recommendations</p>
            </div>
          </div>
        </div>
      </div>

      <Separator className="mx-4" />

      {/* Bottom Footer */}
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <div className="flex flex-col md:flex-row items-center space-y-2 md:space-y-0 md:space-x-6">
            <p className="text-sm text-muted-foreground">
              © 2025 TitanStore. All rights reserved.
            </p>
            <div className="flex space-x-4">
              <Link to="/privacy" className="text-xs text-muted-foreground hover:text-primary transition-colors">
                Privacy Policy
              </Link>
              <Link to="/terms" className="text-xs text-muted-foreground hover:text-primary transition-colors">
                Terms of Service
              </Link>
              <Link to="/cookies" className="text-xs text-muted-foreground hover:text-primary transition-colors">
                Cookie Policy
              </Link>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <span className="text-xs text-muted-foreground">We accept:</span>
            <div className="flex space-x-2">
              <div className="w-8 h-5 bg-gradient-to-r from-blue-600 to-blue-700 rounded flex items-center justify-center">
                <CreditCard className="h-3 w-3 text-white" />
              </div>
              <div className="w-8 h-5 bg-gradient-to-r from-red-600 to-red-700 rounded flex items-center justify-center">
                <CreditCard className="h-3 w-3 text-white" />
              </div>
              <div className="w-8 h-5 bg-gradient-to-r from-green-600 to-green-700 rounded flex items-center justify-center">
                <CreditCard className="h-3 w-3 text-white" />
              </div>
              <div className="w-8 h-5 bg-gradient-to-r from-purple-600 to-purple-700 rounded flex items-center justify-center">
                <CreditCard className="h-3 w-3 text-white" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};
