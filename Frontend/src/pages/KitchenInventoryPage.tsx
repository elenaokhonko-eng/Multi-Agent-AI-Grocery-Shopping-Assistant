import { KitchenInventory } from "@/components/KitchenInventory";

export default function KitchenInventoryPage() {
  return (
    <div className="space-y-8">
      {/* Modern page header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-white/80 to-blue-50/60 backdrop-blur-xl border border-white/30 rounded-3xl p-8 shadow-xl">
        {/* Background decoration */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-200/20 to-purple-200/20 rounded-full blur-2xl"></div>
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-br from-green-200/20 to-emerald-200/20 rounded-full blur-xl"></div>
        
        <div className="relative z-10">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-800 via-blue-700 to-purple-700 bg-clip-text text-transparent mb-2">
            Kitchen Inventory
          </h1>
          <p className="text-gray-600 text-lg">
            Manage your ingredients and track expiration dates with smart insights
          </p>
        </div>
      </div>
      
      <KitchenInventory showHeader={false} />
    </div>
  );
}
