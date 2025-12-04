import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, Database, Loader2, Check, ExternalLink, Star, HardDrive } from "lucide-react";
import { addDatasetFromHuggingFace, getDatasets, downloadDatasetWithProgress } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface HuggingFaceDataset {
  name: string;
  url: string;
  downloads?: number;
  relevance_score?: number;
  id?: string;
  title?: string;
  size?: number;
  size_str?: string;
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
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const { toast } = useToast();

  // Validate and construct proper HuggingFace URL
  const getHuggingFaceUrl = (): string => {
    if (dataset.url && dataset.url.startsWith('http')) {
      return dataset.url;
    }
    // Fallback: construct from id or name
    const datasetId = dataset.id || dataset.name;
    if (datasetId) {
      return `https://huggingface.co/datasets/${datasetId}`;
    }
    return dataset.url || '#';
  };

  const huggingFaceUrl = getHuggingFaceUrl();

  // Check if dataset already exists in user's collection
  useEffect(() => {
    const checkIfDatasetExists = async () => {
      try {
        setIsChecking(true);
        const response = await getDatasets();
        const datasetsList = Array.isArray(response) ? response : (response.datasets || []);

        // Check if any dataset has the same HuggingFace dataset ID (check both snake_case and camelCase)
        const exists = datasetsList.some((ds: any) =>
          ds.source === "huggingface" &&
          (ds.huggingfaceDatasetId === dataset.name ||
           ds.huggingface_dataset_id === dataset.name ||
           ds.name === dataset.name)
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
    setDownloadProgress(0);

    try {
      // Start adding dataset
      const response = await addDatasetFromHuggingFace({
        dataset_name: dataset.name,
        dataset_url: dataset.url,
        chat_id: chatId,
      });

      // Store the dataset ID for download
      if (response && response.id) {
        setDatasetId(response.id);
      }

      // Now download the actual dataset with real-time progress
      setIsDownloading(true);

      const cleanup = downloadDatasetWithProgress(
        response.id || dataset.name,
        "HuggingFace",
        (progress, message) => {
          // Real-time progress update from backend
          setDownloadProgress(progress);
          console.log(`Download progress: ${progress}% - ${message}`);
        },
        (result) => {
          // Download completed successfully
          setIsAdded(true);
          toast({
            title: "Dataset Downloaded Successfully!",
            description: `${dataset.name} has been downloaded and added to your collection.`,
          });

          // Call the callback if provided
          if (onDatasetAdded) {
            onDatasetAdded();
          }

          setIsAdding(false);
          setIsDownloading(false);
          setTimeout(() => setDownloadProgress(0), 1000);
        },
        (errorMsg) => {
          // Download error
          console.error("Download failed:", errorMsg);
          setIsAdded(true);
          toast({
            title: "Dataset Added (Download Pending)",
            description: `${dataset.name} metadata added. Download will happen when you inspect or train.`,
          });

          setIsAdding(false);
          setIsDownloading(false);
          setTimeout(() => setDownloadProgress(0), 1000);
        }
      );

      // Store cleanup function (optional: for cancellation support)
      return cleanup;

    } catch (error) {
      console.error("Failed to add dataset:", error);
      setDownloadProgress(0);

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

      setIsAdding(false);
      setIsDownloading(false);
      setTimeout(() => setDownloadProgress(0), 1000);
    }
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const formatSize = (bytes?: number, sizeStr?: string): string => {
    if (sizeStr && sizeStr !== "Unknown") {
      return sizeStr;
    }
    if (!bytes || bytes === 0) {
      return "Unknown";
    }
    const gb = bytes / (1024 * 1024 * 1024);
    if (gb >= 1) {
      return `${gb.toFixed(2)} GB`;
    }
    const mb = bytes / (1024 * 1024);
    if (mb >= 1) {
      return `${mb.toFixed(2)} MB`;
    }
    const kb = bytes / 1024;
    return `${kb.toFixed(2)} KB`;
  };

  const displayName = dataset.title || dataset.name;
  const hasDownloads = dataset.downloads !== undefined && dataset.downloads !== null;
  const hasRelevance = dataset.relevance_score !== undefined && dataset.relevance_score !== null;
  const hasSize = dataset.size !== undefined || (dataset.size_str && dataset.size_str !== "Unknown");

  return (
    <Card className="p-4 hover:shadow-md transition-shadow">
      <div className="space-y-3">
        {/* Title */}
        <div>
          <h4 className="font-medium text-sm line-clamp-2">{displayName}</h4>
          <div className="flex items-center gap-1 mt-1">
            <Database className="h-3 w-3 text-orange-500" />
            <span className="text-xs text-muted-foreground">HuggingFace Dataset</span>
          </div>
        </div>

        {/* Stats Grid */}
        {(hasDownloads || hasRelevance || hasSize) && (
          <div className="grid grid-cols-2 gap-2">
            {/* Downloads */}
            {hasDownloads && (
              <div className="flex items-center gap-1.5 text-xs">
                <Download className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-muted-foreground">Downloads:</span>
                <span className="font-medium">{formatNumber(dataset.downloads!)}</span>
              </div>
            )}

            {/* Size */}
            {hasSize && (
              <div className="flex items-center gap-1.5 text-xs">
                <HardDrive className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-muted-foreground">Size:</span>
                <span className="font-medium">{formatSize(dataset.size, dataset.size_str)}</span>
              </div>
            )}

            {/* Relevance Score */}
            {hasRelevance && (
              <div className="flex items-center gap-1.5 text-xs">
                <Star className="h-3.5 w-3.5 text-yellow-500" />
                <span className="text-muted-foreground">Relevance:</span>
                <Badge variant="secondary" className="h-5 px-1.5 text-xs">
                  {(dataset.relevance_score! * 100).toFixed(1)}%
                </Badge>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={handleAddDataset}
            disabled={isChecking || isAdding || isAdded}
            size="sm"
            className="flex-1 relative"
            variant={isAdded ? "outline" : "default"}
          >
            {isChecking ? (
              <>
                <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
                Checking...
              </>
            ) : isAdding || isDownloading ? (
              <>
                <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
                {downloadProgress > 0 ? `Downloading ${Math.round(downloadProgress)}%` : 'Preparing...'}
              </>
            ) : isAdded ? (
              <>
                <Check className="h-3.5 w-3.5 mr-2" />
                Downloaded
              </>
            ) : (
              <>
                <Download className="h-3.5 w-3.5 mr-2" />
                Download
              </>
            )}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => window.open(huggingFaceUrl, '_blank', 'noopener,noreferrer')}
            aria-label={`View ${displayName} on HuggingFace (opens in new tab)`}
            disabled={huggingFaceUrl === '#'}
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
