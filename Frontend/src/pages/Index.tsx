import { useState } from 'react';
import { PromoBanner } from '@/components/PromoBanner';
import { ProductGrid } from '@/components/ProductGrid';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { Loader2 } from 'lucide-react';

const Index = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isLoadingList, setIsLoadingList] = useState(false);

  const handleLoadFixedList = async () => {
    setIsLoadingList(true);
    toast({
      title: 'Loading Fixed Shopping List',
      description: 'Consulting AI and scraping stores for your weekly items...',
    });

    try {
      const payload = {
        query: "my weekly list",
        modalities: {}
      };

      const response = await fetch('http://localhost:3004/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      if (data.status === 'success') {
        navigate('/order-placement', {
          state: { searchResults: data.results, originalQuery: "my weekly list" },
        });
        toast({
          title: 'Search completed!',
          description: `Found ${data.results.items_count} optimized items for your weekly list.`,
        });
      } else {
        toast({
          title: 'Search failed',
          description: data.message || 'An error occurred during search',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Search error:', error);
      toast({
        title: 'Network Error',
        description: 'Failed to connect to AI backend. Is it running?',
        variant: 'destructive',
      });
    } finally {
      setIsLoadingList(false);
    }
  };

  return (
    <div className="space-y-8">
      
      {/* Quick Start Fixed List */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-xl p-6 flex flex-col sm:flex-row items-center justify-between shadow-sm">
        <div className="mb-4 sm:mb-0">
          <h3 className="text-xl font-bold text-blue-900">Weekly Grocery Run</h3>
          <p className="text-blue-700">Automatically load and optimize your fixed grocery list for checkout.</p>
        </div>
        <Button 
          onClick={handleLoadFixedList} 
          disabled={isLoadingList}
          size="lg"
          className="bg-blue-600 hover:bg-blue-700 text-white shadow-md transition-all hover:shadow-lg w-full sm:w-auto"
        >
          {isLoadingList ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Processing...
            </>
          ) : (
            'Load Fixed Shopping List'
          )}
        </Button>
      </div>

      {/* Promotional Banner */}
      <PromoBanner />

      {/* Product Grid */}
      <ProductGrid />

      {/* Categories Section - Modern Design */}
      <div className="space-y-8">
        <div className="text-center space-y-4">
          <h2 className="text-4xl font-bold bg-gradient-primary bg-clip-text text-transparent">
            Shop by Category
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Discover curated collections powered by AI to find exactly what you need
          </p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          {[
            { 
              name: 'Electronics', 
              gradient: 'from-blue-500 to-cyan-400', 
              bgGradient: 'from-blue-50 to-cyan-50',
              icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              )
            },
            { 
              name: 'Clothing', 
              gradient: 'from-purple-500 to-pink-400', 
              bgGradient: 'from-purple-50 to-pink-50',
              icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
              )
            },
            { 
              name: 'Home & Garden', 
              gradient: 'from-green-500 to-emerald-400', 
              bgGradient: 'from-green-50 to-emerald-50',
              icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              )
            },
            { 
              name: 'Sports', 
              gradient: 'from-orange-500 to-red-400', 
              bgGradient: 'from-orange-50 to-red-50',
              icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              )
            },
            { 
              name: 'Books', 
              gradient: 'from-yellow-500 to-amber-400', 
              bgGradient: 'from-yellow-50 to-amber-50',
              icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              )
            },
            { 
              name: 'Beauty', 
              gradient: 'from-pink-500 to-rose-400', 
              bgGradient: 'from-pink-50 to-rose-50',
              icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              )
            },
          ].map((category) => (
            <div
              key={category.name}
              className={`relative overflow-hidden bg-gradient-to-br ${category.bgGradient} backdrop-blur-sm border border-white/20 p-8 rounded-2xl text-center hover:shadow-xl transition-all duration-500 cursor-pointer group hover:-translate-y-2`}
            >
              {/* Animated background gradient */}
              <div className={`absolute inset-0 bg-gradient-to-br ${category.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-500`}></div>
              
              {/* Floating particles */}
              <div className="absolute top-2 right-2 w-2 h-2 bg-current opacity-20 rounded-full animate-pulse"></div>
              <div className="absolute bottom-3 left-3 w-1 h-1 bg-current opacity-30 rounded-full animate-pulse delay-300"></div>
              
              <div className={`relative z-10 w-16 h-16 mx-auto mb-4 bg-gradient-to-br ${category.gradient} rounded-2xl flex items-center justify-center text-white group-hover:scale-110 group-hover:rotate-3 transition-all duration-500 shadow-lg`}>
                {category.icon}
              </div>
              
              <h3 className="font-semibold text-gray-800 group-hover:text-gray-900 transition-colors">
                {category.name}
              </h3>
              
              {/* Subtle glow effect */}
              <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${category.gradient} opacity-0 group-hover:opacity-5 blur-xl transition-opacity duration-500`}></div>
            </div>
          ))}
        </div>
      </div>

      {/* Features Section - Ultra Modern Design */}
      <div className="relative overflow-hidden">
        {/* Background with animated gradients */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50"></div>
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-gradient-to-br from-blue-200/30 to-purple-200/30 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-gradient-to-br from-cyan-200/30 to-pink-200/30 rounded-full blur-3xl animate-pulse delay-1000"></div>
        
        <div className="relative z-10 px-8 py-16 rounded-3xl">
          <div className="text-center space-y-6 mb-16">
            <h2 className="text-5xl font-bold">
              <span className="bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent">
                Why Choose
              </span>
              <br />
              <span className="bg-gradient-primary bg-clip-text text-transparent">
                TitanStore AI?
              </span>
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Experience the future of online shopping with cutting-edge AI technology 
              that understands exactly what you need
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* AI-Powered Search */}
            <div className="group">
              <div className="relative bg-white/70 backdrop-blur-xl border border-white/20 rounded-3xl p-8 hover:shadow-2xl transition-all duration-700 hover:-translate-y-4">
                {/* Animated background */}
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                
                {/* Icon container with neural network effect */}
                <div className="relative mb-6">
                  <div className="w-20 h-20 mx-auto bg-gradient-to-br from-blue-500 to-cyan-400 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 group-hover:rotate-6 transition-all duration-500">
                    <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  
                  {/* Neural network dots */}
                  <div className="absolute -top-2 -right-2 w-3 h-3 bg-blue-400 rounded-full animate-ping"></div>
                  <div className="absolute -bottom-2 -left-2 w-2 h-2 bg-cyan-400 rounded-full animate-pulse delay-500"></div>
                  <div className="absolute top-1/2 -right-4 w-1 h-1 bg-blue-300 rounded-full animate-bounce delay-700"></div>
                </div>

                <h3 className="text-2xl font-bold text-gray-800 mb-4 group-hover:text-blue-700 transition-colors">
                  AI-Powered Search
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  Simply describe what you need in natural language. Our advanced AI 
                  understands context and finds the perfect products across multiple stores.
                </p>
                
                {/* Subtle bottom accent */}
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-cyan-400 rounded-b-3xl transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500"></div>
              </div>
            </div>

            {/* Fast Delivery */}
            <div className="group">
              <div className="relative bg-white/70 backdrop-blur-xl border border-white/20 rounded-3xl p-8 hover:shadow-2xl transition-all duration-700 hover:-translate-y-4">
                {/* Animated background */}
                <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-red-500/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                
                {/* Icon container with speed lines */}
                <div className="relative mb-6">
                  <div className="w-20 h-20 mx-auto bg-gradient-to-br from-orange-500 to-red-400 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 group-hover:rotate-6 transition-all duration-500">
                    <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  
                  {/* Speed effect lines */}
                  <div className="absolute top-4 -left-6 w-8 h-0.5 bg-orange-300 rounded opacity-0 group-hover:opacity-100 group-hover:translate-x-2 transition-all duration-300"></div>
                  <div className="absolute top-8 -left-4 w-6 h-0.5 bg-red-300 rounded opacity-0 group-hover:opacity-100 group-hover:translate-x-2 transition-all duration-300 delay-100"></div>
                  <div className="absolute top-12 -left-5 w-7 h-0.5 bg-orange-300 rounded opacity-0 group-hover:opacity-100 group-hover:translate-x-2 transition-all duration-300 delay-200"></div>
                </div>

                <h3 className="text-2xl font-bold text-gray-800 mb-4 group-hover:text-orange-700 transition-colors">
                  Lightning Fast Delivery
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  Get your orders delivered in 24-48 hours with our optimized logistics 
                  network and real-time tracking for complete peace of mind.
                </p>
                
                {/* Subtle bottom accent */}
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-orange-500 to-red-400 rounded-b-3xl transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500"></div>
              </div>
            </div>

            {/* Secure Shopping */}
            <div className="group">
              <div className="relative bg-white/70 backdrop-blur-xl border border-white/20 rounded-3xl p-8 hover:shadow-2xl transition-all duration-700 hover:-translate-y-4">
                {/* Animated background */}
                <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-emerald-500/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                
                {/* Icon container with security shield */}
                <div className="relative mb-6">
                  <div className="w-20 h-20 mx-auto bg-gradient-to-br from-green-500 to-emerald-400 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 group-hover:rotate-6 transition-all duration-500">
                    <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  </div>
                  
                  {/* Security particles */}
                  <div className="absolute -top-1 left-1/2 w-2 h-2 bg-green-400 rounded-full animate-ping"></div>
                  <div className="absolute top-2 right-2 w-1 h-1 bg-emerald-400 rounded-full animate-pulse delay-300"></div>
                  <div className="absolute bottom-1 left-3 w-1.5 h-1.5 bg-green-300 rounded-full animate-bounce delay-500"></div>
                </div>

                <h3 className="text-2xl font-bold text-gray-800 mb-4 group-hover:text-green-700 transition-colors">
                  Bank-Level Security
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  Your data and payments are protected with enterprise-grade encryption 
                  and secure payment processing that exceeds industry standards.
                </p>
                
                {/* Subtle bottom accent */}
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-green-500 to-emerald-400 rounded-b-3xl transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500"></div>
              </div>
            </div>
          </div>
          
          {/* Call to action */}
          <div className="text-center mt-16">
            <Link to="/order-placement">
              <button className="bg-gradient-primary text-white px-8 py-4 rounded-2xl font-semibold text-lg hover:shadow-xl hover:scale-105 transition-all duration-300">
                Experience AI Shopping Now
              </button>
            </Link>
          </div>
        </div>
      </div>
      {/* end Features */}
    </div>
  );
};

export default Index;
