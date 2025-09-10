import { useEffect, useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import {
  ArrowLeft,
  Package,
  Store,
  Clock,
  CreditCard,
  CheckCircle,
  AlertCircle,
  Trash2,
  Loader2,
  Plus,
  Minus,
  Search,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface OptimizedItem {
  title: string;
  price_lkr: number;
  website: string;
  source_url: string;
  collection: string;
  similarity_score: number;
  kg_enhanced: boolean;
  original_query: string;
  image_url?: string;
  quantity?: number; // Add quantity field
  // Optional fields your backend can accept if present
  item_id?: string;
  brand?: string;
  category?: string;
  delivery_hours?: number;
  tags?: string[];
}

interface SearchResults {
  optimized_items: OptimizedItem[];
  total_cost: number;
  budget_used_percentage: number;
  estimated_delivery_hours: number;
  items_count: number;
  stores_used: string[];
  optimization_method: string;
  keywords_processed: string[];
  total_items_found: number;
  pipeline_summary: {
    keywords_extracted: number;
    items_acquired: number;
    items_personalized: number;
    items_after_logistics: number;
    loyalty_savings: number;
    final_selection: number;
  };
}

const STORAGE_KEY = 'op_cache';
type OPCache = { searchResults: SearchResults; originalQuery: string };

// === NEW: config helpers ===
const FEEDBACK_URL = 'http://127.0.0.1:3004/api/feedback'; // or 'http://127.0.0.1:3004/api/feedback' without a dev proxy
const getUserId = () => localStorage.getItem('user_id') || 'default_user';

const OrderPlacement = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();

  const inbound = (location.state ?? null) as Partial<OPCache> | null;

  // Page data + query (from navigation state or restored from sessionStorage)
  const [data, setData] = useState<SearchResults | null>(inbound?.searchResults ?? null);
  const [query, setQuery] = useState<string>(inbound?.originalQuery ?? '');
  // Mutable list for remove action
  const [items, setItems] = useState<OptimizedItem[]>(
    (inbound?.searchResults?.optimized_items ?? []).map(item => ({
      ...item,
      quantity: item.quantity || 1
    }))
  );
  
  // Loading state for order processing
  const [isProcessingOrder, setIsProcessingOrder] = useState(false);

  // Additional search functionality state
  const [additionalQuery, setAdditionalQuery] = useState('');
  const [isSearchingMore, setIsSearchingMore] = useState(false);
  const [showAddMoreSection, setShowAddMoreSection] = useState(false);

  // Cache/restore results & seed items list
  useEffect(() => {
    if (inbound?.searchResults && inbound?.originalQuery) {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ searchResults: inbound.searchResults, originalQuery: inbound.originalQuery })
      );
      setData(inbound.searchResults);
      setQuery(inbound.originalQuery);
      setItems(inbound.searchResults.optimized_items.map(item => ({
        ...item,
        quantity: item.quantity || 1
      })));
    } else if (!data) {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as OPCache;
        setData(parsed.searchResults);
        setQuery(parsed.originalQuery);
        setItems(parsed.searchResults.optimized_items.map(item => ({
          ...item,
          quantity: item.quantity || 1
        })));
      }
    }
  }, [location.key]); // run on route entry changes

  const handleConfirmOrder = async () => {
    if (subtotalCount === 0) {
      toast({
        title: 'No items to order',
        description: 'Please add items to your cart before confirming.',
        variant: 'destructive',
      });
      return;
    }

    // Set loading state
    setIsProcessingOrder(true);

    // Group items by store
    const itemsByStore = items.reduce((acc, item) => {
      const storeDomain = getStoreDomain(item);
      if (!acc[storeDomain]) {
        acc[storeDomain] = [];
      }
      acc[storeDomain].push(item);
      return acc;
    }, {} as Record<string, OptimizedItem[]>);

    console.log('🛒 Items grouped by store:', itemsByStore);
    console.log('🏪 Store domains:', Object.keys(itemsByStore));

    // Show loading state
    toast({
      title: 'Placing orders...',
      description: 'Processing your order with multiple stores.',
    });

    const orderResults: Array<{ store: string; success: boolean; error?: string }> = [];

    // Process orders for each store
    for (const [store, storeItems] of Object.entries(itemsByStore)) {
      try {
        const orderData = {
          userId: `test-user-123`, // Generate unique user ID
          items: storeItems.map((item, index) => {
            // If price is 0, use default price of 500
            const price = item.price_lkr === 0 ? 500 : item.price_lkr;
            
            const orderItem = {
              productId: `${getStorePrefix(store)}${String(index + 1).padStart(3, '0')}`,
              title: item.title,
              price: price, // Use corrected price
              quantity: item.quantity || 1, // Use actual quantity from item
              // Additional fields for reference
              source_url: item.source_url,
              collection: item.collection,
            };
            console.log(`📋 Order item for ${store}:`, orderItem);
            console.log(`   - productId: "${orderItem.productId}" (${typeof orderItem.productId})`);
            console.log(`   - title: "${orderItem.title}" (${typeof orderItem.title})`);
            console.log(`   - price: ${orderItem.price} (${typeof orderItem.price}) ${item.price_lkr === 0 ? '[CORRECTED FROM 0]' : ''}`);
            console.log(`   - quantity: ${orderItem.quantity} (${typeof orderItem.quantity})`);
            return orderItem;
          }),
        };

        console.log(`📦 Sending order to ${store}:`, orderData);

        // Send order to the appropriate store endpoint
        const response = await fetch(`http://localhost:3005/api/orders/${store}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(orderData),
        });

        if (response.ok) {
          const result = await response.json();
          orderResults.push({ store, success: true });
          console.log(`✅ Order placed successfully with ${store}:`, result);
        } else {
          const errorData = await response.json();
          orderResults.push({ 
            store, 
            success: false, 
            error: errorData.message || 'Failed to place order' 
          });
          console.error(`❌ Failed to place order with ${store}:`, errorData);
        }
      } catch (error) {
        orderResults.push({ 
          store, 
          success: false, 
          error: error instanceof Error ? error.message : 'Network error' 
        });
        console.error(`❌ Error placing order with ${store}:`, error);
      }
    }

    // Show results
    const successfulOrders = orderResults.filter(result => result.success);
    const failedOrders = orderResults.filter(result => !result.success);

    if (successfulOrders.length > 0 && failedOrders.length === 0) {
      // All orders successful
      toast({
        title: 'All orders placed successfully! 🎉',
        description: `Orders placed with ${successfulOrders.length} store${successfulOrders.length > 1 ? 's' : ''}: ${successfulOrders.map(r => r.store).join(', ')}. Redirecting to orders page...`,
      });
      
      // Navigate to orders page after a short delay
      setTimeout(() => {
        navigate('/orders');
      }, 2000);
      
    } else if (successfulOrders.length > 0 && failedOrders.length > 0) {
      // Partial success
      toast({
        title: 'Some orders placed successfully',
        description: `✅ Success: ${successfulOrders.map(r => r.store).join(', ')}. ❌ Failed: ${failedOrders.map(r => r.store).join(', ')}. Redirecting to orders page...`,
        variant: 'destructive',
      });
      
      // Navigate to orders page after a short delay even with partial success
      setTimeout(() => {
        navigate('/orders');
      }, 3000);
      
    } else {
      // All orders failed
      toast({
        title: 'Failed to place orders',
        description: `All orders failed. Please try again later.`,
        variant: 'destructive',
      });
    }
    
    // Reset loading state
    setIsProcessingOrder(false);
  };

  // Helper function to get store domain
  const getStoreDomain = (item: OptimizedItem): string => {
    try {
      const domain = new URL(item.source_url).hostname.replace(/^www\./, '').toLowerCase();
      // Map to our API endpoint names
      if (domain.includes('onlinekade')) return 'onlinekade';
      if (domain.includes('kapruka')) return 'kapruka';
      if (domain.includes('glowmark') || domain.includes('glomark')) return 'glowmark';
      return domain.replace('.lk', '').replace('.com', '');
    } catch {
      const website = (item.website || item.collection || '').toLowerCase();
      if (website.includes('onlinekade')) return 'onlinekade';
      if (website.includes('kapruka')) return 'kapruka';
      if (website.includes('glowmark') || website.includes('glomark')) return 'glowmark';
      return website;
    }
  };

  // Helper function to get store prefix for product IDs
  const getStorePrefix = (store: string): string => {
    const prefixes: Record<string, string> = {
      'onlinekade': 'OLK',
      'kapruka': 'KAP',
      'glowmark': 'GLW',
      'glomark': 'GLW',
    };
    return prefixes[store] || 'GEN';
  };

  const formatPrice = (price: number) =>
    new Intl.NumberFormat('en-LK', {
      style: 'currency',
      currency: 'LKR',
      minimumFractionDigits: 2,
    }).format(price);

  // Derive a stable domain from source_url; fallback to website
  const storeDomain = (item: OptimizedItem) => {
    return getStoreDomain(item);
  };

  const getStoreColor = (domain: string) => {
    const colors: Record<string, string> = {
      'glomark.lk': 'bg-blue-100 text-blue-800',
      'kapruka.com': 'bg-green-100 text-green-800',
      'onlinekade.lk': 'bg-purple-100 text-purple-800',
      'lassanaflora.com': 'bg-pink-100 text-pink-800',
    };
    return colors[domain] || 'bg-gray-100 text-gray-800';
  };

  // Safe inline SVG fallback for broken/missing images
  const FALLBACK_IMG =
    'data:image/svg+xml;utf8,' +
    encodeURIComponent(
      `<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80"><rect width="100%" height="100%" fill="#eee"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="10" fill="#666">No Image</text></svg>`
    );

  // === NEW: send dislike feedback ===
  const sendDislikeFeedback = async (item: OptimizedItem, position: number) => {
    const payload = {
      user_id: getUserId(),
      action: 'dislike',
      query: query || item.original_query || '',
      impression_id: (window.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`),
      position, // 1-based
      // rating is optional; omit for dislike
      item: {
        // Provide whatever you have; backend treats many as optional
        item_id: item.item_id || item.source_url || item.title,
        title: item.title,
        brand: item.brand, // may be undefined
        store: storeDomain(item) || item.website,
        category: item.category, // may be undefined
        price_lkr: item.price_lkr,
        delivery_hours: item.delivery_hours, // may be undefined
        tags: item.tags ?? [
          item.collection ? `collection:${item.collection}` : undefined,
          item.kg_enhanced ? 'ai-enhanced' : undefined,
          item.website ? `site:${item.website}` : undefined,
        ].filter(Boolean) as string[],
      },
    };

    const res = await fetch(FEEDBACK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.message || `Feedback failed with ${res.status}`);
    }
  };

  // === UPDATED: remove + feedback ===
  const removeItemAt = async (idx: number, item: OptimizedItem) => {
    // optimistic UI update
    setItems((prev) => prev.filter((_, i) => i !== idx));

    try {
      await sendDislikeFeedback(item, idx + 1);
      toast({
        title: 'Removed',
        description: 'Thanks! We’ll learn from this and improve future picks.',
      });
    } catch (e: any) {
      // non-fatal; keep item removed
      toast({
        title: 'Feedback failed',
        description: e?.message || 'Could not record your feedback.',
        variant: 'destructive',
      });
    }
  };

  // Quantity control functions
  const increaseQuantity = (index: number) => {
    setItems(prev => prev.map((item, i) => 
      i === index ? { ...item, quantity: (item.quantity || 1) + 1 } : item
    ));
  };

  const decreaseQuantity = (index: number) => {
    setItems(prev => prev.map((item, i) => 
      i === index && (item.quantity || 1) > 1 
        ? { ...item, quantity: (item.quantity || 1) - 1 } 
        : item
    ));
  };

  const updateQuantity = (index: number, newQuantity: number) => {
    if (newQuantity < 1) return;
    setItems(prev => prev.map((item, i) => 
      i === index ? { ...item, quantity: newQuantity } : item
    ));
  };

  // Function to search for additional items
  const searchAdditionalItems = async () => {
    if (!additionalQuery.trim()) {
      toast({
        title: "Search query required",
        description: "Please enter what you're looking for",
        variant: "destructive",
      });
      return;
    }

    setIsSearchingMore(true);
    console.log('🔍 Searching for additional items:', additionalQuery);

    try {
      const response = await fetch('http://localhost:3004/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: additionalQuery }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const searchData = await response.json();
      console.log('✅ Additional search response:', searchData);

      if (searchData.status === 'success') {
        // Add new items to existing items
        const newItems = searchData.results.optimized_items.map((item: OptimizedItem) => ({
          ...item,
          quantity: 1, // Default quantity for new items
          original_query: additionalQuery // Track which query this item came from
        }));

        setItems(prev => [...prev, ...newItems]);
        
        // Update the data object to include new items
        setData(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            optimized_items: [...prev.optimized_items, ...searchData.results.optimized_items],
            pipeline_summary: {
              ...prev.pipeline_summary,
              items_acquired: prev.pipeline_summary.items_acquired + searchData.results.optimized_items.length
            }
          };
        });

        toast({
          title: "Additional items found!",
          description: `Added ${searchData.results.optimized_items.length} new items to your order`,
        });

        // Clear the search input and hide the section
        setAdditionalQuery('');
        setShowAddMoreSection(false);
      } else {
        console.error('❌ API returned error:', searchData.message);
        toast({
          title: "Search failed",
          description: searchData.message || "Unable to find additional items",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('❌ Search request failed:', error);
      toast({
        title: "Search failed",
        description: "Unable to connect to search service. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSearchingMore(false);
    }
  };

  if (!data) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center space-y-4">
            <AlertCircle className="h-16 w-16 text-muted-foreground mx-auto" />
            <h1 className="text-2xl font-bold">No Search Results</h1>
            <p className="text-muted-foreground">Please go back and search for products first.</p>
            <Link to="/">
              <Button>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Home
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Summary reflects current (possibly reduced) list
  const subtotalCount = items.length;
  const totalQuantity = items.reduce((sum, it) => sum + (it.quantity || 1), 0);
  // Calculate totals with corrected prices (0 -> 500) and quantities
  const subtotalTotal = items.reduce((sum, it) => sum + ((it.price_lkr === 0 ? 500 : it.price_lkr) * (it.quantity || 1)), 0);

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header Section */}
        <div className="flex items-center space-x-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold">Order Placement</h1>
            <p className="text-muted-foreground">Review your AI-optimized product selection</p>
          </div>
        </div>

        {/* Search Query Display */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className="bg-gradient-primary text-white">
                AI Search Query
              </Badge>
              <span className="font-medium">"{query}"</span>
            </div>
          </CardContent>
        </Card>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content - Product List */}
          <div className="lg:col-span-2 space-y-6">
            {/* Add More Items Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Search className="h-5 w-5" />
                    <span>Add More Items</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddMoreSection(!showAddMoreSection)}
                  >
                    {showAddMoreSection ? 'Hide' : 'Show'}
                  </Button>
                </CardTitle>
              </CardHeader>
              {showAddMoreSection && (
                <CardContent>
                  <div className="space-y-4">
                    <p className="text-sm text-muted-foreground">
                      Search for additional items to add to your order. The AI will find and optimize more products for you.
                    </p>
                    <div className="flex space-x-2">
                      <Input
                        placeholder="Search for more items (e.g., 'organic vegetables', 'dairy products')..."
                        value={additionalQuery}
                        onChange={(e) => setAdditionalQuery(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            searchAdditionalItems();
                          }
                        }}
                        className="flex-1"
                        disabled={isSearchingMore}
                      />
                      <Button 
                        onClick={searchAdditionalItems}
                        disabled={isSearchingMore || !additionalQuery.trim()}
                        className="bg-gradient-primary"
                      >
                        {isSearchingMore ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            Searching...
                          </>
                        ) : (
                          <>
                            <Search className="h-4 w-4 mr-2" />
                            Search
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>

            {/* Results Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Package className="h-5 w-5" />
                  <span>AI Optimization Results</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary">{data.items_count}</div>
                    <div className="text-sm text-muted-foreground">Optimized Items</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{data.pipeline_summary.items_acquired}</div>
                    <div className="text-sm text-muted-foreground">Items Found</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{data.stores_used.length}</div>
                    <div className="text-sm text-muted-foreground">Stores</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {Math.round(data.estimated_delivery_hours)}h
                    </div>
                    <div className="text-sm text-muted-foreground">Delivery</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Optimized Items */}
            <Card>
              <CardHeader>
                <CardTitle>Optimized Product Selection</CardTitle>
                <p className="text-sm text-muted-foreground">
                  These products were selected using {data.optimization_method} optimization
                </p>
              </CardHeader>
              <CardContent>
                {items.length > 0 ? (
                  <div className="space-y-4">
                    {items.map((item, index) => {
                      const domain = storeDomain(item);
                      const imgSrc = item.image_url || FALLBACK_IMG;
                      const key = item.source_url || `${domain}-${item.title}-${index}`;
                      return (
                        <div
                          key={key}
                          className="border rounded-xl p-4 hover:shadow-md transition-shadow"
                        >
                          <div className="flex gap-4">
                            {/* Thumbnail */}
                            <a
                              href={item.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block w-20 h-20 flex-shrink-0"
                              title="Open product page"
                            >
                              <img
                                src={imgSrc}
                                alt={item.title}
                                loading="lazy"
                                className="w-20 h-20 object-contain rounded-md bg-muted"
                                onError={(e) => {
                                  const img = e.currentTarget;
                                  img.onerror = null; // prevent loop
                                  img.src = FALLBACK_IMG;
                                }}
                              />
                            </a>

                            {/* Details + price + remove */}
                            <div className="flex-1">
                              <div className="flex justify-between items-start gap-4">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 mb-2">
                                    <h3 className="font-semibold text-lg">{item.title}</h3>
                                    {item.kg_enhanced && (
                                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                                        🧠 AI Enhanced
                                      </Badge>
                                    )}
                                  </div>

                                  <div className="flex items-center flex-wrap gap-3 text-sm text-muted-foreground">
                                    <div className="flex items-center gap-1">
                                      <Store className="h-4 w-4" />
                                      <Badge className={getStoreColor(domain)}>{domain || item.website}</Badge>
                                    </div>

                                    <a
                                      href={item.source_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="underline hover:no-underline"
                                    >
                                      View product
                                    </a>

                                    <div className="flex items-center gap-1">
                                      <CheckCircle className="h-4 w-4" />
                                      <span>Match: {Math.round(item.similarity_score * 100)}%</span>
                                    </div>
                                  </div>
                                </div>

                                <div className="text-right min-w-[180px]">
                                  <div className="text-2xl font-bold text-primary">
                                    {formatPrice(item.price_lkr === 0 ? 500 : item.price_lkr)}
                                    {item.price_lkr === 0 && (
                                      <span className="text-xs text-orange-600 ml-1"></span>
                                    )}
                                  </div>
                                  <div className="text-sm text-muted-foreground">per item</div>
                                  
                                  {/* Total price if quantity > 1 */}
                                  {(item.quantity || 1) > 1 && (
                                    <div className="text-lg font-semibold text-green-600 mt-1">
                                      Total: {formatPrice((item.price_lkr === 0 ? 500 : item.price_lkr) * (item.quantity || 1))}
                                    </div>
                                  )}

                                  {/* Quantity Controls */}
                                  <div className="mt-3 flex items-center justify-center gap-2">
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="h-8 w-8 p-0"
                                      onClick={() => decreaseQuantity(index)}
                                      disabled={(item.quantity || 1) <= 1}
                                    >
                                      <Minus className="h-4 w-4" />
                                    </Button>
                                    
                                    <div className="flex items-center gap-1 min-w-[60px] justify-center">
                                      <input
                                        type="number"
                                        min="1"
                                        max="99"
                                        value={item.quantity || 1}
                                        onChange={(e) => {
                                          const newQty = parseInt(e.target.value) || 1;
                                          updateQuantity(index, newQty);
                                        }}
                                        className="w-12 text-center text-sm border rounded px-1 py-1"
                                      />
                                      <span className="text-xs text-muted-foreground">qty</span>
                                    </div>
                                    
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="h-8 w-8 p-0"
                                      onClick={() => increaseQuantity(index)}
                                      disabled={(item.quantity || 1) >= 99}
                                    >
                                      <Plus className="h-4 w-4" />
                                    </Button>
                                  </div>

                                  <div className="mt-3 flex items-center justify-end">
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="rounded-full"
                                      onClick={() => removeItemAt(index, item)}
                                    >
                                      <Trash2 className="h-4 w-4 mr-1" />
                                      Remove
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Package className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Items Left</h3>
                    <p className="text-muted-foreground">
                      You removed all items. Go back and search again to repopulate.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Order Summary */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CreditCard className="h-5 w-5" />
                  <span>Order Summary</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>
                      Subtotal ({subtotalCount} {subtotalCount === 1 ? 'item' : 'items'}{totalQuantity > subtotalCount ? `, ${totalQuantity} total` : ''})
                    </span>
                    <span>{formatPrice(subtotalTotal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Loyalty Savings</span>
                    <span className="text-green-600">
                      -{formatPrice(data.pipeline_summary.loyalty_savings)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Delivery Fee</span>
                    <span className="text-green-600">FREE</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between text-lg font-bold">
                    <span>Total</span>
                    <span className="text-primary">
                      {formatPrice(subtotalTotal - data.pipeline_summary.loyalty_savings)}
                    </span>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-sm">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span>Estimated delivery: {Math.round(data.estimated_delivery_hours)} hours</span>
                  </div>

                  <Button
                    onClick={handleConfirmOrder}
                    className="w-full bg-gradient-primary hover:opacity-90"
                    disabled={subtotalCount === 0 || isProcessingOrder}
                  >
                    {isProcessingOrder && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                    {isProcessingOrder ? 'Processing Orders...' : 'Confirm Order'}
                  </Button>

                  <p className="text-xs text-muted-foreground text-center">
                    By confirming, you agree to our terms and conditions
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>AI Processing Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span>Keywords Extracted</span>
                    <Badge variant="outline">{data.pipeline_summary.keywords_extracted}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Items Acquired</span>
                    <Badge variant="outline">{data.pipeline_summary.items_acquired}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>After Personalization</span>
                    <Badge variant="outline">{data.pipeline_summary.items_personalized}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>After Logistics</span>
                    <Badge variant="outline">{data.pipeline_summary.items_after_logistics}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Final Selection</span>
                    <Badge className="bg-gradient-primary text-white">
                      {data.pipeline_summary.final_selection}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

// @ts-ignore
export default OrderPlacement;
