import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, Key, Trash2, CheckCircle2 } from "lucide-react";
import type { Model } from "@shared/schema";

interface ModelCardProps {
  model: Model;
  onDownload?: (id: string) => void;
  onGenerateAPI?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export function ModelCard({ model, onDownload, onGenerateAPI, onDelete }: ModelCardProps) {
  return (
    <Card className="hover-elevate" data-testid={`card-model-${model.id}`}>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1">
            <CardTitle className="text-lg font-semibold">{model.name}</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                v{model.version}
              </Badge>
              <Badge
                variant={model.status === "ready" ? "default" : "secondary"}
                className="text-xs"
              >
                {model.status === "ready" && <CheckCircle2 className="h-3 w-3 mr-1" />}
                {model.status}
              </Badge>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-3 gap-3">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Accuracy</p>
            <p className="text-sm font-medium" data-testid={`text-accuracy-${model.id}`}>
              {model.accuracy || "N/A"}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">F1 Score</p>
            <p className="text-sm font-medium">{model.f1Score || "N/A"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Loss</p>
            <p className="text-sm font-medium">{model.loss || "N/A"}</p>
          </div>
        </div>

        <div className="mt-4 space-y-1">
          <p className="text-xs text-muted-foreground">Base Model</p>
          <p className="text-sm font-mono">{model.baseModel}</p>
        </div>

        <div className="mt-2 space-y-1">
          <p className="text-xs text-muted-foreground">Created</p>
          <p className="text-sm">
            {new Date(model.createdAt).toLocaleDateString()}
          </p>
        </div>
      </CardContent>

      <CardFooter className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onDownload?.(model.id)}
          data-testid={`button-download-${model.id}`}
        >
          <Download className="h-4 w-4 mr-1" />
          Download
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onGenerateAPI?.(model.id)}
          data-testid={`button-api-${model.id}`}
        >
          <Key className="h-4 w-4 mr-1" />
          API
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete?.(model.id)}
          data-testid={`button-delete-${model.id}`}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}
