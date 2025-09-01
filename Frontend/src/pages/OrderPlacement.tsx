import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ArrowLeft, Package, Store, Clock, CreditCard, CheckCircle, AlertCircle } from 'lucide-react';
import { Header } from '@/components/Header';
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

const OrderPlacement = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const searchResults = location.state?.searchResults as SearchResults;
  const originalQuery = location.state?.originalQuery as string;

  if (!searchResults) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
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

  const handleConfirmOrder = () => {
    toast({
      title: "Order functionality coming soon!",
      description: "The order confirmation feature will be implemented next.",
    });
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-LK', {
      style: 'currency',
      currency: 'LKR',
      minimumFractionDigits: 2,
    }).format(price);
  };

  const getStoreColor = (website: string) => {
    const colors: { [key: string]: string } = {
      'glowmark.lk': 'bg-blue-100 text-blue-800',
      'kapruka.com': 'bg-green-100 text-green-800',
      'onlinekade.lk': 'bg-purple-100 text-purple-800',
      'lassanaflora.com': 'bg-pink-100 text-pink-800',
    };
    return colors[website] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <div className="container mx-auto px-4 py-8">
        {/* Header Section */}
        <div className="flex items-center space-x-4 mb-8">
          <Link to="/">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Search
            </Button>
          </Link>
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
              <span className="font-medium">"{originalQuery}"</span>
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
                    <div className="text-2xl font-bold text-primary">{searchResults.items_count}</div>
                    <div className="text-sm text-muted-foreground">Optimized Items</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{searchResults.total_items_found}</div>
                    <div className="text-sm text-muted-foreground">Items Found</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{searchResults.stores_used.length}</div>
                    <div className="text-sm text-muted-foreground">Stores</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{Math.round(searchResults.estimated_delivery_hours)}h</div>
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
                  These products were selected using {searchResults.optimization_method} optimization
                </p>
              </CardHeader>
              <CardContent>
                {searchResults.optimized_items.length > 0 ? (
                  <div className="space-y-4">
                    {searchResults.optimized_items.map((item, index) => (
                      <div key={index} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <h3 className="font-semibold text-lg">{item.title}</h3>
                              {item.kg_enhanced && (
                                <Badge variant="secondary" className="bg-green-100 text-green-800">
                                  🧠 AI Enhanced
                                </Badge>
                              )}
                            </div>
                            <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                              <div className="flex items-center space-x-1">
                                <Store className="h-4 w-4" />
                                <Badge className={getStoreColor(item.website)}>
                                  {item.website}
                                </Badge>
                              </div>
                              <div className="flex items-center space-x-1">
                                <CheckCircle className="h-4 w-4" />
                                <span>Match: {Math.round(item.similarity_score * 100)}%</span>
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-primary">
                              {formatPrice(item.price_lkr)}
                            </div>
                            <div className="text-sm text-muted-foreground">per item</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Package className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Items Found</h3>
                    <p className="text-muted-foreground">
                      The AI couldn't find suitable products matching your criteria. 
                      Try adjusting your search query.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Order Summary */}
          <div className="space-y-6">
            {/* Order Summary */}
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
                    <span>Subtotal ({searchResults.items_count} items)</span>
                    <span>{formatPrice(searchResults.total_cost)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Loyalty Savings</span>
                    <span className="text-green-600">
                      -{formatPrice(searchResults.pipeline_summary.loyalty_savings)}
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
                      {formatPrice(searchResults.total_cost - searchResults.pipeline_summary.loyalty_savings)}
                    </span>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-sm">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span>Estimated delivery: {Math.round(searchResults.estimated_delivery_hours)} hours</span>
                  </div>
                  
                  <Button 
                    onClick={handleConfirmOrder}
                    className="w-full bg-gradient-primary hover:opacity-90"
                    disabled={searchResults.items_count === 0}
                  >
                    Confirm Order
                  </Button>
                  
                  <p className="text-xs text-muted-foreground text-center">
                    By confirming, you agree to our terms and conditions
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Pipeline Summary */}
            <Card>
              <CardHeader>
                <CardTitle>AI Processing Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span>Keywords Extracted</span>
                    <Badge variant="outline">{searchResults.pipeline_summary.keywords_extracted}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Items Acquired</span>
                    <Badge variant="outline">{searchResults.pipeline_summary.items_acquired}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>After Personalization</span>
                    <Badge variant="outline">{searchResults.pipeline_summary.items_personalized}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>After Logistics</span>
                    <Badge variant="outline">{searchResults.pipeline_summary.items_after_logistics}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Final Selection</span>
                    <Badge className="bg-gradient-primary text-white">
                      {searchResults.pipeline_summary.final_selection}
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

export default OrderPlacement;
