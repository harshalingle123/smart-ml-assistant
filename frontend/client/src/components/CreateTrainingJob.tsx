import { memo, useState, useCallback, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { createTrainingJob, getModels, getDatasets } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface CreateTrainingJobProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export const CreateTrainingJob = memo<CreateTrainingJobProps>(({
  open,
  onOpenChange,
  onSuccess,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [models, setModels] = useState<any[]>([]);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    job_name: "",
    model_id: "",
    dataset_id: "",
    learning_rate: "0.0001",
    epochs: "3",
    batch_size: "16",
  });
  const { toast } = useToast();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [modelsData, datasetsData] = await Promise.all([
          getModels(),
          getDatasets(),
        ]);
        setModels(modelsData || []);
        setDatasets(datasetsData || []);
      } catch (error) {
        console.error("Failed to fetch data:", error);
      }
    };

    if (open) {
      fetchData();
    }
  }, [open]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!formData.model_id || !formData.dataset_id || !formData.job_name) {
        toast({
          variant: "destructive",
          title: "Validation error",
          description: "Please fill in all required fields.",
        });
        return;
      }

      setIsLoading(true);

      try {
        await createTrainingJob({
          job_name: formData.job_name,
          model_id: formData.model_id,
          dataset_id: formData.dataset_id,
          hyperparameters: {
            learning_rate: parseFloat(formData.learning_rate),
            epochs: parseInt(formData.epochs, 10),
            batch_size: parseInt(formData.batch_size, 10),
          },
        });

        toast({
          title: "Training job created",
          description: "Your training job has been queued successfully.",
        });

        onOpenChange(false);
        setFormData({
          job_name: "",
          model_id: "",
          dataset_id: "",
          learning_rate: "0.0001",
          epochs: "3",
          batch_size: "16",
        });
        onSuccess?.();
      } catch (error) {
        console.error("Failed to create training job:", error);
        toast({
          variant: "destructive",
          title: "Failed to create job",
          description:
            error instanceof Error
              ? error.message
              : "An error occurred while creating the training job.",
        });
      } finally {
        setIsLoading(false);
      }
    },
    [formData, onOpenChange, onSuccess, toast]
  );

  const handleChange = useCallback(
    (field: string, value: string) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
    },
    []
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create Training Job</DialogTitle>
          <DialogDescription>
            Configure and start a new model training job
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="job_name">
              Job Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="job_name"
              placeholder="e.g., sentiment-analysis-v1"
              value={formData.job_name}
              onChange={(e) => handleChange("job_name", e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="model_id">
                Model <span className="text-destructive">*</span>
              </Label>
              <Select
                value={formData.model_id}
                onValueChange={(value) => handleChange("model_id", value)}
                disabled={isLoading}
                required
              >
                <SelectTrigger id="model_id">
                  <SelectValue placeholder="Select a model">
                    {formData.model_id
                      ? models.find((m) => (m._id || m.id) === formData.model_id)?.name ||
                        models.find((m) => (m._id || m.id) === formData.model_id)?.model_id ||
                        "Select a model"
                      : "Select a model"
                    }
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {models.length === 0 ? (
                    <SelectItem value="" disabled>
                      No models available
                    </SelectItem>
                  ) : (
                    models.map((model) => (
                      <SelectItem key={model._id || model.id} value={model._id || model.id}>
                        {model.name || model.model_id}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="dataset_id">
                Dataset <span className="text-destructive">*</span>
              </Label>
              <Select
                value={formData.dataset_id}
                onValueChange={(value) => handleChange("dataset_id", value)}
                disabled={isLoading}
                required
              >
                <SelectTrigger id="dataset_id">
                  <SelectValue placeholder="Select a dataset">
                    {formData.dataset_id
                      ? datasets.find((d) => d._id === formData.dataset_id)?.dataset_title ||
                        datasets.find((d) => d._id === formData.dataset_id)?.name ||
                        "Select a dataset"
                      : "Select a dataset"
                    }
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {datasets.length === 0 ? (
                    <SelectItem value="" disabled>
                      No datasets available
                    </SelectItem>
                  ) : (
                    datasets.map((dataset) => (
                      <SelectItem key={dataset._id} value={dataset._id}>
                        {dataset.dataset_title || dataset.name}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-3 p-4 border rounded-lg bg-accent/50">
            <h4 className="font-medium text-sm">Hyperparameters</h4>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="learning_rate" className="text-xs">
                  Learning Rate
                </Label>
                <Input
                  id="learning_rate"
                  type="number"
                  step="0.0001"
                  min="0.00001"
                  max="0.1"
                  value={formData.learning_rate}
                  onChange={(e) => handleChange("learning_rate", e.target.value)}
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="epochs" className="text-xs">
                  Epochs
                </Label>
                <Input
                  id="epochs"
                  type="number"
                  min="1"
                  max="100"
                  value={formData.epochs}
                  onChange={(e) => handleChange("epochs", e.target.value)}
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="batch_size" className="text-xs">
                  Batch Size
                </Label>
                <Input
                  id="batch_size"
                  type="number"
                  min="1"
                  max="128"
                  value={formData.batch_size}
                  onChange={(e) => handleChange("batch_size", e.target.value)}
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Create Job
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
});

CreateTrainingJob.displayName = "CreateTrainingJob";
