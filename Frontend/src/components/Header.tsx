import { useState } from 'react';
import { Search, ShoppingCart, User, Menu, Image, Mic, Camera } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Link } from 'react-router-dom';

export const Header = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [cartCount] = useState(3);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-white shadow-soft border-b">
      <div className="container mx-auto px-4">
        {/* Top Bar */}
        <div className="flex items-center justify-between py-2 text-sm border-b border-border">
          <div className="flex items-center space-x-6">
            <span className="text-muted-foreground">Save More on App</span>
            <span className="text-muted-foreground">Become a Seller</span>
            <span className="text-muted-foreground">Help & Support</span>
          </div>
          <div className="flex items-center space-x-4">
            <Link to="/orders" className="text-muted-foreground hover:text-primary">
              Track Orders
            </Link>
            <Button variant="ghost" size="sm">Login</Button>
            <Button variant="ghost" size="sm">Sign Up</Button>
          </div>
        </div>

        {/* Main Header */}
        <div className="flex items-center justify-between py-4">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-gradient-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">T</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                TitanStore
              </h1>
              <span className="text-xs text-accent font-medium">AI Powered</span>
            </div>
          </Link>

          {/* AI Chat Bar */}
          <div className="flex-1 max-w-2xl mx-8">
            <div className="relative">
              <div className={`absolute left-3 z-10 transition-all duration-200 ${isSearchFocused || searchQuery ? 'top-4' : 'top-1/2 transform -translate-y-1/2'}`}>
                <Search className="h-5 w-5 text-muted-foreground" />
              </div>
              <Textarea
                placeholder="Ask AI anything - describe what you need..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchExpanded(e.target.value.length > 0);
                }}
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setIsSearchFocused(false)}
                className={`pl-10 pr-24 py-3 text-base border-2 border-accent/20 focus:border-accent rounded-xl shadow-soft resize-none transition-all duration-300 ${
                  isSearchFocused || isSearchExpanded || searchQuery 
                    ? 'min-h-[80px]' 
                    : 'min-h-[48px] overflow-hidden'
                }`}
                rows={isSearchFocused || isSearchExpanded || searchQuery ? 3 : 1}
              />
              <div className={`absolute right-2 z-10 flex space-x-1 transition-all duration-200 ${isSearchFocused || searchQuery ? 'top-3' : 'top-1/2 transform -translate-y-1/2'}`}>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0 hover:bg-accent/10">
                  <Camera className="h-4 w-4 text-accent" />
                </Button>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0 hover:bg-accent/10">
                  <Image className="h-4 w-4 text-accent" />
                </Button>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0 hover:bg-accent/10">
                  <Mic className="h-4 w-4 text-accent" />
                </Button>
              </div>
            </div>
            <div className={`transition-all duration-200 text-xs text-muted-foreground ml-10 ${isSearchFocused || searchQuery ? 'mt-2 opacity-100' : 'mt-1 opacity-70'}`}>
              ✨ AI will help you find exactly what you're looking for
            </div>
          </div>

          {/* Right Menu */}
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="sm" className="flex items-center space-x-1">
              <User className="h-4 w-4" />
              <span className="hidden md:inline">Account</span>
            </Button>
            
            <Button variant="ghost" size="sm" className="relative flex items-center space-x-1">
              <ShoppingCart className="h-5 w-5" />
              <span className="hidden md:inline">Cart</span>
              {cartCount > 0 && (
                <Badge className="absolute -top-2 -right-2 h-5 w-5 text-xs bg-gradient-primary border-0">
                  {cartCount}
                </Badge>
              )}
            </Button>

            <Button variant="ghost" size="sm" className="md:hidden">
              <Menu className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};