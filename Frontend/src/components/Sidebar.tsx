import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { Home, ChefHat, ShoppingCart, ClipboardPlus, ChevronLeft, ChevronRight, Package, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";

const nav = [
  { to: "/", label: "Home", icon: Home },
  { to: "/inventory", label: "Inventory", icon: ChefHat },
  { to: "/orders", label: "Orders", icon: ShoppingCart },
  { to: "/order-placement", label: "Order Placement", icon: ClipboardPlus },
  { to: "/chat", label: "Chat", icon: MessageSquare },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("sidebar:collapsed") === "1");
  useEffect(() => { localStorage.setItem("sidebar:collapsed", collapsed ? "1" : "0"); }, [collapsed]);

  return (
    <aside className={`h-screen sticky top-0 border-r bg-white/60 dark:bg-black/30 backdrop-blur transition-[width] duration-300 ${collapsed ? "w-16" : "w-64"}`}>
      <div className="h-16 px-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-primary text-white">
            <Package className="h-5 w-5" />
          </div>
          {!collapsed && <span className="font-semibold tracking-tight">TitanStore AI</span>}
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setCollapsed(v => !v)} aria-label="Toggle sidebar">
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      <nav className="px-2 py-2 space-y-1">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors hover:bg-accent/10
               ${isActive ? "bg-accent/20 text-accent-foreground font-medium" : "text-muted-foreground"}`
            }
          >
            <Icon className="h-5 w-5 shrink-0" />
            {!collapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
