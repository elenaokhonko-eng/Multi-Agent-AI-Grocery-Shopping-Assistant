import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import { ShoppingCart, PackageCheck, Loader2, ArrowRight } from "lucide-react";
import { formatCents } from "../lib/utils";

interface ComparisonItem {
  name?: string;
  title?: string;
  price_cents?: number;
}

interface StoreComparison {
  total_cents?: number;
  subtotal_cents?: number;
  delivery_fee_cents?: number;
  items?: ComparisonItem[];
}

interface ComparisonData {
  comparisons?: Record<string, StoreComparison>;
  cheapest_store?: string;
  error?: string;
}

interface CheckoutDetails {
  shipping_address?: string;
  payment_method?: string;
}

export default function E2EFlow() {
  const [step, setStep] = useState<"CONFIRM_LIST" | "ORCHESTRATING" | "COMPARISON" | "CONFIRM_CHECKOUT" | "CHECKOUT">("CONFIRM_LIST");
  const [shoppingList, setShoppingList] = useState<{ item: string, quantity: number }[]>([]);
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [checkoutDetails, setCheckoutDetails] = useState<CheckoutDetails | null>(null);
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
      .catch((e: unknown) => {
        const msg = e instanceof Error ? e.message : "Failed to load shopping list";
        setErrorMsg(msg);
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
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : "Failed to orchestrate";
      toast.error(msg);
      setStep("CONFIRM_LIST");
    }
  };

  const handleCheckout = async (store: string) => {
    toast(`Fetching checkout summary for ${store}...`);
    try {
      const storeComp = comparisonData?.comparisons?.[store];
      const total_cents = storeComp?.total_cents || 0;
      const subtotal_cents = storeComp?.subtotal_cents || 0;
      const delivery_fee_cents = storeComp?.delivery_fee_cents || 0;
      
      const res = await fetch("http://localhost:3004/api/prepare_checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ store, total_cents, subtotal_cents, delivery_fee_cents })
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      
      setCheckoutDetails(data.details);
      setSelectedStore(store);
      setStep("CONFIRM_CHECKOUT");
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : "Failed to fetch checkout";
      toast.error(msg);
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
          items: comparisonData?.comparisons?.[selectedStore]?.items || []
        })
      });
      const data = await res.json();
      if (data.status === "error") throw new Error(data.message);
      
      toast.success(data.message, { duration: 10000 });
      setStep("CHECKOUT");
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : "Checkout error";
      toast.error(msg);
    }
  };

  return (
    <div className="container mx-auto py-10 max-w-4xl space-y-8 animate-in fade-in duration-500">
      
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold tracking-tight">E2E Autonomous Checkout</h1>
        <div className="flex gap-2">
          {["CONFIRM_LIST", "ORCHESTRATING", "COMPARISON", "CONFIRM_CHECKOUT", "CHECKOUT"].map((s, idx) => (
            <div 
              key={s} 
              className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                step === s ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
              }`}
            >
              {idx + 1}. {s.replace("_", " ")}
            </div>
          ))}
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
          {errorMsg}
        </div>
      )}

      {/* STEP 1: Shopping List Confirmation */}
      {step === "CONFIRM_LIST" && (
        <div className="bg-card border rounded-xl p-6 shadow-sm space-y-6">
          <div className="flex items-center gap-3 border-b pb-4">
            <ShoppingCart className="w-5 h-5 text-primary" />
            <h2 className="text-xl font-semibold">Step 1: Your Target Shopping List</h2>
          </div>

          <div className="divide-y">
            {shoppingList.length === 0 ? (
              <p className="text-muted-foreground py-4">Loading shopping list items...</p>
            ) : (
              shoppingList.map((item, idx) => (
                <div key={idx} className="flex justify-between py-3">
                  <span className="font-medium text-foreground">{item.item}</span>
                  <span className="text-muted-foreground">Qty: {item.quantity}</span>
                </div>
              ))
            )}
          </div>

          <button
            onClick={handleStartOrchestration}
            disabled={shoppingList.length === 0}
            className="w-full bg-primary text-primary-foreground font-semibold py-3 rounded-lg flex items-center justify-center gap-2 hover:bg-primary/90 transition shadow"
          >
            Start Parallel Playwright Scrapers <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* STEP 2: Scrapers Running */}
      {step === "ORCHESTRATING" && (
        <div className="bg-card border rounded-xl p-12 text-center shadow-sm space-y-4">
          <Loader2 className="w-10 h-10 animate-spin mx-auto text-primary" />
          <h2 className="text-2xl font-bold">Autonomous Agents Scraping...</h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            Parallel Playwright instances have launched. They are searching for target items and building baskets live on FairPrice and Little Farms.
          </p>
        </div>
      )}

      {/* STEP 3: Multi-store Comparison */}
      {step === "COMPARISON" && comparisonData && (
        <div className="space-y-6">
          <div className="bg-primary/10 border border-primary/20 rounded-xl p-4 flex justify-between items-center">
            <div>
              <h3 className="font-semibold text-primary">Recommendation Engine</h3>
              <p className="text-sm text-muted-foreground">
                Optimal store selected based on cart subtotal & delivery thresholds.
              </p>
            </div>
            <div className="text-right">
              <span className="text-xs uppercase font-bold text-muted-foreground">Best Value</span>
              <p className="text-xl font-bold text-primary">{comparisonData.cheapest_store}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {comparisonData.comparisons && Object.entries(comparisonData.comparisons).map(([store, info]) => {
              const isCheapest = store === comparisonData.cheapest_store;
              return (
                <div 
                  key={store} 
                  className={`bg-card border rounded-xl p-6 shadow-sm space-y-4 flex flex-col justify-between ${
                    isCheapest ? "border-primary ring-2 ring-primary/20" : ""
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <h3 className="text-lg font-bold capitalize">{store}</h3>
                      {isCheapest && (
                        <span className="bg-primary text-primary-foreground text-xs font-semibold px-2 py-0.5 rounded-full">
                          Cheapest Option
                        </span>
                      )}
                    </div>

                    <div className="text-2xl font-bold">
                      {formatCents(info?.total_cents || 0)}
                    </div>

                    <div className="text-xs space-y-1 text-muted-foreground border-t pt-2">
                      <div className="flex justify-between">
                        <span>Items Subtotal:</span>
                        <span>{formatCents(info?.subtotal_cents || 0)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Delivery Fee:</span>
                        <span>{formatCents(info?.delivery_fee_cents || 0)}</span>
                      </div>
                    </div>

                    <div className="border-t pt-2">
                      <span className="text-xs font-semibold text-muted-foreground block mb-2">Cart Lines:</span>
                      <ul className="text-xs space-y-1">
                        {info?.items?.map((it, idx) => (
                          <li key={idx} className="flex justify-between text-muted-foreground">
                            <span className="truncate max-w-[200px]">{it.name || it.title}</span>
                            <span>{formatCents(it.price_cents || 0)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <button
                    onClick={() => handleCheckout(store)}
                    className={`w-full py-2.5 rounded-lg font-semibold flex items-center justify-center gap-2 transition ${
                      isCheapest 
                        ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow" 
                        : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                    }`}
                  >
                    Select {store} for Checkout <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* STEP 4: Confirm Checkout & Address */}
      {step === "CONFIRM_CHECKOUT" && checkoutDetails && (
        <div className="bg-card border rounded-xl p-6 shadow-sm space-y-6 max-w-xl mx-auto">
          <div className="border-b pb-4">
            <h2 className="text-xl font-bold">Pre-Flight Checkout Validation</h2>
            <p className="text-sm text-muted-foreground">
              Reviewing authenticated account state for <span className="capitalize font-semibold text-foreground">{selectedStore}</span>.
            </p>
          </div>

          <div className="space-y-4 text-sm bg-muted/40 p-4 rounded-lg">
            <div>
              <span className="text-xs font-semibold text-muted-foreground uppercase">Extracted Shipping Address</span>
              <p className="font-medium text-foreground mt-0.5">{checkoutDetails.shipping_address || "Loaded via Playwright profile"}</p>
            </div>
            <div className="border-t pt-3">
              <span className="text-xs font-semibold text-muted-foreground uppercase">Payment Method</span>
              <p className="font-medium text-foreground mt-0.5">{checkoutDetails.payment_method || "Account Default Saved Card"}</p>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => setStep("COMPARISON")}
              className="flex-1 bg-secondary text-secondary-foreground font-semibold py-2.5 rounded-lg hover:bg-secondary/80"
            >
              Back
            </button>
            <button
              onClick={handleConfirmCheckout}
              className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-lg flex items-center justify-center gap-2 shadow"
            >
              Place Live Order <PackageCheck className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: Final Placement & Order Receipt */}
      {step === "CHECKOUT" && (
        <div className="bg-card border rounded-xl p-10 text-center shadow-sm space-y-4 max-w-lg mx-auto">
          <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-950/40 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
            <PackageCheck className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold text-emerald-600">Order Placed Successfully!</h2>
          <p className="text-muted-foreground text-sm">
            Playwright has executed the final checkout click and saved the official order confirmation from {selectedStore}.
          </p>
          <button
            onClick={() => setStep("CONFIRM_LIST")}
            className="mt-4 bg-primary text-primary-foreground font-semibold px-6 py-2 rounded-lg hover:bg-primary/90"
          >
            Start New Workflow
          </button>
        </div>
      )}

    </div>
  );
}
