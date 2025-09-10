import { useState, useEffect } from 'react';
import { Search, ShoppingCart, User, Menu, Image, Mic, Camera, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Link, useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';

export const Header = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [cartCount] = useState(3);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  
  // Scroll-based header visibility
  const [isHeaderVisible, setIsHeaderVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  
  const navigate = useNavigate();
  const { toast } = useToast();

  // Scroll detection effect
  useEffect(() => {
    const controlHeaderVisibility = () => {
      const currentScrollY = window.scrollY;
      const scrollThreshold = 80; // Minimum scroll distance to trigger hide/show
      const scrollDelta = Math.abs(currentScrollY - lastScrollY);
      
      // Only react to significant scroll movements
      if (scrollDelta < 10) return;
      
      if (currentScrollY > lastScrollY && currentScrollY > scrollThreshold) {
        // Scrolling down - hide header
        setIsHeaderVisible(false);
      } else if (currentScrollY < lastScrollY || currentScrollY <= scrollThreshold) {
        // Scrolling up or near top - show header
        setIsHeaderVisible(true);
      }
      
      setLastScrollY(currentScrollY);
    };

    const throttledScrollHandler = throttle(controlHeaderVisibility, 50);
    
    window.addEventListener('scroll', throttledScrollHandler, { passive: true });
    return () => window.removeEventListener('scroll', throttledScrollHandler);
  }, [lastScrollY]);

  // Throttle function to limit scroll event firing
  const throttle = (func: Function, delay: number) => {
    let timeoutId: NodeJS.Timeout | null = null;
    let lastExecTime = 0;
    
    return function (...args: any[]) {
      const currentTime = Date.now();
      
      if (currentTime - lastExecTime > delay) {
        func(...args);
        lastExecTime = currentTime;
      } else {
        if (timeoutId) clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          func(...args);
          lastExecTime = Date.now();
        }, delay - (currentTime - lastExecTime));
      }
    };
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast({
        title: "Search query required",
        description: "Please enter what you're looking for",
        variant: "destructive",
      });
      return;
    }

    setIsSearching(true);
    console.log('🔍 Starting search for:', searchQuery);
    
    try {
      console.log('📡 Making API request to:', 'http://localhost:3004/api/search');
      
      const response = await fetch('http://localhost:3004/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: searchQuery }),
      });

      console.log('📦 Response status:', response.status);
      console.log('📦 Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Search response:', data);
      
      if (data.status === 'success') {
        console.log('🚀 Navigating to order placement with results:', data.results);
        // Navigate to order placement page with results
        navigate('/order-placement', { 
          state: { 
            searchResults: data.results, 
            originalQuery: searchQuery 
          } 
        });
        
        toast({
          title: "Search completed!",
          description: `Found ${data.results.items_count} optimized items`,
        });
      } else {
        console.error('❌ API returned error:', data.message);
        toast({
          title: "Search failed",
          description: data.message || "An error occurred during search",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('❌ Search error:', error);
      toast({
        title: "Connection error",
        description: "Unable to connect to search service. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <header className={`header-auto-hide ${isHeaderVisible ? 'visible' : 'hidden'}`}>
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
            <div className={`relative ai-search-container ${isSearchFocused || isSearchExpanded || searchQuery ? 'active' : ''}`}>
              {/* Neural network background pattern */}
              <div className="ai-neural-bg"></div>
              
              {/* Floating sparkles */}
              <div className="ai-sparkle"></div>
              <div className="ai-sparkle"></div>
              <div className="ai-sparkle"></div>
              <div className="ai-sparkle"></div>
              <div className="ai-sparkle"></div>
              <div className="ai-sparkle"></div>
              
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
                onKeyPress={handleKeyPress}
                disabled={isSearching}
                className={`ai-search-input ${isSearchFocused || isSearchExpanded || searchQuery ? 'active' : ''} pl-10 pr-32 py-3 text-base border-2 border-accent/20 focus:border-accent rounded-xl shadow-soft resize-none transition-all duration-300 ${
                  isSearchFocused || isSearchExpanded || searchQuery 
                    ? 'min-h-[80px]' 
                    : 'min-h-[48px] overflow-hidden'
                } ${isSearching ? 'opacity-75' : ''}`}
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
                <Button 
                  onClick={handleSearch}
                  disabled={isSearching || !searchQuery.trim()}
                  size="sm" 
                  className="h-8 bg-gradient-primary text-white hover:opacity-90 disabled:opacity-50"
                >
                  {isSearching ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
            <div className={`transition-all duration-200 text-xs text-muted-foreground ml-10 ${isSearchFocused || searchQuery ? 'mt-2 opacity-100' : 'mt-1 opacity-70'}`}>
              <span className={`${isSearchFocused ? 'text-accent font-medium' : ''} transition-all duration-300`}>
                ✨ {isSearching ? (
                  <span className="animate-pulse">🤖 AI is analyzing your request...</span>
                ) : isSearchFocused ? (
                  <span>🧠 Advanced AI ready to find your perfect items</span>
                ) : (
                  'AI will help you find exactly what you\'re looking for'
                )}
              </span>
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