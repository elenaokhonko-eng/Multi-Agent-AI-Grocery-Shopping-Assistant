import { ArrowLeft, Package, Truck, CheckCircle, Clock, AlertCircle, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Link } from 'react-router-dom';

interface Order {
  id: string;
  productName: string;
  productImage: string;
  price: number;
  quantity: number;
  orderDate: string;
  status: 'in-transit' | 'delivery' | 'delivered' | 'in-review' | 'in-dispute';
  estimatedDelivery?: string;
  trackingNumber: string;
  progress: number;
}

const orders: Order[] = [
  {
    id: "ORD-001",
    productName: "Wireless Bluetooth Headphones",
    productImage: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300&h=300&fit=crop",
    price: 79.99,
    quantity: 1,
    orderDate: "2024-01-02",
    status: "in-transit",
    estimatedDelivery: "2024-01-08",
    trackingNumber: "TRK123456789",
    progress: 60
  },
  {
    id: "ORD-002",
    productName: "Smart Watch Pro",
    productImage: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=300&h=300&fit=crop",
    price: 199.99,
    quantity: 1,
    orderDate: "2024-01-01",
    status: "delivery",
    estimatedDelivery: "2024-01-05",
    trackingNumber: "TRK987654321",
    progress: 85
  },
  {
    id: "ORD-003",
    productName: "Portable Power Bank 20000mAh",
    productImage: "https://images.unsplash.com/photo-1609592282443-6d5c09f8ad3a?w=300&h=300&fit=crop",
    price: 45.99,
    quantity: 2,
    orderDate: "2023-12-28",
    status: "delivered",
    estimatedDelivery: "2024-01-02",
    trackingNumber: "TRK555666777",
    progress: 100
  },
  {
    id: "ORD-004",
    productName: "Wireless Gaming Mouse",
    productImage: "https://images.unsplash.com/photo-1527814050087-3793815479db?w=300&h=300&fit=crop",
    price: 59.99,
    quantity: 1,
    orderDate: "2023-12-25",
    status: "in-review",
    trackingNumber: "TRK111222333",
    progress: 100
  },
  {
    id: "ORD-005",
    productName: "USB-C Fast Charging Cable",
    productImage: "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=300&h=300&fit=crop",
    price: 19.99,
    quantity: 3,
    orderDate: "2023-12-20",
    status: "in-dispute",
    trackingNumber: "TRK444555666",
    progress: 100
  }
];

const getStatusInfo = (status: Order['status']) => {
  switch (status) {
    case 'in-transit':
      return {
        icon: Truck,
        label: 'In Transit',
        color: 'bg-info text-white',
        description: 'Your order is on the way'
      };
    case 'delivery':
      return {
        icon: Package,
        label: 'Out for Delivery',
        color: 'bg-accent text-white',
        description: 'Order will be delivered today'
      };
    case 'delivered':
      return {
        icon: CheckCircle,
        label: 'Delivered',
        color: 'bg-success text-white',
        description: 'Successfully delivered'
      };
    case 'in-review':
      return {
        icon: Clock,
        label: 'In Review',
        color: 'bg-warning text-white',
        description: 'Order review in progress'
      };
    case 'in-dispute':
      return {
        icon: AlertCircle,
        label: 'In Dispute',
        color: 'bg-destructive text-white',
        description: 'Issue reported with order'
      };
    default:
      return {
        icon: Package,
        label: 'Unknown',
        color: 'bg-muted text-muted-foreground',
        description: ''
      };
  }
};

const Orders = () => {
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
