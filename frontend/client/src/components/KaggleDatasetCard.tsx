import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, TrendingUp, Star, Database, Loader2, Check, ExternalLink, HardDrive, Copy } from "lucide-react";
import { addDatasetFromKaggle, getDatasets, downloadDatasetWithProgress } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface KaggleDataset {
  ref: string;
  title: string;
  size?: number;
  last_updated?: string;
  download_count?: number;
  downloads?: number;
  vote_count?: number;
  usability_rating?: number;
  relevance_score?: number;
  url?: string;
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
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const { toast } = useToast();

  // Validate and construct proper Kaggle URL
  const getKaggleUrl = (): string => {
    if (dataset.url && dataset.url.startsWith('http')) {
      return dataset.url;
    }
    // Fallback: construct from ref
    if (dataset.ref) {
      return `https://www.kaggle.com/datasets/${dataset.ref}`;
    }
    return dataset.url || `https://www.kaggle.com/datasets/${dataset.ref}`;
  };

  const kaggleUrl = getKaggleUrl();

  // Check if dataset already exists in user's collection
  useEffect(() => {
    const checkIfDatasetExists = async () => {
      try {
        setIsChecking(true);
        const response = await getDatasets();
        const datasetsList = Array.isArray(response) ? response : (response.datasets || []);

        // Check if any dataset has the same kaggle_ref (check both snake_case and camelCase)
        const exists = datasetsList.some((ds: any) =>
          (ds.kaggleRef === dataset.ref) || (ds.kaggle_ref === dataset.ref)
        );

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
    setDownloadProgress(0);

    try {
      // Start adding dataset
      const response = await addDatasetFromKaggle({
        dataset_ref: dataset.ref,
        dataset_title: dataset.title,
        dataset_size: dataset.size || 0,
        chat_id: chatId,
      });

      // Store the dataset ID for download
      if (response && response.id) {
        setDatasetId(response.id);
      }

      // Now download the actual dataset with real-time progress
      setIsDownloading(true);

      const cleanup = downloadDatasetWithProgress(
        response.id || dataset.ref,
        "Kaggle",
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
            description: `${dataset.title} has been downloaded and added to your collection.`,
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
            description: `${dataset.title} metadata added. Download will happen when you inspect or train.`,
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
      toast({
        variant: "destructive",
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to add dataset. Please try again.",
      });

      setIsAdding(false);
      setIsDownloading(false);
      setTimeout(() => setDownloadProgress(0), 1000);
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

  const downloadsCount = dataset.downloads || dataset.download_count || 0;
  const hasSize = dataset.size !== undefined && dataset.size !== null;
  const hasVotes = dataset.vote_count !== undefined && dataset.vote_count !== null;
  const hasUsability = dataset.usability_rating !== undefined && dataset.usability_rating !== null;
  const hasRelevance = dataset.relevance_score !== undefined && dataset.relevance_score !== null;

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
          {hasSize && (
            <div className="flex items-center gap-1.5 text-xs">
              <Database className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Size:</span>
              <span className="font-medium">{formatSize(dataset.size!)}</span>
            </div>
          )}

          {/* Downloads */}
          <div className="flex items-center gap-1.5 text-xs">
            <Download className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-muted-foreground">Downloads:</span>
            <span className="font-medium">{formatNumber(downloadsCount)}</span>
          </div>

          {/* Votes */}
          {hasVotes && (
            <div className="flex items-center gap-1.5 text-xs">
              <TrendingUp className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Votes:</span>
              <span className="font-medium">{formatNumber(dataset.vote_count!)}</span>
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

          {/* Usability Rating */}
          {hasUsability && (
            <div className="flex items-center gap-1.5 text-xs">
              <Star className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Quality:</span>
              <Badge variant="secondary" className="h-5 px-1.5 text-xs">
                {dataset.usability_rating!.toFixed(2)}
              </Badge>
            </div>
          )}
        </div>

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
            onClick={() => window.open(kaggleUrl, '_blank', 'noopener,noreferrer')}
            aria-label={`View ${dataset.title} on Kaggle (opens in new tab)`}
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
