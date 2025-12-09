import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, Zap, Crown, Sparkles } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import axios from 'axios';

interface Plan {
  id: string;
  plan: string;
  name: string;
  description: string;
  price_monthly: number;
  currency: string;
  api_hits_per_month: number;
  model_generation_per_day: number;
  dataset_size_mb: number;
  azure_storage_gb: number;
  training_time_minutes_per_model: number;
  concurrent_trainings: number;
  features: string[];
  priority_support: boolean;
  is_active: boolean;
}

interface SubscriptionPlansProps {
  currentPlan?: string;
  onUpgrade?: (planName: string) => void;
}

const SubscriptionPlans: React.FC<SubscriptionPlansProps> = ({ currentPlan = 'free', onUpgrade }) => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(false);
  const [processingPlan, setProcessingPlan] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/subscriptions/plans', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setPlans(response.data);
    } catch (error) {
      console.error('Failed to fetch plans:', error);
      toast({
        title: 'Error',
        description: 'Failed to load subscription plans',
        variant: 'destructive'
      });
    }
  };

  const getPlanIcon = (planName: string) => {
    switch (planName) {
      case 'free':
        return <Sparkles className="h-6 w-6" />;
      case 'pro':
        return <Zap className="h-6 w-6" />;
      case 'advanced':
        return <Crown className="h-6 w-6" />;
      default:
        return null;
    }
  };

  const getPlanColor = (planName: string) => {
    switch (planName) {
      case 'free':
        return 'text-gray-600';
      case 'pro':
        return 'text-blue-600';
      case 'advanced':
        return 'text-purple-600';
      default:
        return 'text-gray-600';
    }
  };

  const handleUpgrade = async (planName: string) => {
    if (planName === 'free') {
      toast({
        title: 'Info',
        description: 'You are already on the free plan',
        variant: 'default'
      });
      return;
    }

    setProcessingPlan(planName);
    setLoading(true);

    try {
      // Create Razorpay order
      const orderResponse = await axios.post(
        'http://localhost:8000/api/subscriptions/create-order',
        { plan: planName },
        {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }
      );

      const { order_id, amount, currency, key_id } = orderResponse.data;

      // Load Razorpay script
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.async = true;
      document.body.appendChild(script);

      script.onload = () => {
        const options = {
          key: key_id,
          amount: amount * 100, // Convert to paise
          currency: currency,
          name: 'Smart ML Assistant',
          description: `${planName.toUpperCase()} Plan Subscription`,
          order_id: order_id,
          handler: async (response: any) => {
            try {
              // Verify payment
              await axios.post(
                'http://localhost:8000/api/subscriptions/verify-payment',
                {
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature,
                  plan: planName
                },
                {
                  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
                }
              );

              toast({
                title: 'Success!',
                description: `Subscription to ${planName.toUpperCase()} plan activated!`,
                variant: 'default'
              });

              if (onUpgrade) {
                onUpgrade(planName);
              }

              // Reload page to reflect new plan
              setTimeout(() => window.location.reload(), 1500);
            } catch (error: any) {
              toast({
                title: 'Payment Verification Failed',
                description: error.response?.data?.detail || 'Please contact support',
                variant: 'destructive'
              });
            }
          },
          prefill: {
            email: '', // Add user email if available
            contact: '' // Add user phone if available
          },
          theme: {
            color: '#3B82F6'
          },
          modal: {
            ondismiss: () => {
              setLoading(false);
              setProcessingPlan(null);
              toast({
                title: 'Payment Cancelled',
                description: 'You cancelled the payment process',
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
    } finally {
      setLoading(false);
      setProcessingPlan(null);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-7xl mx-auto p-6">
      {plans.map((plan) => {
        const isCurrentPlan = currentPlan === plan.plan;
        const isFree = plan.plan === 'free';

        return (
          <Card
            key={plan.id}
            className={`relative overflow-hidden transition-all hover:shadow-lg ${
              isCurrentPlan ? 'border-2 border-blue-500' : ''
            } ${plan.plan === 'advanced' ? 'md:scale-105' : ''}`}
          >
            {plan.plan === 'advanced' && (
              <div className="absolute top-0 right-0 bg-gradient-to-l from-purple-600 to-blue-600 text-white px-4 py-1 text-xs font-semibold rounded-bl-lg">
                MOST POPULAR
              </div>
            )}

            <CardHeader>
              <div className={`flex items-center gap-2 mb-2 ${getPlanColor(plan.plan)}`}>
                {getPlanIcon(plan.plan)}
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
              </div>
              <CardDescription className="text-sm">{plan.description}</CardDescription>

              <div className="mt-4">
                {isFree ? (
                  <div className="text-4xl font-bold">Free</div>
                ) : (
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-bold">{formatCurrency(plan.price_monthly)}</span>
                    <span className="text-gray-500">/month</span>
                  </div>
                )}
              </div>

              {isCurrentPlan && (
                <Badge variant="secondary" className="mt-2 w-fit">
                  Current Plan
                </Badge>
              )}
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">API Calls/Month</span>
                  <span className="font-semibold">{plan.api_hits_per_month.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Models/Day</span>
                  <span className="font-semibold">{plan.model_generation_per_day}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Dataset Size</span>
                  <span className="font-semibold">{plan.dataset_size_mb} MB</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Cloud Storage</span>
                  <span className="font-semibold">{plan.azure_storage_gb} GB</span>
                </div>
              </div>

              <div className="border-t pt-4">
                <p className="text-xs font-semibold text-gray-700 mb-2">FEATURES</p>
                <ul className="space-y-2">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <Check className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>

            <CardFooter>
              {isCurrentPlan ? (
                <Button disabled className="w-full" variant="outline">
                  Current Plan
                </Button>
              ) : isFree ? (
                <Button disabled className="w-full" variant="outline">
                  Free Forever
                </Button>
              ) : (
                <Button
                  onClick={() => handleUpgrade(plan.plan)}
                  disabled={loading && processingPlan === plan.plan}
                  className={`w-full ${
                    plan.plan === 'advanced'
                      ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700'
                      : ''
                  }`}
                >
                  {loading && processingPlan === plan.plan ? 'Processing...' : 'Upgrade Now'}
                </Button>
              )}
            </CardFooter>
          </Card>
        );
      })}
    </div>
  );
};

export default SubscriptionPlans;
