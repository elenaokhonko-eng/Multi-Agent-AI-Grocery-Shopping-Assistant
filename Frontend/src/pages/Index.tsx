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
