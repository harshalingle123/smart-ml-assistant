import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, Trash2, FileText, CheckCircle2, Loader2, Link2, ExternalLink, Eye } from "lucide-react";
import type { Dataset } from "@shared/schema";
import { Link } from "wouter";

interface DatasetCardProps {
  dataset: Dataset;
  onDownload?: (id: string) => void;
  onDelete?: (id: string) => void;
}

/**
 * Normalizes dataset object to handle both snake_case and camelCase field formats
 */
const normalizeDataset = (dataset: any): Dataset => {
  console.log('[DatasetCard] Raw dataset received:', {
    id: dataset.id,
    _id: dataset._id,
    name: dataset.name,
    status: dataset.status,
    source: dataset.source,
    kaggleRef: dataset.kaggleRef,
    kaggle_ref: dataset.kaggle_ref,
  });

  // Handle ObjectId conversion for id field
  const id = typeof dataset.id === 'string' ? dataset.id :
             (dataset._id && typeof dataset._id === 'object' && '$oid' in dataset._id) ? dataset._id.$oid :
             dataset._id?.toString() || dataset.id?.toString() || '';

  const normalized = {
    id,
    name: dataset.name || 'Unnamed Dataset',
    rowCount: dataset.rowCount ?? dataset.row_count ?? 0,
    columnCount: dataset.columnCount ?? dataset.column_count ?? 0,
    fileSize: dataset.fileSize ?? dataset.file_size ?? 0,
    status: dataset.status || 'unknown',
    uploadedAt: dataset.uploadedAt ?? dataset.uploaded_at ?? null,
    previewData: dataset.previewData ?? dataset.preview_data ?? null,
    fileName: dataset.fileName ?? dataset.file_name ?? null,
    kaggleRef: dataset.kaggleRef ?? dataset.kaggle_ref ?? null,
    huggingfaceRef: dataset.huggingfaceRef ?? dataset.huggingface_ref ?? null,
    huggingfaceDatasetId: dataset.huggingfaceDatasetId ?? dataset.huggingface_dataset_id ?? null,
    huggingfaceUrl: dataset.huggingfaceUrl ?? dataset.huggingface_url ?? null,
    source: dataset.source ?? null,
    description: dataset.description ?? null,
    schema: dataset.schema ?? null,
  } as Dataset;

  console.log('[DatasetCard] Normalized dataset:', {
    id: normalized.id,
    name: normalized.name,
    status: normalized.status,
    source: normalized.source,
    kaggleRef: normalized.kaggleRef,
    rowCount: normalized.rowCount,
    columnCount: normalized.columnCount,
  });

  return normalized;
};

export function DatasetCard({ dataset: rawDataset, onDownload, onDelete }: DatasetCardProps) {
  const dataset = normalizeDataset(rawDataset);
  const formatFileSize = (bytes: number) => {
    if (!bytes || isNaN(bytes) || bytes === 0) return "Unknown";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <Card className="hover-elevate" data-testid={`card-dataset-${dataset.id}`}>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />
            <CardTitle className="text-lg font-semibold truncate">{dataset.name}</CardTitle>
          </div>
          <div className="flex gap-1 flex-shrink-0">
            {dataset.source && (
              <Badge variant="secondary" className="text-xs">
                {dataset.source === 'kaggle' ? 'Kaggle' :
                 dataset.source === 'huggingface' ? 'HF' :
                 dataset.source}
              </Badge>
            )}
            <Badge
              variant={dataset.status === "ready" ? "default" : dataset.status === "pending_download" ? "outline" : "secondary"}
              className="text-xs"
            >
              {dataset.status === "processing" && (
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              )}
              {dataset.status === "ready" && <CheckCircle2 className="h-3 w-3 mr-1" />}
              {dataset.status === "pending_download" && <Link2 className="h-3 w-3 mr-1" />}
              {dataset.status === "pending_download" ? "Linked" : dataset.status}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Show Kaggle reference for pending downloads */}
        {dataset.status === "pending_download" && dataset.kaggleRef && (
          <div className="mb-4 p-3 bg-accent/50 rounded-md">
            <p className="text-xs text-muted-foreground mb-1">Kaggle Dataset</p>
            <div className="flex items-center justify-between gap-2">
              <code className="text-xs font-mono">{dataset.kaggleRef}</code>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => window.open(`https://www.kaggle.com/datasets/${dataset.kaggleRef}`, '_blank')}
                className="h-7 px-2"
              >
                <ExternalLink className="h-3 w-3" />
              </Button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Rows</p>
            <p className="text-sm font-medium" data-testid={`text-rows-${dataset.id}`}>
              {dataset.rowCount > 0 ? dataset.rowCount.toLocaleString() : "N/A"}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Columns</p>
            <p className="text-sm font-medium">{dataset.columnCount > 0 ? dataset.columnCount : "N/A"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Size</p>
            <p className="text-sm font-medium">{formatFileSize(dataset.fileSize)}</p>
          </div>
        </div>

        {dataset.previewData && Array.isArray(dataset.previewData) && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Preview</p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b">
                    {Object.keys(dataset.previewData[0] || {}).map((key) => (
                      <th key={key} className="text-left py-1 px-2 font-medium">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dataset.previewData.slice(0, 2).map((row: Record<string, any>, idx: number) => (
                    <tr key={idx} className="border-b">
                      {Object.values(row).map((value: unknown, i: number) => (
                        <td key={i} className="py-1 px-2 text-muted-foreground">
                          {String(value).slice(0, 20)}
                          {String(value).length > 20 ? "..." : ""}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="mt-3 space-y-1">
          <p className="text-xs text-muted-foreground">Added</p>
          <p className="text-sm">
            {dataset.uploadedAt
              ? new Date(dataset.uploadedAt).toLocaleDateString()
              : "Unknown"}
          </p>
        </div>
      </CardContent>

      <CardFooter className="flex gap-2">
        <Link href={`/datasets/${dataset.id}`} className="flex-1">
          <Button
            variant="default"
            size="sm"
            className="w-full"
            data-testid={`button-view-details-${dataset.id}`}
          >
            <Eye className="h-4 w-4 mr-1" />
            View Details
          </Button>
        </Link>
        {dataset.status === "pending_download" && dataset.kaggleRef && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(`https://www.kaggle.com/datasets/${dataset.kaggleRef}`, '_blank')}
            data-testid={`button-open-kaggle-${dataset.id}`}
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete?.(dataset.id)}
          data-testid={`button-delete-${dataset.id}`}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}
