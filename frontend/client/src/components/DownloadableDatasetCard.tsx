import { useState, memo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, ExternalLink, Loader2, CheckCircle2, AlertCircle, Database, TrendingUp, FolderDown } from "lucide-react";
import { downloadDataset } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface DownloadableDatasetCardProps {
  id: string;
  title: string;
  source: "Kaggle" | "HuggingFace";
  url: string;
  downloads?: number;
  relevance_score?: number;
}

type DownloadStatus = "idle" | "downloading" | "success" | "error";

export const DownloadableDatasetCard = memo<DownloadableDatasetCardProps>(
  ({ id, title, source, url, downloads, relevance_score }) => {
    const [downloadStatus, setDownloadStatus] = useState<DownloadStatus>("idle");
    const [downloadPath, setDownloadPath] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const { toast } = useToast();

    // Validate and construct proper URL
    const getValidatedUrl = (): string => {
      if (url && url.startsWith('http')) {
        return url;
      }

      // Fallback: construct URL from source and id
      if (source === "Kaggle" && id) {
        return `https://www.kaggle.com/datasets/${id}`;
      }

      if (source === "HuggingFace" && id) {
        return `https://huggingface.co/datasets/${id}`;
      }

      return url || '#';
    };

    const validatedUrl = getValidatedUrl();

    const handleDownload = async () => {
      setDownloadStatus("downloading");
      setErrorMessage(null);
      setDownloadPath(null);

      try {
        const result = await downloadDataset(id, source);

        if (result.success) {
          setDownloadStatus("success");
          setDownloadPath(result.file_path || null);

          toast({
            title: "Download Complete!",
            description: `${title} has been downloaded successfully.`,
          });
        } else {
          setDownloadStatus("error");
          setErrorMessage(result.message || "Download failed");

          toast({
            variant: "destructive",
            title: "Download Failed",
            description: result.message || "Failed to download dataset. Please try again.",
          });
        }
      } catch (error) {
        setDownloadStatus("error");
        const errorMsg = error instanceof Error ? error.message : "An unknown error occurred";
        setErrorMessage(errorMsg);

        toast({
          variant: "destructive",
          title: "Download Error",
          description: errorMsg,
        });
      }
    };

    const formatNumber = (num: number) => {
      if (num >= 1000000) {
        return `${(num / 1000000).toFixed(1)}M`;
      }
      if (num >= 1000) {
        return `${(num / 1000).toFixed(1)}K`;
      }
      return num.toLocaleString();
    };

    const getSourceColor = () => {
      return source === "Kaggle"
        ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
        : "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300";
    };

    const getSourceIcon = () => {
      return source === "Kaggle" ? Database : Database;
    };

    const SourceIcon = getSourceIcon();

    return (
      <Card className="p-4 hover:shadow-md transition-shadow border-l-4 border-l-primary/20">
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-sm line-clamp-2 leading-tight">
                {title}
              </h4>
              <p className="text-xs text-muted-foreground font-mono mt-1 truncate">
                {id}
              </p>
            </div>
            <Badge
              variant="secondary"
              className={`shrink-0 ${getSourceColor()} border-0`}
            >
              <SourceIcon className="h-3 w-3 mr-1" />
              {source}
            </Badge>
          </div>

          {/* Stats Row */}
          <div className="flex items-center gap-4 text-xs">
            {downloads !== undefined && downloads !== null && (
              <div className="flex items-center gap-1.5">
                <TrendingUp className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-muted-foreground">Downloads:</span>
                <span className="font-medium">{formatNumber(downloads)}</span>
              </div>
            )}

            {relevance_score !== undefined && relevance_score !== null && (
              <div className="flex items-center gap-1.5">
                <span className="text-muted-foreground">Relevance:</span>
                <Badge variant="outline" className="h-5 px-1.5 text-xs font-semibold">
                  {(relevance_score * 100).toFixed(0)}%
                </Badge>
              </div>
            )}
          </div>

          {/* Download Status */}
          {downloadStatus === "success" && downloadPath && (
            <div
              className="flex items-start gap-2 p-2 rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800"
              role="status"
              aria-live="polite"
            >
              <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-green-900 dark:text-green-100">
                  Downloaded successfully
                </p>
                <p className="text-xs text-green-700 dark:text-green-300 mt-0.5 truncate">
                  <FolderDown className="h-3 w-3 inline mr-1" />
                  {downloadPath}
                </p>
              </div>
            </div>
          )}

          {downloadStatus === "error" && errorMessage && (
            <div
              className="flex items-start gap-2 p-2 rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800"
              role="alert"
              aria-live="assertive"
            >
              <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-red-900 dark:text-red-100">
                  Download failed
                </p>
                <p className="text-xs text-red-700 dark:text-red-300 mt-0.5">
                  {errorMessage}
                </p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2">
            <Button
              onClick={handleDownload}
              disabled={downloadStatus === "downloading"}
              size="sm"
              className="flex-1"
              variant={downloadStatus === "success" ? "outline" : "default"}
              aria-label={`Download ${title} from ${source}`}
            >
              {downloadStatus === "downloading" ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
                  Downloading...
                </>
              ) : downloadStatus === "success" ? (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5 mr-2" />
                  Downloaded
                </>
              ) : (
                <>
                  <Download className="h-3.5 w-3.5 mr-2" />
                  Download Dataset
                </>
              )}
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => window.open(validatedUrl, "_blank", "noopener,noreferrer")}
              aria-label={`View ${title} on ${source} (opens in new tab)`}
              disabled={validatedUrl === '#'}
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </Card>
    );
  }
);

DownloadableDatasetCard.displayName = "DownloadableDatasetCard";
