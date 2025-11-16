import { useState, useMemo, memo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Calculator, DollarSign, TrendingDown, TrendingUp } from 'lucide-react';
import type { DirectAccessModel } from '@/lib/types';

interface CostCalculatorProps {
  models: DirectAccessModel[];
}

interface CostEstimate {
  freeTierRequests: number;
  paidRequests: number;
  monthlyCost: number;
  costPerRequest: number;
  freeTierValue: number;
  totalValue: number;
}

export const CostCalculator = memo<CostCalculatorProps>(({ models }) => {
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [requestsPerMonth, setRequestsPerMonth] = useState<string>('10000');

  const selectedModel = models.find((m) => m.id === selectedModelId);

  const estimate = useMemo<CostEstimate | null>(() => {
    if (!selectedModel) return null;

    const totalRequests = parseInt(requestsPerMonth) || 0;
    const freeTierRequests = Math.min(totalRequests, selectedModel.free_tier);
    const paidRequests = Math.max(0, totalRequests - selectedModel.free_tier);
    const monthlyCost = paidRequests * selectedModel.pricing.per_request;
    const costPerRequest = totalRequests > 0 ? monthlyCost / totalRequests : 0;
    const freeTierValue = freeTierRequests * selectedModel.pricing.per_request;
    const totalValue = totalRequests * selectedModel.pricing.per_request;

    return {
      freeTierRequests,
      paidRequests,
      monthlyCost,
      costPerRequest,
      freeTierValue,
      totalValue,
    };
  }, [selectedModel, requestsPerMonth]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(amount);
  };

  const getSavingsPercentage = () => {
    if (!estimate || estimate.totalValue === 0) return 0;
    return ((estimate.freeTierValue / estimate.totalValue) * 100).toFixed(0);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calculator className="h-5 w-5" />
          Cost Calculator
        </CardTitle>
        <CardDescription>
          Estimate your monthly costs based on expected usage
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="model-calc-select">Select Model</Label>
            <Select value={selectedModelId} onValueChange={setSelectedModelId}>
              <SelectTrigger id="model-calc-select">
                <SelectValue placeholder="Choose a model..." />
              </SelectTrigger>
              <SelectContent>
                {models.map((model) => (
                  <SelectItem key={model.id} value={model.id}>
                    {model.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="requests-input">Expected Requests per Month</Label>
            <Input
              id="requests-input"
              type="number"
              min="0"
              step="1000"
              value={requestsPerMonth}
              onChange={(e) => setRequestsPerMonth(e.target.value)}
              placeholder="10000"
            />
          </div>
        </div>

        {selectedModel && estimate && (
          <>
            <Separator />

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Estimated Monthly Cost</p>
                  <p className="text-3xl font-bold">{formatCurrency(estimate.monthlyCost)}</p>
                </div>
                <DollarSign className="h-8 w-8 text-muted-foreground" />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="border rounded-lg p-4 space-y-1">
                  <p className="text-xs text-muted-foreground">Free Tier</p>
                  <p className="text-xl font-bold text-green-600 dark:text-green-400">
                    {estimate.freeTierRequests.toLocaleString()}
                  </p>
                  <p className="text-xs text-muted-foreground">requests</p>
                </div>

                <div className="border rounded-lg p-4 space-y-1">
                  <p className="text-xs text-muted-foreground">Paid</p>
                  <p className="text-xl font-bold">
                    {estimate.paidRequests.toLocaleString()}
                  </p>
                  <p className="text-xs text-muted-foreground">requests</p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-muted-foreground">Cost per request</span>
                  <span className="font-medium">{formatCurrency(estimate.costPerRequest)}</span>
                </div>

                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-muted-foreground">Free tier value</span>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">
                      <TrendingDown className="h-3 w-3 mr-1" />
                      {getSavingsPercentage()}% saved
                    </Badge>
                    <span className="font-medium">{formatCurrency(estimate.freeTierValue)}</span>
                  </div>
                </div>

                <Separator />

                <div className="flex items-center justify-between py-2">
                  <span className="text-sm font-medium">Total if paying for all</span>
                  <span className="font-bold">{formatCurrency(estimate.totalValue)}</span>
                </div>
              </div>

              {estimate.monthlyCost === 0 && (
                <div className="bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg p-4">
                  <p className="text-sm font-medium text-green-800 dark:text-green-200">
                    Your usage is covered entirely by the free tier!
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                    You can make {estimate.freeTierRequests.toLocaleString()} requests per month at no cost.
                  </p>
                </div>
              )}
            </div>

            <Separator />

            <div className="space-y-3">
              <h4 className="text-sm font-semibold">Model Details</h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="space-y-1">
                  <p className="text-muted-foreground">Task</p>
                  <p className="font-medium capitalize">{selectedModel.task}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Accuracy</p>
                  <p className="font-medium">{(selectedModel.accuracy * 100).toFixed(0)}%</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Latency</p>
                  <p className="font-medium">{selectedModel.latency_ms}ms</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Rate per 1K</p>
                  <p className="font-medium">
                    {formatCurrency(selectedModel.pricing.per_request * 1000)}
                  </p>
                </div>
              </div>
            </div>
          </>
        )}

        {!selectedModel && (
          <div className="flex items-center justify-center py-12 border-2 border-dashed rounded-lg">
            <p className="text-sm text-muted-foreground">
              Select a model to calculate costs
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
});

CostCalculator.displayName = 'CostCalculator';
