import { Header } from '@/components/Header';
import { PromoBanner } from '@/components/PromoBanner';
import { ProductGrid } from '@/components/ProductGrid';
import { KitchenInventory } from '@/components/KitchenInventory';

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <div className="flex items-start gap-6 overflow-visible">

        {/* Kitchen Inventory Sidebar */}
        <KitchenInventory />

        {/* Main Content */}
        <div className="flex-1">
          <div className="container mx-auto px-4 py-6 space-y-8">
            {/* Promotional Banner */}
            <PromoBanner />
            
            {/* Product Grid */}
            <ProductGrid />
            
            {/* Categories Section */}
            <div className="space-y-6">
              <h2 className="text-2xl font-bold">Shop by Category</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {[
                  { name: "Electronics", icon: "💻", color: "bg-blue-100" },
                  { name: "Clothing", icon: "👕", color: "bg-purple-100" },
                  { name: "Home & Garden", icon: "🏠", color: "bg-green-100" },
                  { name: "Sports", icon: "⚽", color: "bg-orange-100" },
                  { name: "Books", icon: "📚", color: "bg-yellow-100" },
                  { name: "Beauty", icon: "💄", color: "bg-pink-100" }
                ].map((category) => (
                  <div
                    key={category.name}
                    className={`${category.color} p-6 rounded-xl text-center hover:shadow-medium transition-all duration-300 cursor-pointer group`}
                  >
                    <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">
                      {category.icon}
                    </div>
                    <h3 className="font-medium text-sm">{category.name}</h3>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Features Section */}
            <div className="bg-gradient-secondary rounded-2xl p-8">
              <div className="text-center space-y-4">
                <h2 className="text-3xl font-bold">Why Choose TitanStore AI?</h2>
                <p className="text-muted-foreground text-lg">Experience the future of online shopping</p>
                
                <div className="grid md:grid-cols-3 gap-6 mt-8">
                  <div className="text-center space-y-2">
                    <div className="w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center mx-auto">
                      <span className="text-2xl">🤖</span>
                    </div>
                    <h3 className="font-semibold">AI-Powered Search</h3>
                    <p className="text-sm text-muted-foreground">Describe what you need and our AI will find it for you</p>
                  </div>
                  <div className="text-center space-y-2">
                    <div className="w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center mx-auto">
                      <span className="text-2xl">🚚</span>
                    </div>
                    <h3 className="font-semibold">Fast Delivery</h3>
                    <p className="text-sm text-muted-foreground">Get your orders delivered in 24-48 hours</p>
                  </div>
                  <div className="text-center space-y-2">
                    <div className="w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center mx-auto">
                      <span className="text-2xl">🔒</span>
                    </div>
                    <h3 className="font-semibold">Secure Shopping</h3>
                    <p className="text-sm text-muted-foreground">Your data and payments are always protected</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
