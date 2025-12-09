import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import SubscriptionPlans from '@/components/SubscriptionPlans';
import UsageDashboard from '@/components/UsageDashboard';
import CurrentSubscriptionCard from '@/components/CurrentSubscriptionCard';
import PaymentHistoryTable from '@/components/PaymentHistoryTable';
import AddonsGrid from '@/components/AddonsGrid';
import { useAuth } from '@/contexts/AuthContext';
import { BarChart3, CreditCard, History, LayoutGrid, Package } from 'lucide-react';

export default function Billing() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Billing & Subscriptions</h1>
        <p className="text-gray-600 mt-2">
          Manage your subscription, monitor usage, and view payment history
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-grid">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <LayoutGrid className="h-4 w-4" />
            <span className="hidden sm:inline">Overview</span>
          </TabsTrigger>
          <TabsTrigger value="usage" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            <span className="hidden sm:inline">Usage</span>
          </TabsTrigger>
          <TabsTrigger value="plans" className="flex items-center gap-2">
            <Package className="h-4 w-4" />
            <span className="hidden sm:inline">Plans</span>
          </TabsTrigger>
          <TabsTrigger value="addons" className="flex items-center gap-2">
            <CreditCard className="h-4 w-4" />
            <span className="hidden sm:inline">Add-ons</span>
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            <span className="hidden sm:inline">History</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 gap-6">
            <CurrentSubscriptionCard />
            <UsageDashboard />
          </div>
        </TabsContent>

        <TabsContent value="usage" className="space-y-6">
          <UsageDashboard />
        </TabsContent>

        <TabsContent value="plans" className="space-y-6">
          <SubscriptionPlans currentPlan={user?.current_plan || 'free'} />
        </TabsContent>

        <TabsContent value="addons" className="space-y-6">
          <AddonsGrid />
        </TabsContent>

        <TabsContent value="history" className="space-y-6">
          <PaymentHistoryTable />
        </TabsContent>
      </Tabs>
    </div>
  );
}
