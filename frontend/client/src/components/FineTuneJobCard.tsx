import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import type { FineTuneJob } from "@shared/schema";

interface FineTuneJobCardProps {
  job: FineTuneJob;
}

const statusConfig = {
  preparing: { icon: Loader2, variant: "secondary" as const, animate: true },
  training: { icon: Loader2, variant: "default" as const, animate: true },
  evaluating: { icon: Loader2, variant: "default" as const, animate: true },
  deploying: { icon: Loader2, variant: "default" as const, animate: true },
  completed: { icon: CheckCircle2, variant: "default" as const, animate: false },
  failed: { icon: XCircle, variant: "destructive" as const, animate: false },
};

export function FineTuneJobCard({ job }: FineTuneJobCardProps) {
  const config = statusConfig[job.status as keyof typeof statusConfig] || statusConfig.preparing;
  const Icon = config.icon;

  return (
    <Card data-testid={`card-job-${job.id}`}>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="text-lg font-semibold">{job.baseModel}</CardTitle>
            <p className="text-sm text-muted-foreground">
              Job ID: {job.id.slice(0, 8)}
            </p>
          </div>
          <Badge variant={config.variant} className="text-xs">
            <Icon className={`h-3 w-3 mr-1 ${config.animate ? "animate-spin" : ""}`} />
            {job.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium" data-testid={`text-progress-${job.id}`}>
              {job.progress}%
            </span>
          </div>
          <Progress value={job.progress} />
        </div>

        {job.currentStep && (
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Current Step</p>
            <p className="text-sm font-medium">{job.currentStep}</p>
          </div>
        )}

        {job.logs && (
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Latest Log</p>
            <div className="rounded-md bg-muted p-2">
              <p className="text-xs font-mono text-muted-foreground">{job.logs}</p>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Started: {new Date(job.createdAt).toLocaleString()}</span>
          {job.completedAt && (
            <span>Completed: {new Date(job.completedAt).toLocaleString()}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
