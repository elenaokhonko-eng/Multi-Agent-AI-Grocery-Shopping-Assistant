import { useState } from 'react';
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
        query: "Akaroa Salmon Fresh New Zealand King Salmon Fillet, Emborg Frozen Chopped Spinach, Jeju SamDaSoo Mineral Bottle Water 2L, Jeju SamDaSoo Mineral Bottle Water 500ml, Nuyolk Vitamins Enriched Eggs, Authentic Tea House Ayataka No Sugar Japanese Green Tea, Nature's Wonders Baked nuts Macadamia, CGPL South Africa Lemon, Live Well Baby Spinach, Snacky & Crisps Salted Egg Fish Skin, Yuan Zhen Yuan Yellow Capsicum, The Golden Duck Co Gourmet Crunchy Crisps Salted Egg FishSkin, Yuan Zhen Yuan Mexican Avocado, Blueberries, Raspberries",
        modalities: {}
      };

      const response = await fetch('http://127.0.0.1:3004/api/compare_carts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      if (data.status === 'success') {
        navigate('/order-placement', {
          state: { carts: data.carts, originalQuery: "my weekly list" },
        });
        toast({
          title: 'Comparison ready!',
          description: `Gathered carts from FairPrice and RedMart.`,
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
      {/* [PHASE 0] Demo Mode Notice */}
      <div className="bg-amber-50 border-l-4 border-amber-500 p-4 mb-6 rounded-r-md">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-amber-800">Fixture / Demo Mode Active</h3>
            <div className="mt-2 text-sm text-amber-700">
              <p>
                Live transactions are currently disabled for security refactoring (Phase 0).
                All checkouts will return simulated or <code>NOT_IMPLEMENTED</code> responses.
              </p>
            </div>
          </div>
        </div>
      </div>

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
    </div>
  );
};

export default Index;
