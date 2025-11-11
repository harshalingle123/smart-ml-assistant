import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, Trash2, FileText, CheckCircle2, Loader2 } from "lucide-react";
import type { Dataset } from "@shared/schema";

interface DatasetCardProps {
  dataset: Dataset;
  onDownload?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export function DatasetCard({ dataset, onDownload, onDelete }: DatasetCardProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <Card className="hover-elevate" data-testid={`card-dataset-${dataset.id}`}>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg font-semibold">{dataset.name}</CardTitle>
          </div>
          <Badge
            variant={dataset.status === "ready" ? "default" : "secondary"}
            className="text-xs"
          >
            {dataset.status === "processing" && (
              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            )}
            {dataset.status === "ready" && <CheckCircle2 className="h-3 w-3 mr-1" />}
            {dataset.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Rows</p>
            <p className="text-sm font-medium" data-testid={`text-rows-${dataset.id}`}>
              {dataset.rowCount.toLocaleString()}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Columns</p>
            <p className="text-sm font-medium">{dataset.columnCount}</p>
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
          <p className="text-xs text-muted-foreground">Uploaded</p>
          <p className="text-sm">
            {new Date(dataset.uploadedAt).toLocaleDateString()}
          </p>
        </div>
      </CardContent>

      <CardFooter className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onDownload?.(dataset.id)}
          data-testid={`button-download-${dataset.id}`}
        >
          <Download className="h-4 w-4 mr-1" />
          Download
        </Button>
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
