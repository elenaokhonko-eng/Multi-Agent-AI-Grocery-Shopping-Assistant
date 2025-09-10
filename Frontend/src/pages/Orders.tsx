import { Package, Truck, CheckCircle, Clock, AlertCircle, Loader2, ExternalLink, HelpCircle, Calendar, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { useEffect, useState } from 'react';
import { useToast } from '@/hooks/use-toast';

// API response interfaces
interface OrderItem {
  productId: string;
  title: string; // API uses 'title', not 'name'
  price: number;
  quantity: number;
  subtotal: number;
  _id: string;
}

interface StatusHistoryItem {
  status: string;
  timestamp: string;
  note: string;
  _id: string;
}

interface ApiOrder {
  _id: string;
  orderId: string;
  userId: string;
  items: OrderItem[];
  totalAmount: number;
  status: string;
  createdAt: string;
  estimatedDelivery?: string;
  statusHistory: StatusHistoryItem[];
  __v: number;
}

interface StoreOrdersResponse {
  success: boolean;
  data: ApiOrder[];
  store: string;
}

// UI interfaces
interface Order {
  id: string;
  orderId: string;
  store: string;
  items: OrderItem[];
  totalAmount: number;
  orderDate: string;
  status: 'pending' | 'in_transit' | 'store_pickup' | 'completed' | 'cancelled';
  estimatedDelivery?: string;
  progress: number;
}

const USER_ID = 'test-user-123'; // Same user ID used in OrderPlacement
const STORE_NAMES = ['onlinekade', 'kapruka', 'glowmark'];

const getStatusInfo = (status: string) => {
  switch (status.toLowerCase()) {
    case 'pending':
      return {
        icon: Clock,
        label: 'Pending',
        color: 'bg-yellow-500 text-white',
        description: 'Order created successfully',
        progress: 25
      };
    case 'in_transit':
      return {
        icon: Truck,
        label: 'In Transit',
        color: 'bg-blue-500 text-white',
        description: 'Your order is on the way',
        progress: 50
      };
    case 'store_pickup':
      return {
        icon: Package,
        label: 'Ready for Pickup',
        color: 'bg-orange-500 text-white',
        description: 'Order ready for store pickup',
        progress: 75
      };
    case 'completed':
      return {
        icon: CheckCircle,
        label: 'Completed',
        color: 'bg-green-500 text-white',
        description: 'Order completed successfully',
        progress: 100
      };
    case 'cancelled':
      return {
        icon: AlertCircle,
        label: 'Cancelled',
        color: 'bg-red-500 text-white',
        description: 'Order was cancelled',
        progress: 0
      };
    default:
      return {
        icon: Package,
        label: status || 'Unknown',
        color: 'bg-muted text-muted-foreground',
        description: '',
        progress: 0
      };
  }
};

const formatPrice = (price: number) =>
  new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 2,
  }).format(price);

