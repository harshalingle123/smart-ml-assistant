import { memo, useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, Info, AlertTriangle, Loader2 } from "lucide-react";
import { getTrainingLogs } from "@/lib/api";
import type { TrainingLog } from "@/lib/types";

interface TrainingLogsProps {
  jobId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const levelConfig = {
  info: {
    icon: Info,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    label: "INFO",
  },
  warning: {
    icon: AlertTriangle,
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
    label: "WARN",
  },
  error: {
    icon: AlertCircle,
    color: "text-destructive",
    bgColor: "bg-destructive/10",
    label: "ERROR",
  },
};

export const TrainingLogs = memo<TrainingLogsProps>(({
  jobId,
  open,
  onOpenChange,
}) => {
  const [logs, setLogs] = useState<TrainingLog[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!open || !jobId) return;

    const fetchLogs = async () => {
      setIsLoading(true);
      try {
        const data = await getTrainingLogs(jobId);
        setLogs(data.logs || []);
      } catch (error) {
        console.error("Failed to fetch logs:", error);
        setLogs([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLogs();

    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [jobId, open]);

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Training Logs</DialogTitle>
          <DialogDescription>
            Real-time logs from your training job
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="h-[60vh] w-full rounded-md border bg-muted/30 p-4">
          {isLoading && logs.length === 0 ? (
            <div className="space-y-2">
              {[...Array(10)].map((_, i) => (
                <Skeleton key={i} className="h-6 w-full" />
              ))}
            </div>
          ) : logs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <p className="text-sm">No logs available yet</p>
            </div>
          ) : (
            <div className="space-y-2 font-mono text-xs">
              {logs.map((log, index) => {
                const config = levelConfig[log.level];
                const Icon = config.icon;

                return (
                  <div
                    key={index}
                    className={`flex items-start gap-2 p-2 rounded ${config.bgColor}`}
                  >
                    <Icon className={`h-4 w-4 ${config.color} shrink-0 mt-0.5`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge
                          variant="outline"
                          className={`text-xs ${config.color}`}
                        >
                          {config.label}
                        </Badge>
                        <span className="text-muted-foreground">
                          {formatTimestamp(log.timestamp)}
                        </span>
                      </div>
                      <p className="break-words">{log.message}</p>
                      {log.metrics && Object.keys(log.metrics).length > 0 && (
                        <div className="mt-2 pl-4 border-l-2 border-muted">
                          {Object.entries(log.metrics).map(([key, value]) => (
                            <div key={key} className="text-muted-foreground">
                              {key}: {JSON.stringify(value)}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
              {isLoading && (
                <div className="flex items-center gap-2 text-muted-foreground p-2">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span>Loading more logs...</span>
                </div>
              )}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
});

TrainingLogs.displayName = "TrainingLogs";
