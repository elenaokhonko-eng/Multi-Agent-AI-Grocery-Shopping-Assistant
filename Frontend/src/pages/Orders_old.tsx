import { ArrowLeft, Package, Truck, CheckCircle, Clock, AlertCircle, MessageSquare, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useToast } from '@/hooks/use-toast';

// API response interfaces
interface OrderItem {
  productId: string;
  title: string;
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
  store: string;
  items: OrderItem[];
  totalAmount: number;
  status: string;
  estimatedDelivery: string;
  nextStatusUpdate: string;
  statusHistory: StatusHistoryItem[];
  createdAt: string;
  updatedAt: string;
}

interface StoreOrdersResponse {
  success: boolean;
  message: string;
  store: string;
  data: ApiOrder[];
  count: number;
}

// UI Order interface
interface Order {
  id: string;
  orderId: string;
  store: string;
  items: OrderItem[];
  totalAmount: number;
  orderDate: string;
  status: 'pending' | 'in_transit' | 'out_for_delivery' | 'delivered' | 'cancelled' | 'processing';
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
        description: 'Order is being processed',
        progress: 25
      };
    case 'processing':
      return {
        icon: Package,
        label: 'Processing',
        color: 'bg-blue-500 text-white',
        description: 'Order is being prepared',
        progress: 40
      };
    case 'in_transit':
      return {
        icon: Truck,
        label: 'In Transit',
        color: 'bg-info text-white',
        description: 'Your order is on the way',
        progress: 70
      };
    case 'out_for_delivery':
      return {
        icon: Package,
        label: 'Out for Delivery',
        color: 'bg-accent text-white',
        description: 'Order will be delivered today',
        progress: 90
      };
    case 'delivered':
      return {
        icon: CheckCircle,
        label: 'Delivered',
        color: 'bg-success text-white',
        description: 'Successfully delivered',
        progress: 100
      };
    case 'cancelled':
      return {
        icon: AlertCircle,
        label: 'Cancelled',
        color: 'bg-destructive text-white',
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
  const { toast } = useToast();

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
  return (
    <div className="min-h-screen ">
      {/* Header (soft card on tinted bg) */}
      <div className="container mx-auto px-4 pt-6">
        {/*<div className="flex items-center gap-4 rounded-2xl bg-white/70 backdrop-blur-sm border border-white/60 shadow-soft px-4 py-3">*/}
          <Link to="/">
            {/*<Button variant="ghost" size="sm" className="rounded-full">*/}
            {/*  <ArrowLeft className="h-4 w-4 mr-2" />*/}
            {/*  Back to Store*/}
            {/*</Button>*/}
          </Link>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Order Tracking</h1>
            <p className="text-sm md:text-base text-muted-foreground">Track all your orders in one place</p>
          </div>
        {/*</div>*/}
      </div>

      {/* Orders List */}
      <div className="container mx-auto px-4 py-8">
        <div className="space-y-6">
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
                        Order #{order.id}
                      </CardTitle>
                      <p className="text-sm text-muted-foreground">
                        Ordered on {new Date(order.orderDate).toLocaleDateString()}
                      </p>
                    </div>
                    <Badge className={`${statusInfo.color} rounded-full px-3 py-1 text-xs md:text-sm`}>
                      <StatusIcon className="h-3.5 w-3.5 mr-1" />
                      {statusInfo.label}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Product Info */}
                  <div className="flex items-center gap-4">
                    <img
                      src={order.productImage}
                      alt={order.productName}
                      className="w-16 h-16 md:w-20 md:h-20 object-cover rounded-xl shadow-soft"
                    />
                    <div className="flex-1">
                      <h3 className="font-medium text-base md:text-lg">{order.productName}</h3>
                      <p className="text-sm text-muted-foreground">
                        Quantity: {order.quantity} • ${order.price}
                      </p>
                      <p className="text-sm md:text-base font-semibold">
                        Total: ${(order.price * order.quantity).toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs md:text-sm text-muted-foreground">Tracking Number</p>
                      <p className="font-mono text-sm md:text-base font-medium">{order.trackingNumber}</p>
                    </div>
                  </div>

                  <Separator />

                  {/* Progress */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <p className="text-sm md:text-base font-medium">Order Progress</p>
                      <p className="text-sm md:text-base text-muted-foreground">{order.progress}%</p>
                    </div>
                    <Progress value={order.progress} className="h-2" />
                    <p className="text-sm text-muted-foreground">
                      {statusInfo.description}
                      {order.estimatedDelivery && order.status !== 'delivered' && (
                        <span> • Estimated delivery: {new Date(order.estimatedDelivery).toLocaleDateString()}</span>
                      )}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap items-center gap-2 pt-2">
                    {order.status === 'delivered' && (
                      <>
                        <Button variant="outline" size="sm" className="rounded-full">
                          Rate Product
                        </Button>
                        <Button variant="outline" size="sm" className="rounded-full">
                          Buy Again
                        </Button>
                      </>
                    )}
                    {order.status === 'in-dispute' && (
                      <Button variant="outline" size="sm" className="rounded-full">
                        <MessageSquare className="h-4 w-4 mr-2" />
                        View Dispute
                      </Button>
                    )}
                    {order.status === 'in-review' && (
                      <Button variant="outline" size="sm" className="rounded-full">
                        <Clock className="h-4 w-4 mr-2" />
                        Review Details
                      </Button>
                    )}
                    {(order.status === 'in-transit' || order.status === 'delivery') && (
                      <Button variant="outline" size="sm" className="rounded-full">
                        <Truck className="h-4 w-4 mr-2" />
                        Track Live
                      </Button>
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

        {/* Summary (pill-style like your status bar) */}
        <Card className="mt-8 rounded-3xl border-0 bg-[#F2FBFD] shadow-soft">
          <CardContent className="p-6">
            <div className="text-center space-y-3">
              <h3 className="text-lg md:text-xl font-semibold tracking-tight">Order Summary</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-6 text-center">
                <div className="space-y-1">
                  <div className="text-2xl md:text-3xl font-bold leading-none">
                    {orders.filter(o => o.status === 'in-transit').length}
                  </div>
                  <p className="text-sm md:text-base text-muted-foreground">In Transit</p>
                </div>
                <div className="space-y-1">
                  <div className="text-2xl md:text-3xl font-bold leading-none">
                    {orders.filter(o => o.status === 'delivery').length}
                  </div>
                  <p className="text-sm md:text-base text-muted-foreground">Out for Delivery</p>
                </div>
                <div className="space-y-1">
                  <div className="text-2xl md:text-3xl font-bold leading-none">
                    {orders.filter(o => o.status === 'delivered').length}
                  </div>
                  <p className="text-sm md:text-base text-muted-foreground">Delivered</p>
                </div>
                <div className="space-y-1">
                  <div className="text-2xl md:text-3xl font-bold leading-none">
                    {orders.filter(o => o.status === 'in-review').length}
                  </div>
                  <p className="text-sm md:text-base text-muted-foreground">In Review</p>
                </div>
                <div className="space-y-1">
                  <div className="text-2xl md:text-3xl font-bold leading-none">
                    {orders.filter(o => o.status === 'in-dispute').length}
                  </div>
                  <p className="text-sm md:text-base text-muted-foreground">In Dispute</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Orders;
