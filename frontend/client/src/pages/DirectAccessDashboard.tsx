import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Loader2,
  Copy,
  CheckCircle2,
  Activity,
  Clock,
  DollarSign,
  TrendingUp,
  Key,
  Trash2,
  AlertCircle,
} from 'lucide-react';
import { UsageChart } from '@/components/UsageChart';
import { getDirectAccessKeys, getUsageStatistics, getCostBreakdown, revokeDirectAccessKey } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import type { DirectAccessKey, UsageStatistics, CostBreakdown } from '@/lib/types';

export default function DirectAccessDashboard() {
  const [apiKeys, setApiKeys] = useState<DirectAccessKey[]>([]);
  const [statistics, setStatistics] = useState<UsageStatistics | null>(null);
  const [costs, setCosts] = useState<CostBreakdown | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState<'24h' | '7d' | '30d'>('7d');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadDashboardData();
  }, [timeframe]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [keysRes, statsRes, costsRes] = await Promise.allSettled([
        getDirectAccessKeys(),
        getUsageStatistics(timeframe),
        getCostBreakdown(),
      ]);

      if (keysRes.status === 'fulfilled') {
        setApiKeys(keysRes.value.keys || []);
      } else {
        setApiKeys(getMockKeys());
      }

      if (statsRes.status === 'fulfilled') {
        setStatistics(statsRes.value);
      } else {
        setStatistics(getMockStatistics());
      }

      if (costsRes.status === 'fulfilled') {
        setCosts(costsRes.value);
      } else {
        setCosts(getMockCosts());
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setApiKeys(getMockKeys());
      setStatistics(getMockStatistics());
      setCosts(getMockCosts());
      toast({
        title: 'Info',
        description: 'Loading demo data. Backend integration pending.',
      });
    } finally {
      setLoading(false);
    }
  };

  const getMockKeys = (): DirectAccessKey[] => [
    {
      _id: '1',
      api_key: 'mlai_test_abc123def456ghi789jkl012',
      model_id: 'vader',
      model_name: 'VADER Sentiment',
      task: 'sentiment',
      usage_plan: 'free',
      free_tier_limit: 10000,
      requests_used: 2450,
      requests_this_month: 2450,
      rate_limit: 100,
      status: 'active',
      endpoint: 'https://api.yourplatform.com/v1/sentiment/vader',
      created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      _id: '2',
      api_key: 'mlai_test_xyz789uvw456rst123opq890',
      model_id: 'distilbert',
      model_name: 'DistilBERT Sentiment',
      task: 'sentiment',
      usage_plan: 'pay_as_you_go',
      free_tier_limit: 1000,
      requests_used: 1850,
      requests_this_month: 1850,
      rate_limit: 50,
      status: 'active',
      endpoint: 'https://api.yourplatform.com/v1/sentiment/distilbert',
      created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    },
  ];

  const getMockStatistics = (): UsageStatistics => ({
    total_requests: 4300,
    successful_requests: 4245,
    failed_requests: 55,
    average_latency_ms: 42,
    by_model: {
      vader: {
        requests: 2450,
        cost: 0,
        free_tier_used: 2450,
        free_tier_remaining: 7550,
      },
      distilbert: {
        requests: 1850,
        cost: 0.51,
        free_tier_used: 1000,
        free_tier_remaining: 0,
      },
    },
    time_series: Array.from({ length: 14 }, (_, i) => ({
      timestamp: new Date(Date.now() - (13 - i) * 24 * 60 * 60 * 1000).toISOString(),
      requests: Math.floor(Math.random() * 500) + 200,
    })),
  });

  const getMockCosts = (): CostBreakdown => ({
    current_month: {
      total_cost: 0.51,
      free_tier_used: 3450,
      paid_requests: 850,
    },
    projected_month: {
      estimated_cost: 1.12,
      based_on_current_rate: true,
    },
    by_model: {
      vader: { cost: 0, requests: 2450 },
      distilbert: { cost: 0.51, requests: 1850 },
    },
  });

  const handleCopyKey = (apiKey: string, keyId: string) => {
    navigator.clipboard.writeText(apiKey);
    setCopiedKey(keyId);
    setTimeout(() => setCopiedKey(null), 2000);
    toast({
      title: 'Copied',
      description: 'API key copied to clipboard',
    });
  };

  const handleRevokeKey = async (keyId: string) => {
    try {
      await revokeDirectAccessKey(keyId);
      toast({
        title: 'Success',
        description: 'API key revoked successfully',
      });
      await loadDashboardData();
    } catch (error) {
      toast({
        title: 'Demo Mode',
        description: 'Key revocation will work when backend is connected',
        variant: 'destructive',
      });
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Direct Access Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Monitor your API usage, costs, and manage your access keys
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statistics?.total_requests.toLocaleString() || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {statistics?.successful_requests || 0} successful
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statistics?.average_latency_ms || 0}ms</div>
            <p className="text-xs text-muted-foreground mt-1">Response time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(costs?.current_month.total_cost || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">This month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Projected Cost</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(costs?.projected_month.estimated_cost || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Month-end estimate</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="usage" className="space-y-4">
        <TabsList>
          <TabsTrigger value="usage">Usage</TabsTrigger>
          <TabsTrigger value="keys">API Keys</TabsTrigger>
          <TabsTrigger value="costs">Costs</TabsTrigger>
        </TabsList>

        <TabsContent value="usage" className="space-y-4">
          <div className="flex items-center gap-2">
            <Button
              variant={timeframe === '24h' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeframe('24h')}
            >
              24 Hours
            </Button>
            <Button
              variant={timeframe === '7d' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeframe('7d')}
            >
              7 Days
            </Button>
            <Button
              variant={timeframe === '30d' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeframe('30d')}
            >
              30 Days
            </Button>
          </div>

          {statistics && (
            <UsageChart
              data={statistics.time_series}
              timeframe={timeframe}
              title="API Requests Over Time"
              description={`Showing ${timeframe} of request activity`}
            />
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {statistics &&
              Object.entries(statistics.by_model).map(([modelId, data]) => (
                <Card key={modelId}>
                  <CardHeader>
                    <CardTitle className="text-lg capitalize">{modelId}</CardTitle>
                    <CardDescription>Usage details for this model</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Total Requests</span>
                      <span className="font-semibold">{data.requests.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Free Tier Used</span>
                      <span className="font-semibold">{data.free_tier_used.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Free Tier Remaining</span>
                      <span className="font-semibold text-green-600">
                        {data.free_tier_remaining.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between pt-2 border-t">
                      <span className="text-sm text-muted-foreground">Cost</span>
                      <span className="font-semibold">{formatCurrency(data.cost)}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
          </div>
        </TabsContent>

        <TabsContent value="keys" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                Your API Keys
              </CardTitle>
              <CardDescription>Manage your direct access API keys</CardDescription>
            </CardHeader>
            <CardContent>
              {apiKeys.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed rounded-lg">
                  <Key className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No API keys yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Generate your first API key to get started
                  </p>
                  <Button>Generate API Key</Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Model</TableHead>
                      <TableHead>API Key</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Usage</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {apiKeys.map((key) => (
                      <TableRow key={key._id}>
                        <TableCell className="font-medium">
                          <div>
                            <p className="font-semibold">{key.model_name}</p>
                            <p className="text-xs text-muted-foreground capitalize">{key.task}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <code className="text-xs bg-muted px-2 py-1 rounded">
                              {key.api_key.substring(0, 20)}...
                            </code>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleCopyKey(key.api_key, key._id)}
                            >
                              {copiedKey === key._id ? (
                                <CheckCircle2 className="h-4 w-4 text-green-600" />
                              ) : (
                                <Copy className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={key.status === 'active' ? 'default' : 'secondary'}
                            className={
                              key.status === 'active'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100'
                                : ''
                            }
                          >
                            {key.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-semibold">
                              {key.requests_this_month.toLocaleString()}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              of {key.free_tier_limit.toLocaleString()}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>
                          {new Date(key.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleRevokeKey(key._id)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="costs" className="space-y-4">
          {costs && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Current Month</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Total Cost</span>
                      <span className="text-2xl font-bold">
                        {formatCurrency(costs.current_month.total_cost)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Free Tier Used</span>
                      <span className="font-semibold">
                        {costs.current_month.free_tier_used.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Paid Requests</span>
                      <span className="font-semibold">
                        {costs.current_month.paid_requests.toLocaleString()}
                      </span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Projected Month-End</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Estimated Cost</span>
                      <span className="text-2xl font-bold">
                        {formatCurrency(costs.projected_month.estimated_cost)}
                      </span>
                    </div>
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-xs">
                        Based on your current usage rate over the past{' '}
                        {costs.projected_month.based_on_current_rate ? '7 days' : '30 days'}
                      </AlertDescription>
                    </Alert>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Cost Breakdown by Model</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Model</TableHead>
                        <TableHead>Requests</TableHead>
                        <TableHead className="text-right">Cost</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {Object.entries(costs.by_model).map(([modelId, data]) => (
                        <TableRow key={modelId}>
                          <TableCell className="font-medium capitalize">{modelId}</TableCell>
                          <TableCell>{data.requests.toLocaleString()}</TableCell>
                          <TableCell className="text-right font-semibold">
                            {formatCurrency(data.cost)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
