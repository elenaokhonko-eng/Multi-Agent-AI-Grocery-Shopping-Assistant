import { Star, ShoppingCart, Heart } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const products = [
  {
    id: 1,
    name: "Fresh Organic Carrots - 1kg",
    price: 1497,
    originalPrice: 2097,
    rating: 4.5,
    reviews: 128,
    image: "https://images.unsplash.com/photo-1445282768818-728615cc910a?w=300&h=300&fit=crop",
    discount: "29% OFF",
    badge: "Organic"
  },
  {
    id: 2,
    name: "Fresh Milk - 1 Liter",
    price: 897,
    originalPrice: 1047,
    rating: 4.7,
    reviews: 86,
    image: "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=300&h=300&fit=crop",
    discount: "14% OFF",
    badge: "Fresh"
  },
  {
    id: 3,
    name: "Organic Tomatoes - 500g",
    price: 1197,
    originalPrice: 1497,
    rating: 4.3,
    reviews: 234,
    image: "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=300&h=300&fit=crop",
    discount: "20% OFF"
  },
  {
    id: 4,
    name: "Brown Bread Loaf",
    price: 747,
    originalPrice: 897,
    rating: 4.6,
    reviews: 156,
    image: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop",
    discount: "17% OFF"
  },
  {
    id: 5,
    name: "Free Range Eggs - 12 Pack",
    price: 1497,
    originalPrice: 1797,
    rating: 4.4,
    reviews: 312,
    image: "https://images.unsplash.com/photo-1518569656558-1f25e69d93d7?w=300&h=300&fit=crop",
    discount: "17% OFF"
  },
  {
    id: 6,
    name: "Fresh Bananas - 1kg",
    price: 597,
    originalPrice: 747,
    rating: 4.5,
    reviews: 89,
    image: "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=300&h=300&fit=crop",
    discount: "20% OFF",
    badge: "Popular"
  },
  {
    id: 7,
    name: "Basmati Rice - 2kg",
    price: 2697,
    originalPrice: 3297,
    rating: 4.8,
    reviews: 201,
    image: "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&h=300&fit=crop",
    discount: "18% OFF",
    badge: "Premium"
  },
  {
    id: 8,
    name: "Greek Yogurt - 500g",
    price: 1047,
    originalPrice: 1197,
    rating: 4.6,
    reviews: 145,
    image: "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=300&h=300&fit=crop",
    discount: "13% OFF"
  },
  {
    id: 9,
    name: "Fresh Spinach - 250g",
    price: 897,
    originalPrice: 1047,
    rating: 4.4,
    reviews: 98,
    image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=300&h=300&fit=crop",
    discount: "14% OFF",
    badge: "Organic"
  },
  {
    id: 10,
    name: "Coconut Oil - 500ml",
    price: 2097,
    originalPrice: 2547,
    rating: 4.7,
    reviews: 167,
    image: "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop",
    discount: "18% OFF"
  },
  {
    id: 11,
    name: "Fresh Apples - 1kg",
    price: 1347,
    originalPrice: 1647,
    rating: 4.5,
    reviews: 223,
    image: "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=300&h=300&fit=crop",
    discount: "18% OFF"
  },
  {
    id: 12,
    name: "Whole Wheat Pasta - 500g",
    price: 897,
    originalPrice: 1047,
    rating: 4.3,
    reviews: 134,
    image: "https://images.unsplash.com/photo-1551892374-ecf8754cf8b0?w=300&h=300&fit=crop",
    discount: "14% OFF"
  },
  {
    id: 13,
    name: "Red Onions - 1kg",
    price: 747,
    originalPrice: 897,
    rating: 4.2,
    reviews: 176,
    image: "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=300&h=300&fit=crop",
    discount: "17% OFF"
  },
  {
    id: 14,
    name: "Green Tea Bags - 50 Pack",
    price: 1497,
    originalPrice: 1797,
    rating: 4.6,
    reviews: 189,
    image: "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=300&h=300&fit=crop",
    discount: "17% OFF",
    badge: "Bestseller"
  },
  {
    id: 15,
    name: "Fresh Broccoli - 500g",
    price: 1047,
    originalPrice: 1197,
    rating: 4.4,
    reviews: 112,
    image: "https://images.unsplash.com/photo-1459411552884-841db9b3cc2a?w=300&h=300&fit=crop",
    discount: "13% OFF"
  },
  {
    id: 16,
    name: "Olive Oil Extra Virgin - 500ml",
    price: 2997,
    originalPrice: 3597,
    rating: 4.8,
    reviews: 256,
    image: "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop",
    discount: "17% OFF",
    badge: "Premium"
  },
  {
    id: 17,
    name: "Fresh Potatoes - 2kg",
    price: 1197,
    originalPrice: 1497,
    rating: 4.3,
    reviews: 198,
    image: "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=300&h=300&fit=crop",
    discount: "20% OFF"
  },
  {
    id: 18,
    name: "Cheddar Cheese - 200g",
    price: 1347,
    originalPrice: 1647,
    rating: 4.7,
    reviews: 143,
    image: "https://d2j6dbq0eux0bg.cloudfront.net/images/31151001/3933781796.jpg?w=300&h=300&fit=crop",
    discount: "18% OFF"
  },
  {
    id: 19,
    name: "Whole Grain Oats - 1kg",
    price: 1197,
    originalPrice: 1497,
    rating: 4.5,
    reviews: 167,
    image: "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=300&h=300&fit=crop",
    discount: "20% OFF"
  },
  {
    id: 20,
    name: "Fresh Bell Peppers - 500g",
    price: 897,
    originalPrice: 1047,
    rating: 4.4,
    reviews: 134,
    image: "https://images.unsplash.com/photo-1525607551316-4a8e16d1b9c5?w=300&h=300&fit=crop",
    discount: "14% OFF"
  },
  {
    id: 21,
    name: "Honey - 250ml",
    price: 2097,
    originalPrice: 2397,
    rating: 4.6,
    reviews: 189,
    image: "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=300&h=300&fit=crop",
    discount: "13% OFF",
    badge: "Natural"
  },
  {
    id: 22,
    name: "Fresh Cucumber - 500g",
    price: 597,
    originalPrice: 747,
    rating: 4.2,
    reviews: 123,
    image: "https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?w=300&h=300&fit=crop",
    discount: "20% OFF"
  },
  {
    id: 23,
    name: "Almonds - 250g",
    price: 2397,
    originalPrice: 2847,
    rating: 4.7,
    reviews: 156,
    image: "https://images.unsplash.com/photo-1508747703725-719777637510?w=300&h=300&fit=crop",
    discount: "16% OFF"
  },
  {
    id: 24,
    name: "Fresh Lemon - 500g",
    price: 747,
    originalPrice: 897,
    rating: 4.3,
    reviews: 145,
    image: "https://images.unsplash.com/photo-1590502593747-42a996133562?w=300&h=300&fit=crop",
    discount: "17% OFF"
  },
  {
    id: 25,
    name: "Chicken Breast - 500g",
    price: 2697,
    originalPrice: 3297,
    rating: 4.8,
    reviews: 234,
    image: "https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=300&h=300&fit=crop",
    discount: "18% OFF",
    badge: "Fresh"
  }
];

export const ProductGrid = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Fresh Groceries & Daily Essentials</h2>
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
                    Rs.{product.price.toLocaleString()}
                  </span>
                  <span className="text-sm text-muted-foreground line-through">
                    Rs.{product.originalPrice.toLocaleString()}
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