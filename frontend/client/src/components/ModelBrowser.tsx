import { useState, useEffect, memo } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Zap, Target, DollarSign, Clock, CheckCircle2, Sparkles } from 'lucide-react';
import type { DirectAccessModel } from '@/lib/types';

interface ModelBrowserProps {
  models: DirectAccessModel[];
  loading?: boolean;
  onRequestAccess: (modelId: string) => void;
  selectedTask?: string;
  onTaskChange?: (task: string) => void;
  selectedPriority?: string;
  onPriorityChange?: (priority: string) => void;
}

const ModelBrowserSkeleton = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {[1, 2, 3, 4, 5, 6].map((i) => (
      <Card key={i}>
        <CardHeader>
          <Skeleton className="h-6 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </CardContent>
        <CardFooter>
          <Skeleton className="h-10 w-full" />
        </CardFooter>
      </Card>
    ))}
  </div>
);

const ModelCard = memo<{ model: DirectAccessModel; onRequestAccess: (modelId: string) => void }>(
  ({ model, onRequestAccess }) => {
    const isFreeTier = model.free_tier > 0;
    const pricingPerK = (model.pricing.per_request * 1000).toFixed(2);

    return (
      <Card className="hover-elevate flex flex-col">
        <CardHeader>
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              <CardTitle className="text-lg font-semibold">{model.name}</CardTitle>
              <CardDescription className="mt-1">{model.task}</CardDescription>
            </div>
            {isFreeTier && (
              <Badge variant="secondary" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">
                <Sparkles className="h-3 w-3 mr-1" />
                Free Tier
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="flex-1 space-y-4">
          {model.description && (
            <p className="text-sm text-muted-foreground">{model.description}</p>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Target className="h-3 w-3" />
                Accuracy
              </div>
              <p className="text-sm font-semibold">{(model.accuracy * 100).toFixed(0)}%</p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                Latency
              </div>
              <p className="text-sm font-semibold">{model.latency_ms}ms</p>
            </div>
          </div>

          {isFreeTier && (
            <div className="bg-muted/50 rounded-md p-3 space-y-1">
              <div className="flex items-center gap-1 text-xs font-medium">
                <CheckCircle2 className="h-3 w-3 text-green-600 dark:text-green-400" />
                Free Tier
              </div>
              <p className="text-sm font-semibold">
                {model.free_tier.toLocaleString()} requests/month
              </p>
            </div>
          )}

          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <DollarSign className="h-3 w-3" />
              Pricing
            </div>
            <p className="text-sm">
              {isFreeTier ? 'Free, then ' : ''}
              <span className="font-semibold">${pricingPerK}</span> per 1K requests
            </p>
          </div>

          {model.languages && model.languages.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {model.languages.slice(0, 3).map((lang) => (
                <Badge key={lang} variant="outline" className="text-xs">
                  {lang}
                </Badge>
              ))}
              {model.languages.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{model.languages.length - 3}
                </Badge>
              )}
            </div>
          )}
        </CardContent>

        <CardFooter>
          <Button
            onClick={() => onRequestAccess(model.id)}
            className="w-full"
            variant={isFreeTier ? 'default' : 'outline'}
          >
            <Zap className="h-4 w-4 mr-2" />
            Request Access
          </Button>
        </CardFooter>
      </Card>
    );
  }
);

ModelCard.displayName = 'ModelCard';

export const ModelBrowser = memo<ModelBrowserProps>(
  ({ models, loading, onRequestAccess, selectedTask, onTaskChange, selectedPriority, onPriorityChange }) => {
    const [filteredModels, setFilteredModels] = useState<DirectAccessModel[]>(models);

    useEffect(() => {
      let filtered = [...models];

      if (selectedTask && selectedTask !== 'all') {
        filtered = filtered.filter((m) => m.task === selectedTask);
      }

      if (selectedPriority) {
        switch (selectedPriority) {
          case 'speed':
            filtered.sort((a, b) => a.latency_ms - b.latency_ms);
            break;
          case 'accuracy':
            filtered.sort((a, b) => b.accuracy - a.accuracy);
            break;
          case 'cost':
            filtered.sort((a, b) => {
              const aCost = a.free_tier > 0 ? 0 : a.pricing.per_request;
              const bCost = b.free_tier > 0 ? 0 : b.pricing.per_request;
              return aCost - bCost;
            });
            break;
        }
      }

      setFilteredModels(filtered);
    }, [models, selectedTask, selectedPriority]);

    const tasks = Array.from(new Set(models.map((m) => m.task)));

    if (loading) {
      return <ModelBrowserSkeleton />;
    }

    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Select value={selectedTask} onValueChange={onTaskChange}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by task" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tasks</SelectItem>
                {tasks.map((task) => (
                  <SelectItem key={task} value={task}>
                    {task.charAt(0).toUpperCase() + task.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex-1">
            <Select value={selectedPriority} onValueChange={onPriorityChange}>
              <SelectTrigger>
                <SelectValue placeholder="Sort by priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="speed">Speed (Fastest First)</SelectItem>
                <SelectItem value="accuracy">Accuracy (Highest First)</SelectItem>
                <SelectItem value="cost">Cost (Free First)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {filteredModels.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed rounded-lg">
            <p className="text-muted-foreground">No models found matching your filters</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredModels.map((model) => (
              <ModelCard key={model.id} model={model} onRequestAccess={onRequestAccess} />
            ))}
          </div>
        )}
      </div>
    );
  }
);

ModelBrowser.displayName = 'ModelBrowser';
