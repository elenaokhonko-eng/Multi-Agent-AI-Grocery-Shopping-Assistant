import { Outlet } from "react-router-dom";
import Sidebar from "@/components/Sidebar";
import { Header } from "@/components/Header";

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar />
      <div className="flex-1 min-w-0 flex flex-col">
        <Header />
        <main className="container mx-auto px-4 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