const Orders = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancellingOrders, setCancellingOrders] = useState<Set<string>>(new Set());
  const { toast } = useToast();

  const handleCancelOrder = async (order: Order) => {
    try {
      setCancellingOrders(prev => new Set(prev).add(order.id));
      
      const response = await fetch(
        `http://localhost:3005/api/orders/${order.store}/${order.orderId}/cancel`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            reason: 'Customer requested cancellation'
          })
        }
      );

      if (response.ok) {
        // Update the order status in the local state
        setOrders(prevOrders => 
          prevOrders.map(o => 
            o.id === order.id 
              ? { ...o, status: 'cancelled' as const, progress: 0 }
              : o
          )
        );
        
        toast({
          title: 'Order cancelled successfully',
          description: `Order #${order.orderId} has been cancelled.`,
          variant: 'default',
        });
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to cancel order');
      }
    } catch (error) {
      console.error('Error cancelling order:', error);
      toast({
        title: 'Failed to cancel order',
        description: error instanceof Error ? error.message : 'An unexpected error occurred',
        variant: 'destructive',
      });
    } finally {
      setCancellingOrders(prev => {
        const newSet = new Set(prev);
        newSet.delete(order.id);
        return newSet;
      });
    }
  };

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const allOrders: Order[] = [];
        
        // Fetch orders from all stores
        for (const storeName of STORE_NAMES) {
          try {
            const response = await fetch(`http://localhost:3005/api/orders/${storeName}/user/${USER_ID}`);
            
            if (response.ok) {
              const storeResponse: StoreOrdersResponse = await response.json();
              
              // Transform API orders to UI orders
              const transformedOrders: Order[] = storeResponse.data.map(apiOrder => ({
                id: apiOrder._id,
                orderId: apiOrder.orderId,
                store: storeName,
                items: apiOrder.items,
                totalAmount: apiOrder.totalAmount,
                orderDate: apiOrder.createdAt,
                status: apiOrder.status as Order['status'],
                estimatedDelivery: apiOrder.estimatedDelivery,
                progress: getStatusInfo(apiOrder.status).progress,
              }));
              
              allOrders.push(...transformedOrders);
              console.log(`✅ Fetched ${transformedOrders.length} orders from ${storeName}`);
            } else {
              console.log(`ℹ️ No orders found for ${storeName} (${response.status})`);
            }
          } catch (storeError) {
            console.error(`❌ Error fetching orders from ${storeName}:`, storeError);
          }
        }
        
        // Sort orders by creation date (newest first)
        allOrders.sort((a, b) => new Date(b.orderDate).getTime() - new Date(a.orderDate).getTime());
        
        setOrders(allOrders);
        console.log(`📦 Total orders loaded: ${allOrders.length}`);
        
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch orders';
        setError(errorMessage);
        toast({
          title: 'Error loading orders',
          description: errorMessage,
          variant: 'destructive',
        });
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, [toast]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
          <h2 className="text-xl font-semibold">Loading your orders...</h2>
          <p className="text-muted-foreground">Fetching data from all stores</p>
        </div>
      </div>
    );
  }

  if (error && orders.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <AlertCircle className="h-16 w-16 text-destructive mx-auto" />
          <h2 className="text-xl font-semibold">Failed to load orders</h2>
          <p className="text-muted-foreground">{error}</p>
          <Button onClick={() => window.location.reload()}>Try Again</Button>
        </div>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50/50 to-white flex items-center justify-center">
        <Card className="max-w-md mx-auto p-8 text-center">
          <Package className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">No orders found</h3>
          <p className="text-muted-foreground mb-6">You haven't placed any orders yet.</p>
          <Button onClick={() => window.location.href = '/'}>
            Start Shopping
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50/50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
            My Orders
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Track and manage your order history across all stores
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-warning/20 rounded-lg">
                <Package className="h-5 w-5 text-warning" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Orders</p>
                <p className="text-2xl font-bold">{orders.length}</p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-info/20 rounded-lg">
                <Truck className="h-5 w-5 text-info" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">In Transit</p>
                <p className="text-2xl font-bold">
                  {orders.filter(o => o.status === 'in_transit').length}
                </p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-accent/20 rounded-lg">
                <Package className="h-5 w-5 text-accent" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Ready for Pickup</p>
                <p className="text-2xl font-bold">
                  {orders.filter(o => o.status === 'store_pickup').length}
                </p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-success/20 rounded-lg">
                <CheckCircle className="h-5 w-5 text-success" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="text-2xl font-bold">
                  {orders.filter(o => o.status === 'completed').length}
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Orders Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {orders.map((order) => {
            const statusInfo = getStatusInfo(order.status);
            const StatusIcon = statusInfo.icon;

            return (
              <Card
                key={order.id}
                className="rounded-2xl border border-black/5 bg-white/90 backdrop-blur-sm shadow-soft"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-xl md:text-2xl font-semibold tracking-tight">
                        Order #{order.orderId}
                      </CardTitle>
                      <p className="text-sm text-muted-foreground">
                        {new Date(order.orderDate).toLocaleDateString()} • {order.store}
                      </p>
                    </div>
                    <Badge className={`${statusInfo.color} rounded-full px-3 py-1 text-xs md:text-sm`}>
                      <StatusIcon className="h-3.5 w-3.5 mr-1" />
                      {statusInfo.label}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Items List */}
                  <div className="space-y-3">
                    {order.items.map((item, index) => (
                      <div key={index} className="flex items-center gap-4 p-3 bg-muted/30 rounded-lg">
                        <div className="w-12 h-12 bg-muted rounded-lg flex items-center justify-center">
                          <Package className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-sm">{item.title}</h4>
                          <p className="text-xs text-muted-foreground">
                            Qty: {item.quantity} • {formatPrice(item.price)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-semibold">
                            {formatPrice(item.price * item.quantity)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <Separator />

                  {/* Total Amount */}
                  <div className="flex justify-between items-center p-3 bg-primary/5 rounded-lg">
                    <span className="font-semibold">Total Amount:</span>
                    <span className="font-bold text-lg">{formatPrice(order.totalAmount)}</span>
                  </div>

                  {/* Progress */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <p className="text-sm md:text-base font-medium">Order Progress</p>
                      <p className="text-sm md:text-base text-muted-foreground">{order.progress}%</p>
                    </div>
                    <Progress value={order.progress} className="h-2" />
                    <p className="text-sm text-muted-foreground">
                      {statusInfo.description}
                      {order.estimatedDelivery && order.status !== 'completed' && (
                        <span> • Est. delivery: {new Date(order.estimatedDelivery).toLocaleDateString()}</span>
                      )}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap items-center gap-2 pt-2">
                    {order.status === 'completed' && (
                      <>
                        <Button variant="outline" size="sm" className="rounded-full">
                          Rate Product
                        </Button>
                        <Button variant="outline" size="sm" className="rounded-full">
                          Buy Again
                        </Button>
                      </>
                    )}
                    {order.status === 'cancelled' && (
                      <Button variant="outline" size="sm" className="rounded-full" disabled>
                        <AlertCircle className="h-4 w-4 mr-2" />
                        Cancelled
                      </Button>
                    )}
                    {order.status === 'pending' && (
                      <Button variant="outline" size="sm" className="rounded-full">
                        <Clock className="h-4 w-4 mr-2" />
                        Processing
                      </Button>
                    )}
                    {order.status === 'store_pickup' && (
                      <Button variant="outline" size="sm" className="rounded-full">
                        <Package className="h-4 w-4 mr-2" />
                        Ready for Pickup
                      </Button>
                    )}
                    {order.status === 'in_transit' && (
                      <Button variant="outline" size="sm" className="rounded-full">
                        <Truck className="h-4 w-4 mr-2" />
                        Track Package
                      </Button>
                    )}
                    
                    {/* Cancel Order Button - only for pending and in_transit orders */}
                    {(order.status === 'pending' || order.status === 'in_transit') && (
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button 
                            variant="destructive" 
                            size="sm" 
                            className="rounded-full"
                            disabled={cancellingOrders.has(order.id)}
                          >
                            {cancellingOrders.has(order.id) ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <X className="h-4 w-4 mr-2" />
                            )}
                            {cancellingOrders.has(order.id) ? 'Cancelling...' : 'Cancel Order'}
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Cancel Order #{order.orderId}?</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to cancel this order? This action cannot be undone.
                              <br /><br />
                              <strong>Order Details:</strong>
                              <br />• Store: {order.store}
                              <br />• Total: {formatPrice(order.totalAmount)}
                              <br />• Status: {getStatusInfo(order.status).label}
                              <br /><br />
                              You will receive a refund if payment has been processed.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Keep Order</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleCancelOrder(order)}
                              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            >
                              Yes, Cancel Order
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    )}
                    
                    <Button variant="ghost" size="sm" className="rounded-full">
                      Order Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Orders;
