import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import { ShoppingCart, PackageCheck, Loader2, ArrowRight } from "lucide-react";

export default function E2EFlow() {
  const [step, setStep] = useState<"CONFIRM_LIST" | "ORCHESTRATING" | "COMPARISON" | "CONFIRM_CHECKOUT" | "CHECKOUT">("CONFIRM_LIST");
  const [shoppingList, setShoppingList] = useState<{ item: string, quantity: number }[]>([]);
  const [comparisonData, setComparisonData] = useState<any>(null);
  const [checkoutDetails, setCheckoutDetails] = useState<any>(null);
  const [selectedStore, setSelectedStore] = useState<string | null>(null);

  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch list on mount
  useEffect(() => {
    fetch("http://localhost:3004/api/shopping-list")
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch");
        return res.json();
      })
      .then(data => setShoppingList(data))
      .catch(e => {
        console.error(e);
        setErrorMsg(e.message || "Failed to load shopping list. Is the backend running on port 3004?");
      });
  }, []);

  const handleStartOrchestration = async () => {
    setStep("ORCHESTRATING");
    toast("Starting Agents... Watch the Playwright browsers!");
    
    try {
      const res = await fetch("http://localhost:3004/api/orchestrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      
      setComparisonData(data);
      setStep("COMPARISON");
      toast.success("Prices fetched successfully!");
    } catch (error: any) {
      toast.error(error.message || "Failed to orchestrate");
      setStep("CONFIRM_LIST");
    }
  };

  const handleCheckout = async (store: string) => {
    toast(`Fetching checkout summary for ${store}...`);
    try {
      const total = comparisonData.comparisons[store]?.total || 0;
      const subtotal = comparisonData.comparisons[store]?.subtotal || 0;
      const delivery_fee = comparisonData.comparisons[store]?.delivery_fee || 0;
      
      const res = await fetch("http://localhost:3004/api/prepare_checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ store, total, subtotal, delivery_fee })
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      
      setCheckoutDetails(data.details);
      setSelectedStore(store);
      setStep("CONFIRM_CHECKOUT");
    } catch (error: any) {
      toast.error(error.message);
    }
  };

  const handleConfirmCheckout = async () => {
    if (!selectedStore) return;
    toast(`Initiating final checkout with ${selectedStore}... Watch the Playwright browser!`);
    try {
      const res = await fetch("http://localhost:3004/api/confirm_checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          store: selectedStore,
          items: comparisonData.comparisons[selectedStore]?.items || []
        })
      });
      const data = await res.json();
      if (data.status === "error") throw new Error(data.message);
      
      toast.success(data.message, { duration: 10000 });
      setStep("CHECKOUT");
    } catch (error: any) {
      toast.error(error.message);
    }
  };

  return (
    <div className="container mx-auto py-10 max-w-4xl space-y-8 animate-in fade-in duration-500">
      
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold tracking-tight">E2E Autonomous Checkout</h1>
        <div className="flex gap-2">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${step === "CONFIRM_LIST" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>1. List</span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${step === "ORCHESTRATING" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>2. Orchestrating</span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${step === "COMPARISON" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>3. Review</span>
        </div>
      </div>

      {step === "CONFIRM_LIST" && (
        <div className="border rounded-xl p-6 bg-card shadow-sm">
          <h2 className="text-xl font-semibold mb-4">Confirm Shopping List</h2>
          <div className="space-y-2 mb-6">
            {errorMsg && <p className="text-red-500 font-medium">Error: {errorMsg}</p>}
            {!errorMsg && shoppingList.length === 0 && <p className="text-muted-foreground">Loading list...</p>}
            {shoppingList.map((i, idx) => (
              <div key={idx} className="flex justify-between p-3 bg-muted/50 rounded-lg">
                <span className="font-medium">{i.item}</span>
                <span className="text-muted-foreground">Qty: {i.quantity}</span>
              </div>
            ))}
          </div>
          <button 
            onClick={handleStartOrchestration}
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md font-medium flex items-center justify-center gap-2"
          >
            Confirm & Run Agents
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {step === "ORCHESTRATING" && (
        <div className="border rounded-xl p-12 bg-card shadow-sm flex flex-col items-center justify-center text-center space-y-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary" />
          <h2 className="text-2xl font-semibold">Agents are shopping...</h2>
          <p className="text-muted-foreground max-w-md">
            The LangGraph orchestrator is dispatching Playwright bots to FairPrice, RedMart, Sheng Siong, and Little Farms. Watch your terminal and the spawned browsers!
          </p>
        </div>
      )}

      {step === "COMPARISON" && comparisonData && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {["FairPrice", "RedMart", "ShengSiong"].map(store => {
              const data = comparisonData.comparisons[store];
              if (!data) return null;
              const isCheapest = comparisonData.cheapest_store === store;

              return (
                <div key={store} className={`border rounded-xl p-6 relative flex flex-col ${isCheapest ? "ring-2 ring-primary bg-primary/5" : "bg-card"} shadow-sm`}>
                  {isCheapest && (
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider">
                      Cheapest
                    </span>
                  )}
                  <h3 className="text-xl font-bold mb-4">{store}</h3>
                  <div className="space-y-2 mb-4 flex-grow">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Subtotal:</span>
                      <span>${data.subtotal.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Delivery Fee:</span>
                      <span className={data.delivery_fee === 0 ? "text-green-600 font-medium" : ""}>
                        {data.delivery_fee === 0 ? "FREE" : `$${data.delivery_fee.toFixed(2)}`}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground pt-1 border-t mt-2">
                      Free delivery over ${data.free_delivery_threshold.toFixed(2)}
                    </div>
                  </div>
                  
                  <div className="text-sm space-y-1 mb-4 flex-grow border-t pt-2 overflow-y-auto max-h-48">
                    <p className="font-semibold text-xs uppercase text-muted-foreground mb-2">Items Found</p>
                    {data.items && data.items.length > 0 ? (
                      data.items.map((item: any, idx: number) => (
                        <div key={idx} className="flex justify-between items-start gap-2 text-xs">
                          <span className="truncate flex-1" title={item.title || item.item}>{item.title || item.item}</span>
                          <span className="font-medium shrink-0">${(item.price_sgd || item.price || 0).toFixed(2)}</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-muted-foreground italic text-xs">No items found.</p>
                    )}
                    
                    {data.missing_items && data.missing_items.length > 0 && (
                      <>
                        <p className="font-semibold text-xs uppercase text-red-400 mt-4 mb-2">Not Found</p>
                        {data.missing_items.map((missing: string, idx: number) => (
                          <div key={`missing-${idx}`} className="text-red-500/80 line-through text-xs truncate mb-1" title={missing}>
                            {missing}
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                  <div className="pt-4 border-t mt-auto">
                    <div className="flex justify-between font-bold text-lg mb-4">
                      <span>Total:</span>
                      <span>${data.total.toFixed(2)}</span>
                    </div>
                    <button 
                      onClick={() => handleCheckout(store)}
                      className={`w-full py-2 rounded-md font-medium transition-colors ${isCheapest ? "bg-primary text-primary-foreground hover:bg-primary/90" : "bg-secondary text-secondary-foreground hover:bg-secondary/80"}`}
                    >
                      Order from {store}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
          
           {comparisonData.comparisons["LittleFarms"] && (
            <div className="border border-blue-200 bg-blue-50/50 rounded-xl p-6 shadow-sm">
               <h3 className="text-lg font-bold mb-2 flex items-center gap-2 text-blue-900">
                <ShoppingCart className="w-5 h-5" />
                Specialty Order: Little Farms (Salmon)
               </h3>
               <div className="flex items-center justify-between mb-4">
                 <div className="text-sm text-blue-800">
                   Subtotal: ${comparisonData.comparisons["LittleFarms"].subtotal.toFixed(2)} | 
                   Delivery: ${comparisonData.comparisons["LittleFarms"].delivery_fee.toFixed(2)} (Free over $100)
                 </div>
                 <div className="font-bold text-blue-900">
                   Total: ${comparisonData.comparisons["LittleFarms"].total.toFixed(2)}
                 </div>
               </div>
               <button 
                 onClick={() => handleCheckout("LittleFarms")}
                 className="w-full py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition-colors"
               >
                 Order from Little Farms
               </button>
            </div>
          )}
        </div>
      )}

      {step === "CONFIRM_CHECKOUT" && checkoutDetails && (
        <div className="border border-amber-200 bg-amber-50 rounded-xl p-8 shadow-sm max-w-lg mx-auto">
          <h2 className="text-2xl font-bold mb-6 text-amber-900 text-center">Confirm Order Details</h2>
          <div className="space-y-4 text-amber-950">
            <div className="flex justify-between border-b border-amber-200 pb-2">
              <span className="font-medium text-amber-800">Store:</span>
              <span className="font-bold">{selectedStore}</span>
            </div>
            <div className="flex justify-between border-b border-amber-200 pb-2">
              <span className="font-medium text-amber-800">Delivery Address:</span>
              <span className="text-right max-w-[200px]">{checkoutDetails.address}</span>
            </div>
            <div className="flex justify-between border-b border-amber-200 pb-2">
              <span className="font-medium text-amber-800">Payment Method:</span>
              <span className="text-right">{checkoutDetails.payment_method}</span>
            </div>
            <div className="flex justify-between border-b border-amber-200 pb-2 mt-4">
              <span className="font-medium text-amber-800">Subtotal:</span>
              <span>${checkoutDetails.subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between border-b border-amber-200 pb-2">
              <span className="font-medium text-amber-800">Delivery Fee:</span>
              <span>${checkoutDetails.delivery_fee.toFixed(2)}</span>
            </div>
            <div className="flex justify-between font-bold text-xl pt-2">
              <span>Total:</span>
              <span>${checkoutDetails.total.toFixed(2)}</span>
            </div>
          </div>
          
          <div className="flex gap-4 mt-8">
            <button 
              onClick={() => setStep("COMPARISON")}
              className="flex-1 py-3 border border-amber-300 text-amber-800 rounded-md font-medium hover:bg-amber-100 transition-colors"
            >
              Cancel
            </button>
            <button 
              onClick={handleConfirmCheckout}
              className="flex-1 py-3 bg-amber-600 text-white rounded-md font-medium hover:bg-amber-700 transition-colors"
            >
              Confirm & Pay
            </button>
          </div>
        </div>
      )}

      {step === "CHECKOUT" && (
        <div className="border border-green-200 bg-green-50 rounded-xl p-12 shadow-sm flex flex-col items-center justify-center text-center space-y-4">
          <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-2">
             <PackageCheck className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-green-900">Safety Stop Triggered Successfully!</h2>
          <p className="text-green-800 max-w-md">
            The agent successfully spawned a Playwright browser, logged in, added the items to your cart, and paused before submitting final payment. 
          </p>
          <button 
            onClick={() => setStep("CONFIRM_LIST")}
            className="mt-6 px-6 py-2 border border-green-300 text-green-800 rounded-md hover:bg-green-100 font-medium transition-colors"
          >
            Run Again
          </button>
        </div>
      )}

    </div>
  );
}
