import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { ThemeProvider } from "@/components/ThemeProvider";
import { ThemeToggle } from "@/components/ThemeToggle";
import { AppSidebar } from "@/components/AppSidebar";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import Chat from "@/pages/Chat";
import Models from "@/pages/Models";
import ModelDetail from "@/pages/ModelDetail";
import Datasets from "@/pages/Datasets";
import DatasetDetails from "@/pages/DatasetDetails";
import FineTune from "@/pages/FineTune";
import Billing from "@/pages/Billing";
import Chats from "@/pages/Chats";
import NotFound from "@/pages/not-found";
import Settings from "@/pages/Settings";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import ForgotPassword from "@/pages/ForgotPassword";

function ProtectedLayout() {
  const style = {
    "--sidebar-width": "16rem",
    "--sidebar-width-icon": "4rem",
  };

  return (
    <ProtectedRoute>
      <SidebarProvider style={style as React.CSSProperties}>
        <div className="flex h-screen w-full">
          <AppSidebar />
          <div className="flex flex-col flex-1 overflow-hidden">
            <header className="flex items-center justify-between h-16 px-4 border-b bg-background">
              <SidebarTrigger data-testid="button-sidebar-toggle" />
              <ThemeToggle />
            </header>
            <main className="flex-1 overflow-auto">
              <Switch>
                <Route path="/" component={Chat} />
                <Route path="/chats" component={Chats} />
                <Route path="/models/:id" component={ModelDetail} />
                <Route path="/models" component={Models} />
                <Route path="/datasets/:id" component={DatasetDetails} />
                <Route path="/datasets" component={Datasets} />
                <Route path="/fine-tune" component={FineTune} />
                <Route path="/billing" component={Billing} />
                <Route path="/settings" component={Settings} />
                <Route component={NotFound} />
              </Switch>
            </main>
          </div>
        </div>
      </SidebarProvider>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <ThemeProvider>
          <AuthProvider>
            <Switch>
              <Route path="/login" component={Login} />
              <Route path="/register" component={Register} />
              <Route path="/forgot-password" component={ForgotPassword} />
              <Route>
                <ProtectedLayout />
              </Route>
            </Switch>
            <Toaster />
          </AuthProvider>
        </ThemeProvider>
      </TooltipProvider>
    </QueryClientProvider>
  );
}
