import { memo } from "react";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Loader2,
  XCircle,
  StopCircle,
  FileText,
  TrendingUp,
} from "lucide-react";
import type { TrainingJob } from "@/lib/types";

interface TrainingJobCardProps {
  job: TrainingJob;
  onCancel?: (jobId: string) => void;
  onViewLogs?: (jobId: string) => void;
  onViewDetails?: (jobId: string) => void;
}

const statusConfig = {
  queued: {
    icon: Clock,
    label: "Queued",
    variant: "secondary" as const,
    color: "text-muted-foreground",
  },
  training: {
    icon: Loader2,
    label: "Training",
    variant: "default" as const,
    color: "text-primary",
    animate: true,
  },
  completed: {
    icon: CheckCircle2,
    label: "Completed",
    variant: "default" as const,
    color: "text-green-500",
  },
  failed: {
    icon: XCircle,
    label: "Failed",
    variant: "destructive" as const,
    color: "text-destructive",
  },
  cancelled: {
    icon: StopCircle,
    label: "Cancelled",
    variant: "secondary" as const,
    color: "text-muted-foreground",
  },
};

export const TrainingJobCard = memo<TrainingJobCardProps>(({
  job,
  onCancel,
  onViewLogs,
  onViewDetails,
}) => {
  const config = statusConfig[job.status];
  const Icon = config.icon;

  const formatDate = (date: string) => {
    return new Date(date).toLocaleString();
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency || "USD",
    }).format(amount);
  };

  const getETA = () => {
    if (!job.estimated_completion) return null;
    const eta = new Date(job.estimated_completion);
    const now = new Date();
    const diff = eta.getTime() - now.getTime();
    if (diff < 0) return "Completing soon";

    const minutes = Math.floor(diff / 60000);
    if (minutes < 60) return `~${minutes}m remaining`;
    const hours = Math.floor(minutes / 60);
    return `~${hours}h ${minutes % 60}m remaining`;
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm truncate">
                {job.job_name}
              </h3>
              <Badge variant={config.variant} className="shrink-0">
                <Icon
                  className={`h-3 w-3 mr-1 ${config.color} ${
                    config.animate ? "animate-spin" : ""
                  }`}
                />
                {config.label}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Model: {job.model_id}
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 pb-3">
        {job.status === "training" && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-medium">{job.progress}%</span>
            </div>
            <Progress value={job.progress} className="h-2" />
            {job.current_epoch && job.total_epochs && (
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>
                  Epoch {job.current_epoch} of {job.total_epochs}
                </span>
                <span>{getETA()}</span>
              </div>
            )}
          </div>
        )}

        {job.metrics && Object.keys(job.metrics).length > 0 && (
          <div className="grid grid-cols-2 gap-3">
            {job.metrics.accuracy !== undefined && (
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Accuracy</p>
                <p className="text-sm font-medium">
                  {(job.metrics.accuracy * 100).toFixed(2)}%
                </p>
              </div>
            )}
            {job.metrics.loss !== undefined && (
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Loss</p>
                <p className="text-sm font-medium">
                  {job.metrics.loss.toFixed(4)}
                </p>
              </div>
            )}
            {job.metrics.validation_accuracy !== undefined && (
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Val. Accuracy</p>
                <p className="text-sm font-medium">
                  {(job.metrics.validation_accuracy * 100).toFixed(2)}%
                </p>
              </div>
            )}
            {job.metrics.validation_loss !== undefined && (
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Val. Loss</p>
                <p className="text-sm font-medium">
                  {job.metrics.validation_loss.toFixed(4)}
                </p>
              </div>
            )}
          </div>
        )}

        {job.cost && (
          <div className="flex items-center justify-between p-2 bg-accent/50 rounded-md">
            <div className="text-xs">
              <p className="text-muted-foreground">Estimated Cost</p>
              <p className="font-medium mt-0.5">
                {formatCurrency(job.cost.estimated, job.cost.currency)}
              </p>
            </div>
            {job.cost.actual > 0 && (
              <div className="text-xs text-right">
                <p className="text-muted-foreground">Actual Cost</p>
                <p className="font-medium mt-0.5">
                  {formatCurrency(job.cost.actual, job.cost.currency)}
                </p>
              </div>
            )}
          </div>
        )}

        {job.error_message && (
          <div className="flex items-start gap-2 p-2 bg-destructive/10 border border-destructive/20 rounded-md">
            <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
            <p className="text-xs text-destructive">{job.error_message}</p>
          </div>
        )}

        <div className="text-xs text-muted-foreground space-y-1">
          <p>Created: {formatDate(job.created_at)}</p>
          {job.started_at && <p>Started: {formatDate(job.started_at)}</p>}
          {job.completed_at && <p>Completed: {formatDate(job.completed_at)}</p>}
        </div>
      </CardContent>

      <CardFooter className="flex gap-2 pt-3 border-t">
        <Button
          size="sm"
          variant="outline"
          onClick={() => onViewDetails?.(job._id)}
          className="flex-1"
        >
          <TrendingUp className="h-3 w-3 mr-1" />
          Details
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onViewLogs?.(job._id)}
        >
          <FileText className="h-3 w-3 mr-1" />
          Logs
        </Button>
        {job.status === "training" && onCancel && (
          <Button
            size="sm"
            variant="destructive"
            onClick={() => onCancel(job._id)}
          >
            <StopCircle className="h-3 w-3 mr-1" />
            Cancel
          </Button>
        )}
      </CardFooter>
    </Card>
  );
});

TrainingJobCard.displayName = "TrainingJobCard";
