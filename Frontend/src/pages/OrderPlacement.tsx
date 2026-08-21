import { useEffect, useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Package, Store, CheckCircle, Loader2, CreditCard } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface CartItem {
  keyword: string;
  title: string;
  price_sgd: number;
  price_lkr: number;
  quantity: number;
  website: string;
  source_url: string;
  image_url: string;
  collection: string;
}

interface Cart {
  store_name: string;
  domain: string;
  items: CartItem[];
  missing_items: string[];
  subtotal: number;
}

const STORAGE_KEY = 'op_compare_cache';

const OrderPlacement = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();

  const inbound = location.state as { carts: Cart[], originalQuery: string } | null;
  const [carts, setCarts] = useState<Cart[] | null>(inbound?.carts ?? null);
  const [query, setQuery] = useState<string>(inbound?.originalQuery ?? '');
  
  const [selectedCartIndex, setSelectedCartIndex] = useState<number>(0);
  const [isProcessingOrder, setIsProcessingOrder] = useState(false);
  
  useEffect(() => {
    if (inbound?.carts) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ carts: inbound.carts, originalQuery: inbound.originalQuery }));
      setCarts(inbound.carts);
      setQuery(inbound.originalQuery);
    } else if (!carts) {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        setCarts(parsed.carts);
        setQuery(parsed.originalQuery);
      }
    }
  }, [location.key]);

  const handleConfirmOrder = async () => {
    if (!carts || carts.length === 0) return;
    
    const selectedCart = carts[selectedCartIndex];
    if (!selectedCart || selectedCart.items.length === 0) {
      toast({ title: 'No items to order', variant: 'destructive' });
      return;
    }

    setIsProcessingOrder(true);
    toast({ title: `Placing order with ${selectedCart.store_name}...`, description: 'Agent is automating the checkout process.' });

    try {
      const response = await fetch(`http://127.0.0.1:3004/api/execute_order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          store_name: selectedCart.store_name,
          items: selectedCart.items
        }),
      });

      if (response.ok) {
        toast({ title: 'Order placed successfully! 🎉', description: `Agent successfully checked out with ${selectedCart.store_name}. Redirecting...` });
        setTimeout(() => navigate('/'), 3000);
      } else {
        const err = await response.json();
        toast({ title: 'Checkout Failed', description: err.message, variant: 'destructive' });
      }
    } catch (e) {
      toast({ title: 'Network Error', description: 'Failed to contact backend.', variant: 'destructive' });
    } finally {
      setIsProcessingOrder(false);
    }
  };

  const calculateDelivery = (cart: Cart) => {
    if (cart.subtotal > 100) return 0;
    return cart.store_name === 'FairPrice' ? 7.0 : 6.99;
  };

  const FALLBACK_IMG = 'data:image/svg+xml;utf8,' + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80"><rect width="100%" height="100%" fill="#eee"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="10" fill="#666">No Image</text></svg>`);

  const formatPrice = (p: number) => new Intl.NumberFormat('en-SG', { style: 'currency', currency: 'SGD' }).format(p);

  if (!carts) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8 text-center space-y-4">
          <Package className="h-16 w-16 text-muted-foreground mx-auto" />
          <h1 className="text-2xl font-bold">No Comparison Data</h1>
          <p className="text-muted-foreground">Please go back and run the AI search first.</p>
          <Link to="/"><Button><ArrowLeft className="h-4 w-4 mr-2" /> Back to Home</Button></Link>
        </div>
      </div>
    );
  }

  const selectedCart = carts[selectedCartIndex];
  const deliveryFee = calculateDelivery(selectedCart);
  const totalCost = selectedCart.subtotal + deliveryFee;

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Cart Comparison</h1>
          <p className="text-muted-foreground">Agents have fetched carts from different stores for comparison.</p>
        </div>

        {/* Tab Selection */}
        <div className="flex gap-4 mb-8 overflow-x-auto pb-2">
          {carts.map((cart, idx) => (
            <div 
              key={cart.store_name} 
              onClick={() => setSelectedCartIndex(idx)}
              className={`cursor-pointer border-2 rounded-xl p-4 flex-1 min-w-[250px] transition-all ${selectedCartIndex === idx ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-200 bg-white hover:border-blue-300'}`}
            >
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-lg font-bold text-gray-900">{cart.store_name}</h3>
                {selectedCartIndex === idx && <CheckCircle className="text-blue-500 h-5 w-5" />}
              </div>
              <div className="text-2xl font-black text-blue-700">{formatPrice(cart.subtotal + calculateDelivery(cart))}</div>
              <p className="text-sm text-gray-500 mb-2">{cart.items.length} items found</p>
              {cart.missing_items.length > 0 && (
                <Badge variant="destructive" className="mt-1">{cart.missing_items.length} items missing</Badge>
              )}
            </div>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content - Product List */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Items in {selectedCart.store_name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {selectedCart.items.map((item, idx) => (
                  <div key={idx} className="border rounded-xl p-4 flex gap-4">
                    <img src={item.image_url || FALLBACK_IMG} alt={item.title} className="w-16 h-16 object-contain rounded-md bg-muted" onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = FALLBACK_IMG; }} />
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 line-clamp-2">{item.title}</h4>
                      <p className="text-xs text-gray-500 mt-1">Found for: "{item.keyword}"</p>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-lg text-gray-900">{formatPrice(item.price_sgd)}</div>
                      <div className="text-xs text-gray-500">Qty: {item.quantity}</div>
                    </div>
                  </div>
                ))}

                {selectedCart.missing_items.length > 0 && (
                  <div className="mt-6 pt-6 border-t border-red-100">
                    <h4 className="font-bold text-red-600 mb-2">Could not find:</h4>
                    <ul className="list-disc list-inside text-sm text-red-500 space-y-1">
                      {selectedCart.missing_items.map((m, i) => <li key={i}>{m}</li>)}
                    </ul>
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
                {selectedCart.subtotal > 100 && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center mb-4">
                    <p className="text-green-700 font-medium">✨ Your order qualifies for free delivery!</p>
                  </div>
                )}
                <div className="space-y-2">
                  <div className="flex justify-between text-gray-600">
                    <span>Subtotal ({selectedCart.items.length} items)</span>
                    <span>{formatPrice(selectedCart.subtotal)}</span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span>Delivery Fee</span>
                    <span>{deliveryFee === 0 ? <span className="text-green-600 font-medium">FREE</span> : formatPrice(deliveryFee)}</span>
                  </div>
                  <Separator className="my-4" />
                  <div className="flex justify-between text-xl font-black text-gray-900">
                    <span>Total</span>
                    <span>{formatPrice(totalCost)}</span>
                  </div>
                </div>

                <Button
                  onClick={handleConfirmOrder}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold h-12 mt-6"
                  disabled={isProcessingOrder || selectedCart.items.length === 0}
                >
                  {isProcessingOrder ? <Loader2 className="h-5 w-5 mr-2 animate-spin" /> : null}
                  {isProcessingOrder ? 'Executing Agent Checkout...' : `Checkout with ${selectedCart.store_name} Agent`}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderPlacement;
