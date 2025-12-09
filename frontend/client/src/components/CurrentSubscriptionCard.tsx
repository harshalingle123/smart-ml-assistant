import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calendar, CreditCard, AlertCircle, Crown, Sparkles, Zap, TrendingUp } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import axios from 'axios';

interface Subscription {
  id: string;
  plan: string;
  status: string;
  period_start: string;
  period_end: string;
  amount: number;
  currency: string;
  cancel_at_period_end: boolean;
  canceled_at: string | null;
  next_billing_date: string | null;
}

const CurrentSubscriptionCard: React.FC = () => {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [isFree, setIsFree] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchSubscription();
  }, []);

  const fetchSubscription = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        'http://localhost:8000/api/subscriptions/current',
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSubscription(response.data);
      setIsFree(false);
    } catch (error: any) {
      if (error.response?.status === 404) {
        // User is on free plan
        setIsFree(true);
      } else {
        toast({
          title: 'Error',
          description: 'Failed to fetch subscription details',
          variant: 'destructive',
        });
      }
    } finally {
      setLoading(false);
    }
  };


  const getPlanIcon = (plan: string) => {
    switch (plan) {
      case 'free':
        return <Sparkles className="h-5 w-5" />;
      case 'pro':
        return <Zap className="h-5 w-5 text-blue-500" />;
      case 'advanced':
        return <Crown className="h-5 w-5 text-purple-500" />;
      default:
        return <TrendingUp className="h-5 w-5" />;
    }
  };

  const getPlanColor = (plan: string) => {
    switch (plan) {
      case 'free':
        return 'bg-gray-100 text-gray-800';
      case 'pro':
        return 'bg-blue-100 text-blue-800';
      case 'advanced':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-green-100 text-green-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Current Subscription</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isFree) {
    return (
      <Card className="border-2 border-dashed">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getPlanIcon('free')}
              <div>
                <CardTitle>Free Plan</CardTitle>
                <CardDescription>You're currently on the free tier</CardDescription>
              </div>
            </div>
            <Badge className={getPlanColor('free')}>FREE</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-900">
              Upgrade to unlock premium features, higher limits, and priority support!
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-500">API Calls</p>
              <p className="font-semibold">500/month</p>
            </div>
            <div>
              <p className="text-gray-500">Models/Day</p>
              <p className="font-semibold">3/day</p>
            </div>
            <div>
              <p className="text-gray-500">Storage</p>
              <p className="font-semibold">100 MB</p>
            </div>
          </div>

          <Button className="w-full" size="lg">
            Upgrade to Pro
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getPlanIcon(subscription?.plan || '')}
            <div>
              <CardTitle>Current Subscription</CardTitle>
              <CardDescription>Manage your active subscription</CardDescription>
            </div>
          </div>
          <Badge className={getPlanColor(subscription?.plan || '')}>
            {subscription?.plan?.toUpperCase()}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {subscription?.cancel_at_period_end && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-semibold text-amber-900">Subscription Ending</p>
              <p className="text-amber-700">
                Your subscription will be canceled on{' '}
                {subscription.period_end && formatDate(subscription.period_end)}
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Calendar className="h-4 w-4" />
              <span>Billing Cycle</span>
            </div>
            <p className="text-sm font-medium">
              {subscription?.period_start && formatDate(subscription.period_start)} -{' '}
              {subscription?.period_end && formatDate(subscription.period_end)}
            </p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <CreditCard className="h-4 w-4" />
              <span>Amount</span>
            </div>
            <p className="text-sm font-medium">
              {subscription?.currency === 'INR' ? '₹' : '$'}
              {subscription?.amount?.toFixed(2)} / month
            </p>
          </div>
        </div>

        {subscription?.next_billing_date && !subscription?.cancel_at_period_end && (
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600">Next billing date</p>
            <p className="text-base font-semibold text-gray-900">
              {formatDate(subscription.next_billing_date)}
            </p>
          </div>
        )}

        <div className="flex gap-3">
          <Button variant="outline" className="w-full">
            Change Plan
          </Button>
        </div>

        <p className="text-xs text-gray-500 text-center">
          Billing managed securely through Razorpay
        </p>
      </CardContent>
    </Card>
  );
};

export default CurrentSubscriptionCard;
