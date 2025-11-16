import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, TrendingUp, Star, Database, Loader2, Check } from "lucide-react";
import { addDatasetFromKaggle, getDatasets } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface KaggleDataset {
  ref: string;
  title: string;
  size: number;
  last_updated: string;
  download_count: number;
  vote_count: number;
  usability_rating: number;
}

interface KaggleDatasetCardProps {
  dataset: KaggleDataset;
  chatId: string;
  onDatasetAdded?: () => void;
}

export function KaggleDatasetCard({ dataset, chatId, onDatasetAdded }: KaggleDatasetCardProps) {
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

        // Check if any dataset has the same kaggle_ref
        const exists = datasetsList.some((ds: any) => ds.kaggle_ref === dataset.ref);

        if (exists) {
          console.log(`Dataset ${dataset.ref} already exists in collection`);
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
  }, [dataset.ref]);

  const handleAddDataset = async () => {
    setIsAdding(true);
    try {
      await addDatasetFromKaggle({
        dataset_ref: dataset.ref,
        dataset_title: dataset.title,
        dataset_size: dataset.size,
        chat_id: chatId,
      });

      setIsAdded(true);
      toast({
        title: "Dataset Added Successfully!",
        description: `${dataset.title} has been added to your collection. Check the Datasets tab to view it.`,
      });

      // Call the callback if provided
      if (onDatasetAdded) {
        onDatasetAdded();
      }
    } catch (error) {
      console.error("Failed to add dataset:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to add dataset. Please try again.",
      });
    } finally {
      setIsAdding(false);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  return (
    <Card className="p-4 hover:shadow-md transition-shadow">
      <div className="space-y-3">
        {/* Title and Reference */}
        <div>
          <h4 className="font-medium text-sm line-clamp-1">{dataset.title}</h4>
          <p className="text-xs text-muted-foreground font-mono mt-1">{dataset.ref}</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-2">
          {/* Size */}
          <div className="flex items-center gap-1.5 text-xs">
            <Database className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-muted-foreground">Size:</span>
            <span className="font-medium">{formatSize(dataset.size)}</span>
          </div>

          {/* Downloads */}
          <div className="flex items-center gap-1.5 text-xs">
            <Download className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-muted-foreground">Downloads:</span>
            <span className="font-medium">{formatNumber(dataset.download_count)}</span>
          </div>

          {/* Votes */}
          <div className="flex items-center gap-1.5 text-xs">
            <TrendingUp className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-muted-foreground">Votes:</span>
            <span className="font-medium">{formatNumber(dataset.vote_count)}</span>
          </div>

          {/* Usability Rating */}
          <div className="flex items-center gap-1.5 text-xs">
            <Star className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-muted-foreground">Quality:</span>
            <Badge variant="secondary" className="h-5 px-1.5 text-xs">
              {dataset.usability_rating.toFixed(2)}
            </Badge>
          </div>
        </div>

        {/* Add Button */}
        <Button
          onClick={handleAddDataset}
          disabled={isChecking || isAdding || isAdded}
          size="sm"
          className="w-full"
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
              Adding Dataset...
            </>
          ) : isAdded ? (
            <>
              <Check className="h-3.5 w-3.5 mr-2" />
              Already in Datasets
            </>
          ) : (
            <>
              <Download className="h-3.5 w-3.5 mr-2" />
              Add to My Datasets
            </>
          )}
        </Button>
      </div>
    </Card>
  );
}
