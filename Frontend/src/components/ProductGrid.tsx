import { Star, ShoppingCart, Heart } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const products = [
  {
    id: 1,
    name: "Wireless Bluetooth Headphones",
    price: 79.99,
    originalPrice: 120.00,
    rating: 4.5,
    reviews: 128,
    image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300&h=300&fit=crop",
    discount: "33% OFF",
    badge: "Bestseller"
  },
  {
    id: 2,
    name: "Smart Watch Pro",
    price: 199.99,
    originalPrice: 299.99,
    rating: 4.7,
    reviews: 86,
    image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=300&h=300&fit=crop",
    discount: "33% OFF",
    badge: "New"
  },
  {
    id: 3,
    name: "Portable Power Bank 20000mAh",
    price: 45.99,
    originalPrice: 69.99,
    rating: 4.3,
    reviews: 234,
    image: "https://images.unsplash.com/photo-1609592282443-6d5c09f8ad3a?w=300&h=300&fit=crop",
    discount: "34% OFF"
  },
  {
    id: 4,
    name: "Wireless Gaming Mouse",
    price: 59.99,
    originalPrice: 89.99,
    rating: 4.6,
    reviews: 156,
    image: "https://images.unsplash.com/photo-1527814050087-3793815479db?w=300&h=300&fit=crop",
    discount: "33% OFF"
  },
  {
    id: 5,
    name: "USB-C Fast Charging Cable",
    price: 19.99,
    originalPrice: 29.99,
    rating: 4.4,
    reviews: 312,
    image: "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=300&h=300&fit=crop",
    discount: "33% OFF"
  },
  {
    id: 6,
    name: "Bluetooth Speaker Waterproof",
    price: 89.99,
    originalPrice: 129.99,
    rating: 4.5,
    reviews: 89,
    image: "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=300&h=300&fit=crop",
    discount: "31% OFF",
    badge: "Limited"
  }
];

export const ProductGrid = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">On Sale Now</h2>
        <Button variant="outline" className="border-accent text-accent hover:bg-accent hover:text-white">
          Shop All Products
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {products.map((product) => (
          <Card key={product.id} className="group hover:shadow-medium transition-all duration-300 border-0 shadow-soft">
            <CardContent className="p-4">
              {/* Product Image */}
              <div className="relative mb-4 overflow-hidden rounded-lg">
                <img
                  src={product.image}
                  alt={product.name}
                  className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
                />
                
                {/* Badges */}
                <div className="absolute top-2 left-2 flex flex-col space-y-1">
                  {product.badge && (
                    <Badge className="bg-gradient-primary border-0 text-white text-xs">
                      {product.badge}
                    </Badge>
                  )}
                  <Badge variant="destructive" className="text-xs">
                    {product.discount}
                  </Badge>
                </div>

                {/* Favorite Button */}
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute top-2 right-2 h-8 w-8 p-0 bg-white/80 hover:bg-white opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Heart className="h-4 w-4 text-muted-foreground" />
                </Button>

                {/* Quick Add to Cart */}
                <Button
                  className="absolute bottom-2 left-1/2 transform -translate-x-1/2 translate-y-full group-hover:translate-y-0 transition-transform bg-gradient-primary border-0"
                  size="sm"
                >
                  <ShoppingCart className="h-4 w-4 mr-2" />
                  Add to Cart
                </Button>
              </div>

              {/* Product Info */}
              <div className="space-y-2">
                <h3 className="font-medium text-sm line-clamp-2 group-hover:text-primary transition-colors">
                  {product.name}
                </h3>
                
                {/* Rating */}
                <div className="flex items-center space-x-1">
                  <div className="flex items-center">
                    <Star className="h-4 w-4 fill-warning text-warning" />
                    <span className="text-sm font-medium ml-1">{product.rating}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">({product.reviews})</span>
                </div>

                {/* Price */}
                <div className="flex items-center space-x-2">
                  <span className="text-lg font-bold text-primary">
                    ${product.price}
                  </span>
                  <span className="text-sm text-muted-foreground line-through">
                    ${product.originalPrice}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};