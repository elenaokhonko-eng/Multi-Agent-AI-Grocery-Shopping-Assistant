import { Header } from "@/components/Header";
import { KitchenInventory } from "@/components/KitchenInventory";
import { Link } from "react-router-dom";

export default function KitchenInventoryPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="container mx-auto px-4 py-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Kitchen Inventory</h1>
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border hover:bg-accent/10"
          >
            ← Home
          </Link>
        </div>

        {/* Full-page inventory (hide internal mini-header) */}
        <KitchenInventory showHeader={false} />
      </div>
    </div>
  );
}
