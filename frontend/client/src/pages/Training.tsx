import { useState, useEffect, useCallback } from "react";
import { TrainingJobCard } from "@/components/TrainingJobCard";
import { CreateTrainingJob } from "@/components/CreateTrainingJob";
import { TrainingLogs } from "@/components/TrainingLogs";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, AlertCircle, RefreshCw } from "lucide-react";
import { getTrainingJobs, cancelTrainingJob } from "@/lib/api";
import type { TrainingJob } from "@/lib/types";
import { useToast } from "@/hooks/use-toast";

export default function Training() {
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [isLogsOpen, setIsLogsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const { toast } = useToast();

  const fetchJobs = useCallback(async () => {
    try {
      setError(null);
      const data = await getTrainingJobs();
      setJobs(data.jobs || []);
    } catch (err) {
      console.error("Failed to fetch training jobs:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load training jobs. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 10000);
    return () => clearInterval(interval);
  }, [fetchJobs]);

  const handleCancelJob = useCallback(
    async (jobId: string) => {
      try {
        await cancelTrainingJob(jobId);
        toast({
          title: "Job cancelled",
          description: "The training job has been cancelled.",
        });
        fetchJobs();
      } catch (error) {
        console.error("Failed to cancel job:", error);
        toast({
          variant: "destructive",
          title: "Failed to cancel job",
          description:
            error instanceof Error
              ? error.message
              : "An error occurred while cancelling the job.",
        });
      }
    },
    [fetchJobs, toast]
  );

  const handleViewLogs = useCallback((jobId: string) => {
    setSelectedJobId(jobId);
    setIsLogsOpen(true);
  }, []);

  const handleViewDetails = useCallback((jobId: string) => {
    console.log("View details for job:", jobId);
  }, []);

  const filterJobs = (status?: string) => {
    if (!status || status === "all") return jobs;
    return jobs.filter((job) => job.status === status);
  };

  const jobCounts = {
    all: jobs.length,
    queued: jobs.filter((j) => j.status === "queued").length,
    training: jobs.filter((j) => j.status === "training").length,
    completed: jobs.filter((j) => j.status === "completed").length,
    failed: jobs.filter((j) => j.status === "failed").length,
  };

  const displayedJobs = filterJobs(activeTab);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Training Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and manage your model training jobs
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => fetchJobs()}
            disabled={isLoading}
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
          <Button onClick={() => setIsCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-1" />
            New Training Job
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">
            All {jobCounts.all > 0 && `(${jobCounts.all})`}
          </TabsTrigger>
          <TabsTrigger value="queued">
            Queued {jobCounts.queued > 0 && `(${jobCounts.queued})`}
          </TabsTrigger>
          <TabsTrigger value="training">
            Training {jobCounts.training > 0 && `(${jobCounts.training})`}
          </TabsTrigger>
          <TabsTrigger value="completed">
            Completed {jobCounts.completed > 0 && `(${jobCounts.completed})`}
          </TabsTrigger>
          <TabsTrigger value="failed">
            Failed {jobCounts.failed > 0 && `(${jobCounts.failed})`}
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-6">
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="space-y-3 border rounded-lg p-4">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-8 w-full" />
                </div>
              ))}
            </div>
          ) : displayedJobs.length === 0 ? (
            <div className="text-center py-12 border rounded-lg bg-muted/30">
              <p className="text-muted-foreground">
                {activeTab === "all"
                  ? "No training jobs yet. Create your first training job to get started."
                  : `No ${activeTab} jobs.`}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {displayedJobs.map((job) => (
                <TrainingJobCard
                  key={job._id}
                  job={job}
                  onCancel={handleCancelJob}
                  onViewLogs={handleViewLogs}
                  onViewDetails={handleViewDetails}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      <CreateTrainingJob
        open={isCreateOpen}
        onOpenChange={setIsCreateOpen}
        onSuccess={fetchJobs}
      />

      <TrainingLogs
        jobId={selectedJobId}
        open={isLogsOpen}
        onOpenChange={setIsLogsOpen}
      />
    </div>
  );
}
