import { KitchenInventory } from "@/components/KitchenInventory";

export default function KitchenInventoryPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Kitchen Inventory</h1>
      <KitchenInventory showHeader={false} />
    </div>
  );
}
