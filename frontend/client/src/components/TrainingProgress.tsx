import { memo, useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Clock,
  DollarSign,
  Loader2,
  StopCircle,
  TrendingUp,
  Activity,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { getTrainingJob, getTrainingLogs, cancelTrainingJob } from '@/lib/api';
import type { TrainingJob, TrainingLog } from '@/lib/types';

interface TrainingProgressProps {
  jobId: string;
  onCancel?: () => void;
  onComplete?: (job: TrainingJob) => void;
  pollingInterval?: number;
}

export const TrainingProgress = memo<TrainingProgressProps>(({
  jobId,
  onCancel,
  onComplete,
  pollingInterval = 3000,
}) => {
  const [job, setJob] = useState<TrainingJob | null>(null);
  const [logs, setLogs] = useState<TrainingLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCancelling, setIsCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchJobData = useCallback(async () => {
    try {
      const [jobData, logsData] = await Promise.all([
        getTrainingJob(jobId),
        getTrainingLogs(jobId),
      ]);
      setJob(jobData);
      setLogs(logsData.logs || []);
      setError(null);

      if (jobData.status === 'completed' && onComplete) {
        onComplete(jobData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch training data');
    } finally {
      setIsLoading(false);
    }
  }, [jobId, onComplete]);

  useEffect(() => {
    fetchJobData();

    if (!job || job.status === 'training' || job.status === 'queued') {
      const interval = setInterval(fetchJobData, pollingInterval);
      return () => clearInterval(interval);
    }
  }, [fetchJobData, job, pollingInterval]);

  const handleCancel = async () => {
    setIsCancelling(true);
    try {
      await cancelTrainingJob(jobId);
      await fetchJobData();
      onCancel?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel training');
    } finally {
      setIsCancelling(false);
    }
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const getTimeRemaining = () => {
    if (!job?.estimated_completion) return null;
    const eta = new Date(job.estimated_completion);
    const now = new Date();
    const diff = eta.getTime() - now.getTime();

    if (diff < 0) return 'Completing soon';

    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);

    if (hours > 0) return `${hours}h ${minutes}m remaining`;
    if (minutes > 0) return `${minutes}m ${seconds}s remaining`;
    return `${seconds}s remaining`;
  };

  const getCurrentPhase = () => {
    if (!job) return 'Initializing';

    switch (job.status) {
      case 'queued':
        return 'Waiting in queue';
      case 'training':
        if (job.current_epoch && job.total_epochs) {
          return `Training model (Epoch ${job.current_epoch}/${job.total_epochs})`;
        }
        return 'Training model';
      case 'completed':
        return 'Training complete';
      case 'failed':
        return 'Training failed';
      case 'cancelled':
        return 'Training cancelled';
      default:
        return 'Initializing';
    }
  };

  const getStatusBadge = () => {
    if (!job) return null;

    const statusConfig = {
      queued: { icon: Clock, label: 'Queued', className: 'bg-blue-500' },
      training: { icon: Loader2, label: 'Training', className: 'bg-primary animate-pulse' },
      completed: { icon: CheckCircle2, label: 'Completed', className: 'bg-green-500' },
      failed: { icon: AlertCircle, label: 'Failed', className: 'bg-destructive' },
      cancelled: { icon: StopCircle, label: 'Cancelled', className: 'bg-muted' },
    };

    const config = statusConfig[job.status];
    const Icon = config.icon;

    return (
      <Badge className={config.className}>
        <Icon className={`h-3 w-3 mr-1 ${job.status === 'training' ? 'animate-spin' : ''}`} />
        {config.label}
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading training progress...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="flex items-center gap-3 py-6">
          <AlertCircle className="h-5 w-5 text-destructive shrink-0" />
          <div className="flex-1">
            <p className="font-medium text-destructive">Error loading training data</p>
            <p className="text-sm text-muted-foreground mt-1">{error}</p>
          </div>
          <Button variant="outline" size="sm" onClick={fetchJobData}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!job) return null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              <span className="truncate">{job.job_name}</span>
            </CardTitle>
            <CardDescription className="mt-1">
              Model: {job.model_id} • Dataset: {job.dataset_id}
            </CardDescription>
          </div>
          {getStatusBadge()}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">{getCurrentPhase()}</span>
            <span className="text-muted-foreground">{job.progress}%</span>
          </div>

          <Progress value={job.progress} className="h-3" />

          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              <span>{getTimeRemaining() || 'Calculating...'}</span>
            </div>
            {job.current_epoch && job.total_epochs && (
              <span>
                Step {job.current_epoch} of {job.total_epochs}
              </span>
            )}
          </div>
        </div>

        <Separator />

        <div className="grid grid-cols-2 gap-4">
          {job.metrics?.accuracy !== undefined && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <TrendingUp className="h-3.5 w-3.5" />
                <span>Training Accuracy</span>
              </div>
              <p className="text-2xl font-bold">
                {(job.metrics.accuracy * 100).toFixed(2)}%
              </p>
            </div>
          )}

          {job.metrics?.loss !== undefined && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Activity className="h-3.5 w-3.5" />
                <span>Training Loss</span>
              </div>
              <p className="text-2xl font-bold">{job.metrics.loss.toFixed(4)}</p>
            </div>
          )}

          {job.metrics?.validation_accuracy !== undefined && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Validation Accuracy</span>
              </div>
              <p className="text-2xl font-bold">
                {(job.metrics.validation_accuracy * 100).toFixed(2)}%
              </p>
            </div>
          )}

          {job.metrics?.validation_loss !== undefined && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <AlertCircle className="h-3.5 w-3.5" />
                <span>Validation Loss</span>
              </div>
              <p className="text-2xl font-bold">
                {job.metrics.validation_loss.toFixed(4)}
              </p>
            </div>
          )}
        </div>

        {job.cost && (
          <>
            <Separator />
            <div className="bg-accent/50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Cost Tracking</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">Estimated</p>
                  <p className="text-lg font-semibold mt-1">
                    {formatCurrency(job.cost.estimated, job.cost.currency)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Actual</p>
                  <p className="text-lg font-semibold mt-1">
                    {formatCurrency(job.cost.actual, job.cost.currency)}
                  </p>
                </div>
              </div>
              {job.cost.actual > job.cost.estimated && (
                <div className="flex items-start gap-2 mt-3 p-2 bg-amber-500/10 border border-amber-500/20 rounded-md">
                  <AlertCircle className="h-3.5 w-3.5 text-amber-500 shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-700 dark:text-amber-400">
                    Cost exceeds estimate by{' '}
                    {formatCurrency(job.cost.actual - job.cost.estimated, job.cost.currency)}
                  </p>
                </div>
              )}
            </div>
          </>
        )}

        <Separator />

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Live Training Logs</span>
            <Badge variant="secondary" className="text-xs">
              {logs.length} entries
            </Badge>
          </div>

          <ScrollArea className="h-64 rounded-md border bg-muted/30 p-4">
            {logs.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <p className="text-sm text-muted-foreground">No logs available yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {logs.map((log, index) => (
                  <div
                    key={index}
                    className={`text-xs font-mono p-2 rounded ${
                      log.level === 'error'
                        ? 'bg-destructive/10 text-destructive'
                        : log.level === 'warning'
                        ? 'bg-amber-500/10 text-amber-700 dark:text-amber-400'
                        : 'text-foreground/80'
                    }`}
                  >
                    <span className="text-muted-foreground">
                      [{new Date(log.timestamp).toLocaleTimeString()}]
                    </span>{' '}
                    {log.message}
                    {log.metrics && (
                      <div className="mt-1 pl-4 text-primary">
                        {JSON.stringify(log.metrics, null, 2)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>

        {job.error_message && (
          <div className="flex items-start gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
            <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-destructive">Error Details</p>
              <p className="text-xs text-destructive/80 mt-1">{job.error_message}</p>
            </div>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex gap-2 border-t pt-4">
        {(job.status === 'training' || job.status === 'queued') && (
          <Button
            variant="destructive"
            size="sm"
            onClick={handleCancel}
            disabled={isCancelling}
            className="ml-auto"
          >
            {isCancelling ? (
              <>
                <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                Cancelling...
              </>
            ) : (
              <>
                <StopCircle className="h-3 w-3 mr-2" />
                Cancel Training
              </>
            )}
          </Button>
        )}

        {job.status === 'completed' && (
          <div className="flex gap-2 ml-auto">
            <Button variant="outline" size="sm">
              View Results
            </Button>
            <Button size="sm">Deploy Model</Button>
          </div>
        )}
      </CardFooter>
    </Card>
  );
});

TrainingProgress.displayName = 'TrainingProgress';
