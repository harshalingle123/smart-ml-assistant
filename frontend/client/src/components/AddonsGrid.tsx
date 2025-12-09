import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { HardDrive, Zap, Activity, TrendingUp, Plus, Check, X, Info } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import axios from 'axios';
import { getApiUrl } from '@/lib/env';

interface Addon {
  id: string;
  addon_slug: string;
  name: string;
  description: string;
  category: string;
  price_monthly: number;
  currency: string;
  quota_type: string;
  quota_amount: number;
  compatible_plans: string[];
  max_quantity: number;
  is_active: boolean;
  icon?: string;
  badge_text?: string;
}

interface UserAddon {
  id: string;
  addon_id: string;
  addon_name: string;
  addon_description: string;
  quantity: number;
  amount_paid: number;
  currency: string;
  status: string;
  period_start: string;
  period_end: string;
  auto_renew: boolean;
  quota_type: string;
  quota_amount: number;
  total_quota: number;
}

interface CombinedLimits {
  plan: string;
  base_limits: Record<string, number>;
  addon_contributions: Record<string, number>;
  total_limits: Record<string, number>;
  active_addons: UserAddon[];
  addon_count: number;
  total_addon_cost: number;
}

const AddonsGrid: React.FC = () => {
  const [addons, setAddons] = useState<Addon[]>([]);
  const [myAddons, setMyAddons] = useState<UserAddon[]>([]);
  const [combinedLimits, setCombinedLimits] = useState<CombinedLimits | null>(null);
  const [loading, setLoading] = useState(true);
  const [purchasingSlug, setPurchasingSlug] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [addonsRes, myAddonsRes, limitsRes] = await Promise.all([
        axios.get(`${getApiUrl()}/api/addons/`, { headers }),
        axios.get(`${getApiUrl()}/api/addons/my-addons`, { headers }),
        axios.get(`${getApiUrl()}/api/addons/combined-limits`, { headers })
      ]);

      setAddons(addonsRes.data);
      setMyAddons(myAddonsRes.data);
      setCombinedLimits(limitsRes.data);
    } catch (error: any) {
      // Handle 401 Unauthorized - redirect to login
      if (error.response?.status === 401) {
        console.warn('[AUTH] Token expired, redirecting to login...');
        localStorage.removeItem('token');
        window.location.href = '/login?message=Session expired. Please log in again.';
        return;
      }

      console.error('Failed to fetch add-ons:', error);
      toast({
        title: 'Error',
        description: 'Failed to load add-ons',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const getIcon = (iconName?: string) => {
    const icons: Record<string, JSX.Element> = {
      'hard-drive': <HardDrive className="h-5 w-5" />,
      'zap': <Zap className="h-5 w-5" />,
      'activity': <Activity className="h-5 w-5" />,
      'trending-up': <TrendingUp className="h-5 w-5" />
    };
    return icons[iconName || 'hard-drive'] || <HardDrive className="h-5 w-5" />;
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      storage: 'text-blue-600',
      api_hits: 'text-yellow-600',
      training: 'text-green-600',
      support: 'text-purple-600'
    };
    return colors[category] || 'text-gray-600';
  };

  const formatQuotaType = (quotaType: string): string => {
    const labels: Record<string, string> = {
      azure_storage_gb: 'Storage',
      api_hits_per_month: 'API Calls',
      model_generation_per_day: 'Models/Day',
      training_time_minutes_per_model: 'Training Time'
    };
    return labels[quotaType] || quotaType;
  };

  const formatQuotaAmount = (quotaType: string, amount: number): string => {
    if (quotaType === 'azure_storage_gb') {
      return `${amount} GB`;
    } else if (quotaType === 'api_hits_per_month') {
      return `${amount.toLocaleString()} calls`;
    } else if (quotaType === 'model_generation_per_day') {
      return `${amount} models`;
    }
    return `${amount}`;
  };

  const handlePurchase = async (addonSlug: string, quantity: number = 1) => {
    setPurchasingSlug(addonSlug);

    try {
      const token = localStorage.getItem('token');

      // Create order
      const orderResponse = await axios.post(
        `${getApiUrl()}/api/addons/create-order`,
        { addon_slug: addonSlug, quantity },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const { order_id, amount, currency, key_id, addon_name } = orderResponse.data;

      // Load Razorpay script
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.async = true;
      document.body.appendChild(script);

      script.onload = () => {
        const options = {
          key: key_id,
          amount: amount * 100,
          currency: currency,
          name: 'Smart ML Assistant',
          description: `Add-on: ${addon_name} × ${quantity}`,
          order_id: order_id,
          handler: async (response: any) => {
            try {
              await axios.post(
                `${getApiUrl()}/api/addons/verify-payment`,
                {
                  addon_slug: addonSlug,
                  quantity: quantity,
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature
                },
                { headers: { Authorization: `Bearer ${token}` } }
              );

              toast({
                title: 'Success!',
                description: `${addon_name} activated successfully!`
              });

              // Refresh data
              fetchData();
            } catch (error: any) {
              toast({
                title: 'Payment Verification Failed',
                description: error.response?.data?.detail || 'Please contact support',
                variant: 'destructive'
              });
            } finally {
              setPurchasingSlug(null);
            }
          },
          prefill: {
            email: '',
            contact: ''
          },
          theme: {
            color: '#3B82F6'
          },
          modal: {
            ondismiss: () => {
              setPurchasingSlug(null);
              toast({
                title: 'Payment Cancelled',
                description: 'You cancelled the payment',
                variant: 'default'
              });
            }
          }
        };

        const razorpay = new (window as any).Razorpay(options);
        razorpay.open();
      };
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to initiate payment',
        variant: 'destructive'
      });
      setPurchasingSlug(null);
    }
  };

  const getActiveQuantity = (addonSlug: string): number => {
    const addon = addons.find(a => a.addon_slug === addonSlug);
    if (!addon) return 0;

    return myAddons
      .filter(ua => ua.addon_id === addon.id && ua.status === 'active')
      .reduce((sum, ua) => sum + ua.quantity, 0);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Group add-ons by category
  const addonsByCategory: Record<string, Addon[]> = {};
  addons.forEach(addon => {
    if (!addonsByCategory[addon.category]) {
      addonsByCategory[addon.category] = [];
    }
    addonsByCategory[addon.category].push(addon);
  });

  const categoryTitles: Record<string, string> = {
    storage: 'Storage Add-ons',
    api_hits: 'API Call Boosts',
    training: 'Model Training Boosts',
    support: 'Support & Features'
  };

  return (
    <div className="space-y-8 p-6">
      {/* Combined Limits Summary */}
      {combinedLimits && combinedLimits.addon_count > 0 && (
        <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-blue-600" />
              Your Enhanced Limits
            </CardTitle>
            <CardDescription>
              {combinedLimits.plan.toUpperCase()} Plan + {combinedLimits.addon_count} Active Add-on{combinedLimits.addon_count > 1 ? 's' : ''}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">API Calls/Month</p>
                <p className="text-2xl font-bold text-blue-600">
                  {combinedLimits.total_limits.api_hits_per_month?.toLocaleString()}
                </p>
                {combinedLimits.addon_contributions.api_hits_per_month > 0 && (
                  <p className="text-xs text-green-600">
                    +{combinedLimits.addon_contributions.api_hits_per_month?.toLocaleString()} from add-ons
                  </p>
                )}
              </div>
              <div>
                <p className="text-sm text-gray-600">Models/Day</p>
                <p className="text-2xl font-bold text-green-600">
                  {combinedLimits.total_limits.model_generation_per_day}
                </p>
                {combinedLimits.addon_contributions.model_generation_per_day > 0 && (
                  <p className="text-xs text-green-600">
                    +{combinedLimits.addon_contributions.model_generation_per_day} from add-ons
                  </p>
                )}
              </div>
              <div>
                <p className="text-sm text-gray-600">Storage</p>
                <p className="text-2xl font-bold text-purple-600">
                  {combinedLimits.total_limits.azure_storage_gb} GB
                </p>
                {combinedLimits.addon_contributions.azure_storage_gb > 0 && (
                  <p className="text-xs text-green-600">
                    +{combinedLimits.addon_contributions.azure_storage_gb} GB from add-ons
                  </p>
                )}
              </div>
              <div>
                <p className="text-sm text-gray-600">Monthly Add-on Cost</p>
                <p className="text-2xl font-bold text-orange-600">
                  {formatCurrency(combinedLimits.total_addon_cost)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Add-ons */}
      {myAddons.length > 0 && (
        <div>
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Check className="h-5 w-5 text-green-600" />
            Your Active Add-ons
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {myAddons.map((addon) => (
              <Card key={addon.id} className="border-green-500 bg-green-50">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{addon.addon_name}</CardTitle>
                      <Badge variant="secondary" className="mt-2 bg-green-600 text-white">
                        Active
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Quantity:</span>
                    <span className="font-semibold">{addon.quantity}×</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Provides:</span>
                    <span className="font-semibold text-green-600">
                      {formatQuotaAmount(addon.quota_type, addon.total_quota)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Cost:</span>
                    <span className="font-semibold">{formatCurrency(addon.amount_paid)}/mo</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Renews:</span>
                    <span className="font-semibold">
                      {new Date(addon.period_end).toLocaleDateString()}
                    </span>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button variant="outline" size="sm" className="w-full">
                    Manage
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Available Add-ons by Category */}
      {Object.keys(addonsByCategory).map((category) => (
        <div key={category}>
          <h3 className="text-xl font-bold mb-4">{categoryTitles[category] || category}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {addonsByCategory[category].map((addon) => {
              const activeQuantity = getActiveQuantity(addon.addon_slug);
              const canPurchaseMore = activeQuantity < addon.max_quantity;
              const isPurchasing = purchasingSlug === addon.addon_slug;

              return (
                <Card key={addon.id} className="hover:shadow-lg transition-all relative">
                  {addon.badge_text && (
                    <div className="absolute top-0 right-0 bg-gradient-to-l from-blue-600 to-purple-600 text-white px-3 py-1 text-xs font-semibold rounded-bl-lg">
                      {addon.badge_text}
                    </div>
                  )}

                  <CardHeader>
                    <div className={`flex items-center gap-2 mb-2 ${getCategoryColor(addon.category)}`}>
                      {getIcon(addon.icon)}
                      <CardTitle className="text-lg">{addon.name}</CardTitle>
                    </div>
                    <CardDescription className="text-sm">{addon.description}</CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <div className="flex items-baseline gap-1">
                      <span className="text-3xl font-bold">{formatCurrency(addon.price_monthly)}</span>
                      <span className="text-gray-500 text-sm">/month</span>
                    </div>

                    <div className="bg-gray-50 rounded-lg p-3 space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Adds:</span>
                        <span className="font-semibold text-green-600">
                          {formatQuotaAmount(addon.quota_type, addon.quota_amount)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Type:</span>
                        <span className="font-medium">{formatQuotaType(addon.quota_type)}</span>
                      </div>
                    </div>

                    {activeQuantity > 0 && (
                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription>
                          Active: {activeQuantity}× = {formatQuotaAmount(addon.quota_type, addon.quota_amount * activeQuantity)}
                        </AlertDescription>
                      </Alert>
                    )}

                    {addon.max_quantity > 1 && (
                      <p className="text-xs text-gray-500">
                        Max: {addon.max_quantity} per user
                      </p>
                    )}
                  </CardContent>

                  <CardFooter>
                    <Button
                      onClick={() => handlePurchase(addon.addon_slug)}
                      disabled={!canPurchaseMore || isPurchasing}
                      className="w-full"
                    >
                      {isPurchasing ? (
                        <>Processing...</>
                      ) : !canPurchaseMore ? (
                        <>
                          <X className="h-4 w-4 mr-2" />
                          Max Reached
                        </>
                      ) : (
                        <>
                          <Plus className="h-4 w-4 mr-2" />
                          {activeQuantity > 0 ? 'Add More' : 'Purchase'}
                        </>
                      )}
                    </Button>
                  </CardFooter>
                </Card>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};

export default AddonsGrid;
