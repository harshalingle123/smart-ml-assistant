import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { ModelCard } from "@/components/ModelCard";
import { Button } from "@/components/ui/button";
import { Plus, Loader2 } from "lucide-react";
import { getModels, downloadModel, deleteModel } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface Model {
  _id: string;
  id?: string;
  userId: string;
  name: string;
  baseModel: string;
  version: string;
  accuracy: string;
  f1Score?: string;
  loss: string;
  status: string;
  datasetId?: string;
  taskType?: string;
  createdAt: string;
}

export default function Models() {
  const [, setLocation] = useLocation();
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      const data = await getModels();
      setModels(data);
    } catch (error) {
      console.error("Failed to load models:", error);
      toast({
        title: "Error",
        description: "Failed to load models",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (id: string) => {
    try {
      toast({
        title: "Download Started",
        description: "Preparing model for download...",
      });

      await downloadModel(id);

      toast({
        title: "Download Complete",
        description: "Model downloaded successfully",
      });
    } catch (error) {
      console.error("Failed to download model:", error);
      toast({
        title: "Download Failed",
        description: error instanceof Error ? error.message : "Failed to download model",
        variant: "destructive",
      });
    }
  };

  const handleGenerateAPI = (id: string) => {
    // Navigate to model detail page
    setLocation(`/models/${id}`);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this model?")) {
      return;
    }

    try {
      await deleteModel(id);

      toast({
        title: "Model Deleted",
        description: "Model has been permanently deleted",
      });

      // Reload models list
      loadModels();
    } catch (error) {
      console.error("Failed to delete model:", error);
      toast({
        title: "Delete Failed",
        description: error instanceof Error ? error.message : "Failed to delete model",
        variant: "destructive",
      });
    }
  };

  const handleViewDetails = (id: string) => {
    setLocation(`/models/${id}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading models...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">My Models</h1>
          <p className="text-muted-foreground mt-1">
            Manage your trained models and deployments
          </p>
        </div>
        <Button data-testid="button-new-model" onClick={() => setLocation("/datasets")}>
          <Plus className="h-4 w-4 mr-1" />
          Train New Model
        </Button>
      </div>

      {models.length === 0 ? (
        <div className="text-center p-12 border-2 border-dashed rounded-lg">
          <h3 className="text-lg font-semibold mb-2">No models yet</h3>
          <p className="text-muted-foreground mb-4">
            Train your first model by uploading a dataset and starting AutoML training
          </p>
          <Button onClick={() => setLocation("/datasets")}>
            <Plus className="h-4 w-4 mr-2" />
            Go to Datasets
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {models.map((model) => (
            <ModelCard
              key={model._id || model.id}
              model={{
                id: model._id || model.id!,
                name: model.name,
                baseModel: model.baseModel,
                status: model.status,
                accuracy: model.accuracy,
                loss: model.loss,
                createdAt: model.createdAt,
                taskType: model.taskType,
              }}
              onDownload={handleDownload}
              onGenerateAPI={handleGenerateAPI}
              onDelete={handleDelete}
              onClick={handleViewDetails}
            />
          ))}
        </div>
      )}
    </div>
  );
}
