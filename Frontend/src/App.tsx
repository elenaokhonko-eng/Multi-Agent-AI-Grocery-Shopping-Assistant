import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import AppLayout from "@/layouts/AppLayout";
import ScrollToTop from "@/components/ScrollToTop";
import Index from "./pages/Index";
import Orders from "./pages/Orders";
import OrderPlacement from "./pages/OrderPlacement";
import KitchenInventoryPage from "./pages/KitchenInventoryPage";
import NotFound from "./pages/NotFound";
import UserProfilePage from "./pages/UserProfile";
import E2EFlow from "./pages/E2EFlow";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <ScrollToTop />
        <Routes>
          {/* Everything below shares Sidebar + Header */}
          <Route element={<AppLayout />}>
            <Route path="/" element={<Index />} />
            <Route path="/inventory" element={<KitchenInventoryPage />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/order-placement" element={<OrderPlacement />} />
            <Route path="/profile" element={<UserProfilePage />} />
            <Route path="/e2e" element={<E2EFlow />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
