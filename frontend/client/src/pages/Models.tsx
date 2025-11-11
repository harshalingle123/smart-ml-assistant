import { ModelCard } from "@/components/ModelCard";
import { MOCK_MODELS } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export default function Models() {
  const handleDownload = (id: string) => {
    console.log("Download model:", id);
  };

  const handleGenerateAPI = (id: string) => {
    console.log("Generate API for model:", id);
  };

  const handleDelete = (id: string) => {
    console.log("Delete model:", id);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">My Models</h1>
          <p className="text-muted-foreground mt-1">
            Manage your fine-tuned models and deployments
          </p>
        </div>
        <Button data-testid="button-new-model">
          <Plus className="h-4 w-4 mr-1" />
          New Model
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {MOCK_MODELS.map((model) => (
          <ModelCard
            key={model.id}
            model={model}
            onDownload={handleDownload}
            onGenerateAPI={handleGenerateAPI}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  );
}
