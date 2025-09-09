import { useEffect, useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  ArrowLeft,
  Package,
  Store,
  Clock,
  CreditCard,
  CheckCircle,
  AlertCircle,
  Trash2,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Header } from '@/components/Header';

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

const OrderPlacement = () => {
  const location = useLocation();
  const { toast } = useToast();

  const inbound = (location.state ?? null) as Partial<OPCache> | null;

  // Page data + query (from navigation state or restored from sessionStorage)
  const [data, setData] = useState<SearchResults | null>(inbound?.searchResults ?? null);
  const [query, setQuery] = useState<string>(inbound?.originalQuery ?? '');
  // Mutable list for remove action
  const [items, setItems] = useState<OptimizedItem[]>(
    inbound?.searchResults?.optimized_items ?? []
  );

  // Cache/restore results & seed items list
  useEffect(() => {
    if (inbound?.searchResults && inbound?.originalQuery) {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ searchResults: inbound.searchResults, originalQuery: inbound.originalQuery })
      );
      setData(inbound.searchResults);
      setQuery(inbound.originalQuery);
      setItems(inbound.searchResults.optimized_items);
    } else if (!data) {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as OPCache;
        setData(parsed.searchResults);
        setQuery(parsed.originalQuery);
        setItems(parsed.searchResults.optimized_items);
      }
    }
  }, [location.key]); // run on route entry changes

  const handleConfirmOrder = () => {
    toast({
      title: 'Order functionality coming soon!',
      description: 'The order confirmation feature will be implemented next.',
    });
  };

  const formatPrice = (price: number) =>
    new Intl.NumberFormat('en-LK', {
      style: 'currency',
      currency: 'LKR',
      minimumFractionDigits: 2,
    }).format(price);

  // Derive a stable domain from source_url; fallback to website
  const storeDomain = (item: OptimizedItem) => {
    try {
      return new URL(item.source_url).hostname.replace(/^www\./, '').toLowerCase();
    } catch {
      return (item.website || '').toLowerCase();
    }
  };

  const getStoreColor = (domain: string) => {
    const colors: Record<string, string> = {
      'glowmark.lk': 'bg-blue-100 text-blue-800',
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

  const removeItemAt = (idx: number) => {
    setItems((prev) => prev.filter((_, i) => i !== idx));
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
  const subtotalTotal = items.reduce((sum, it) => sum + it.price_lkr, 0);

  return (
    <div className="min-h-screen bg-background">

      <div className="container mx-auto px-4 py-8">
        {/* Header Section */}
        <div className="flex items-center space-x-4 mb-8">
          {/*<Link to="/">*/}
          {/*  <Button variant="outline" size="sm">*/}
          {/*    <ArrowLeft className="h-4 w-4 mr-2" />*/}
          {/*    Back to Search*/}
          {/*  </Button>*/}
          {/*</Link>*/}
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
                    <div className="text-2xl font-bold text-green-600">{data.total_items_found}</div>
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
                                    {formatPrice(item.price_lkr)}
                                  </div>
                                  <div className="text-sm text-muted-foreground">per item</div>

                                  <div className="mt-3 flex items-center justify-end">
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="rounded-full"
                                      onClick={() => removeItemAt(index)}
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
                      Subtotal ({subtotalCount} {subtotalCount === 1 ? 'item' : 'items'})
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
                    disabled={subtotalCount === 0}
                  >
                    Confirm Order
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