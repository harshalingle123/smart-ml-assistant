import { useState } from "react";
import { FineTuneJobCard } from "@/components/FineTuneJobCard";
import { FineTuneModal } from "@/components/FineTuneModal";
import { MOCK_FINE_TUNE_JOBS, MOCK_DATASETS, BASE_MODELS } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export default function FineTune() {
  const [modalOpen, setModalOpen] = useState(false);

  const handleStartFineTune = (config: any) => {
    console.log("Start fine-tune with config:", config);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Fine-tune Jobs</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and manage your model fine-tuning jobs
          </p>
        </div>
        <Button onClick={() => setModalOpen(true)} data-testid="button-new-fine-tune">
          <Plus className="h-4 w-4 mr-1" />
          New Fine-tune Job
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {MOCK_FINE_TUNE_JOBS.map((job) => (
          <FineTuneJobCard key={job.id} job={job} />
        ))}
      </div>

      <FineTuneModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        datasets={MOCK_DATASETS.map((d) => ({ id: d.id, name: d.name }))}
        baseModels={BASE_MODELS}
        onStartFineTune={handleStartFineTune}
      />
    </div>
  );
}
