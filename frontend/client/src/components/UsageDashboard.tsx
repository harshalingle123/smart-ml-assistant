import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, Database, Zap, HardDrive, TrendingUp, AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import axios from 'axios';

interface UsageData {
  user_id: string;
  subscription_id: string;
  plan: string;
  api_hits_used: number;
  api_hits_limit: number;
  models_trained_today: number;
  models_limit_per_day: number;
  azure_storage_used_mb: number;
  azure_storage_limit_gb: number;
  billing_cycle_start: string;
  billing_cycle_end: string;
  usage_percentage: {
    api_hits: number;
    models: number;
    storage: number;
  };
}

const UsageDashboard: React.FC = () => {
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    fetchUsage();
    // Refresh every 30 seconds
    const interval = setInterval(fetchUsage, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchUsage = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/subscriptions/usage', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setUsage(response.data);
    } catch (error: any) {
      // Handle 401 Unauthorized - redirect to login
      if (error.response?.status === 401) {
        console.warn('[AUTH] Token expired, redirecting to login...');
        localStorage.removeItem('token');
        window.location.href = '/login?message=Session expired. Please log in again.';
        return;
      }
      console.error('Failed to fetch usage:', error);
    } finally {
      setLoading(false);
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getUsageStatus = (percentage: number) => {
    if (percentage >= 90) return { text: 'Critical', color: 'destructive' };
    if (percentage >= 75) return { text: 'Warning', color: 'warning' };
    return { text: 'Healthy', color: 'success' };
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatStorage = (mb: number) => {
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(2)} GB`;
    }
    return `${mb.toFixed(2)} MB`;
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-6">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="pb-2">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-2 bg-gray-200 rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!usage) {
    return (
      <Card className="m-6">
        <CardContent className="pt-6">
          <p className="text-center text-gray-500">Failed to load usage data</p>
        </CardContent>
      </Card>
    );
  }

  const usageStats = [
    {
      icon: <Zap className="h-5 w-5" />,
      title: 'API Hits',
      current: usage.api_hits_used,
      limit: usage.api_hits_limit,
      percentage: usage.usage_percentage.api_hits,
      unit: 'requests'
    },
    {
      icon: <Activity className="h-5 w-5" />,
      title: 'Models Today',
      current: usage.models_trained_today,
      limit: usage.models_limit_per_day,
      percentage: usage.usage_percentage.models,
      unit: 'models'
    },
    {
      icon: <HardDrive className="h-5 w-5" />,
      title: 'Storage Used',
      current: usage.azure_storage_used_mb,
      limit: usage.azure_storage_limit_gb * 1024,
      percentage: usage.usage_percentage.storage,
      unit: 'storage',
      isStorage: true
    }
  ];

  return (
    <div className="space-y-6 p-6">
      {/* Header Card */}
      <Card className="bg-gradient-to-r from-blue-500 to-purple-600 text-white">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">Usage Overview</CardTitle>
              <CardDescription className="text-blue-100 mt-1">
                Current Plan: <span className="font-semibold uppercase">{usage.plan}</span>
              </CardDescription>
            </div>
            <Badge variant="secondary" className="text-sm">
              {formatDate(usage.billing_cycle_start)} - {formatDate(usage.billing_cycle_end)}
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {/* Usage Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {usageStats.map((stat, index) => {
          const status = getUsageStatus(stat.percentage);

          return (
            <Card key={index} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-blue-100 rounded-lg text-blue-600">{stat.icon}</div>
                    <CardTitle className="text-lg">{stat.title}</CardTitle>
                  </div>
                  <Badge variant={status.color as any}>{status.text}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-baseline justify-between">
                  <div>
                    <p className="text-3xl font-bold">
                      {stat.isStorage
                        ? formatStorage(stat.current)
                        : stat.current.toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      of {stat.isStorage ? `${stat.limit / 1024} GB` : stat.limit.toLocaleString()}{' '}
                      {!stat.isStorage && stat.unit}
                    </p>
                  </div>
                  <div className="text-right">
                    <p
                      className={`text-2xl font-bold ${
                        stat.percentage >= 90
                          ? 'text-red-600'
                          : stat.percentage >= 75
                          ? 'text-yellow-600'
                          : 'text-green-600'
                      }`}
                    >
                      {stat.percentage.toFixed(1)}%
                    </p>
                  </div>
                </div>

                <div className="space-y-1">
                  <Progress value={stat.percentage} className="h-2" />
                  {stat.percentage >= 90 && (
                    <div className="flex items-center gap-1 text-xs text-red-600">
                      <AlertCircle className="h-3 w-3" />
                      <span>Limit almost reached. Consider upgrading.</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Upgrade Banner */}
      {(usage.usage_percentage.api_hits >= 80 ||
        usage.usage_percentage.models >= 80 ||
        usage.usage_percentage.storage >= 80) && (
        <Card className="border-yellow-500 bg-yellow-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <TrendingUp className="h-8 w-8 text-yellow-600" />
                <div>
                  <h3 className="font-semibold text-gray-900">
                    You're approaching your plan limits
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Upgrade to a higher plan to continue using advanced features without interruption.
                  </p>
                </div>
              </div>
              <Button className="bg-yellow-600 hover:bg-yellow-700">Upgrade Now</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default UsageDashboard;
