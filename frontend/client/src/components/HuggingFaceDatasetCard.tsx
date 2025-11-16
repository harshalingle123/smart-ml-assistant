import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Database, Loader2, Check, ExternalLink } from "lucide-react";
import { addDatasetFromHuggingFace, getDatasets } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface HuggingFaceDataset {
  name: string;
  url: string;
}

interface HuggingFaceDatasetCardProps {
  dataset: HuggingFaceDataset;
  chatId: string;
  onDatasetAdded?: () => void;
}

export function HuggingFaceDatasetCard({ dataset, chatId, onDatasetAdded }: HuggingFaceDatasetCardProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [isAdded, setIsAdded] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const { toast } = useToast();

  // Check if dataset already exists in user's collection
  useEffect(() => {
    const checkIfDatasetExists = async () => {
      try {
        setIsChecking(true);
        const response = await getDatasets();
        const datasetsList = Array.isArray(response) ? response : (response.datasets || []);

        // Check if any dataset has the same HuggingFace dataset ID
        const exists = datasetsList.some((ds: any) =>
          ds.source === "huggingface" &&
          (ds.huggingface_dataset_id === dataset.name || ds.name === dataset.name)
        );

        if (exists) {
          console.log(`HuggingFace dataset ${dataset.name} already exists in collection`);
          setIsAdded(true);
        }
      } catch (error) {
        console.error("Failed to check if dataset exists:", error);
        // Don't show error to user, just assume it doesn't exist
      } finally {
        setIsChecking(false);
      }
    };

    checkIfDatasetExists();
  }, [dataset.name]);

  const handleAddDataset = async () => {
    setIsAdding(true);
    try {
      await addDatasetFromHuggingFace({
        dataset_name: dataset.name,
        dataset_url: dataset.url,
        chat_id: chatId,
      });

      setIsAdded(true);
      toast({
        title: "Dataset Added Successfully!",
        description: `${dataset.name} has been added to your collection. Check the Datasets tab to view it.`,
      });

      // Call the callback if provided
      if (onDatasetAdded) {
        onDatasetAdded();
      }
    } catch (error) {
      console.error("Failed to add dataset:", error);

      // Parse error message for better user feedback
      let errorMessage = "Failed to add dataset. Please try again.";

      if (error instanceof Error) {
        const msg = error.message.toLowerCase();

        if (msg.includes("not found") || msg.includes("404")) {
          errorMessage = `Dataset '${dataset.name}' not found on HuggingFace. Please check the dataset name.`;
        } else if (msg.includes("private") || msg.includes("invalid link")) {
          errorMessage = "Unable to access dataset. It may be private or the link may be invalid.";
        } else if (msg.includes("timeout")) {
          errorMessage = "Request timeout. Please check your internet connection and try again.";
        } else if (msg.includes("network") || msg.includes("connect")) {
          errorMessage = "Network error. Please check your internet connection.";
        } else {
          errorMessage = error.message;
        }
      }

      toast({
        variant: "destructive",
        title: "Failed to Add Dataset",
        description: errorMessage,
      });
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <Card className="p-4 hover:shadow-md transition-shadow">
      <div className="space-y-3">
        {/* Title */}
        <div>
          <h4 className="font-medium text-sm line-clamp-2">{dataset.name}</h4>
          <div className="flex items-center gap-1 mt-1">
            <Database className="h-3 w-3 text-orange-500" />
            <span className="text-xs text-muted-foreground">HuggingFace Dataset</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={handleAddDataset}
            disabled={isChecking || isAdding || isAdded}
            size="sm"
            className="flex-1"
            variant={isAdded ? "outline" : "default"}
          >
            {isChecking ? (
              <>
                <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
                Checking...
              </>
            ) : isAdding ? (
              <>
                <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
                Adding...
              </>
            ) : isAdded ? (
              <>
                <Check className="h-3.5 w-3.5 mr-2" />
                Added
              </>
            ) : (
              <>
                <Download className="h-3.5 w-3.5 mr-2" />
                Add to Datasets
              </>
            )}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => window.open(dataset.url, '_blank')}
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
