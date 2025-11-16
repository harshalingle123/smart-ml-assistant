import { memo } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Download, ExternalLink } from "lucide-react";
import type { HuggingFaceModel } from "@/lib/types";

interface ModelComparisonProps {
  models: HuggingFaceModel[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectModel?: (modelId: string) => void;
}

export const ModelComparison = memo<ModelComparisonProps>(({
  models,
  open,
  onOpenChange,
  onSelectModel,
}) => {
  const formatNumber = (num?: number) => {
    if (!num) return "N/A";
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(1)}B`;
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const comparisonFields = [
    { label: "Model ID", key: "id" },
    { label: "Author", key: "author" },
    { label: "Task", key: "task" },
    { label: "Downloads", key: "downloads", format: formatNumber },
    { label: "Likes", key: "likes", format: formatNumber },
    { label: "Parameters", key: "parameters", format: formatNumber },
    { label: "Accuracy", key: "accuracy", format: (val?: number) => val ? `${(val * 100).toFixed(1)}%` : "N/A" },
    { label: "Library", key: "library" },
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Compare Models</DialogTitle>
          <DialogDescription>
            Side-by-side comparison of {models.length} models
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="h-[60vh]">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-1">
            {models.map((model) => (
              <div
                key={model.id}
                className="border rounded-lg p-4 space-y-4 bg-card"
              >
                <div>
                  <h3 className="font-semibold text-sm truncate" title={model.name}>
                    {model.name}
                  </h3>
                  <p className="text-xs text-muted-foreground truncate" title={model.id}>
                    {model.id}
                  </p>
                </div>

                <div className="space-y-3">
                  {comparisonFields.map((field) => {
                    const value = model[field.key as keyof HuggingFaceModel];
                    const displayValue = field.format
                      ? field.format(value as number)
                      : value || "N/A";

                    return (
                      <div key={field.key} className="space-y-1">
                        <p className="text-xs font-medium text-muted-foreground">
                          {field.label}
                        </p>
                        <p className="text-sm break-words">
                          {field.key === "task" ? (
                            <Badge variant="secondary" className="text-xs">
                              {displayValue as string}
                            </Badge>
                          ) : (
                            displayValue
                          )}
                        </p>
                      </div>
                    );
                  })}

                  {model.languages && model.languages.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-xs font-medium text-muted-foreground">
                        Languages
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {model.languages.slice(0, 3).map((lang) => (
                          <Badge key={lang} variant="outline" className="text-xs">
                            {lang}
                          </Badge>
                        ))}
                        {model.languages.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{model.languages.length - 3}
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2 pt-2 border-t">
                  {onSelectModel && (
                    <Button
                      size="sm"
                      onClick={() => {
                        onSelectModel(model.id);
                        onOpenChange(false);
                      }}
                      className="w-full"
                    >
                      <Download className="h-3 w-3 mr-1" />
                      Select Model
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    asChild
                    className="w-full"
                  >
                    <a
                      href={`https://huggingface.co/${model.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="h-3 w-3 mr-1" />
                      View on HuggingFace
                    </a>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
});

ModelComparison.displayName = "ModelComparison";
