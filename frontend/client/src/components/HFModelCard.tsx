import { memo } from "react";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Download,
  Heart,
  ExternalLink,
  GitCompare,
  Info,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { HuggingFaceModel } from "@/lib/types";

interface HFModelCardProps {
  model: HuggingFaceModel;
  onSelect?: (modelId: string) => void;
  onCompare?: (modelId: string, checked: boolean) => void;
  isComparing?: boolean;
  isSelected?: boolean;
}

export const HFModelCard = memo<HFModelCardProps>(({
  model,
  onSelect,
  onCompare,
  isComparing,
  isSelected,
}) => {
  const formatNumber = (num: number) => {
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(1)}B`;
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardHeader className="space-y-2 pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-sm truncate" title={model.name}>
              {model.name}
            </h3>
            <p className="text-xs text-muted-foreground truncate" title={model.id}>
              {model.id}
            </p>
          </div>
          {isComparing && (
            <Checkbox
              checked={isSelected}
              onCheckedChange={(checked) => onCompare?.(model.id, checked as boolean)}
              aria-label={`Compare ${model.name}`}
            />
          )}
        </div>

        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-1" title="Downloads">
            <Download className="h-3 w-3" />
            <span>{formatNumber(model.downloads)}</span>
          </div>
          <div className="flex items-center gap-1" title="Likes">
            <Heart className="h-3 w-3" />
            <span>{formatNumber(model.likes)}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pb-3">
        <div className="flex flex-wrap gap-1">
          {model.task && (
            <Badge variant="secondary" className="text-xs">
              {model.task}
            </Badge>
          )}
          {model.library && (
            <Badge variant="outline" className="text-xs">
              {model.library}
            </Badge>
          )}
        </div>

        {model.description && (
          <p className="text-xs text-muted-foreground line-clamp-2">
            {model.description}
          </p>
        )}

        <div className="grid grid-cols-2 gap-2 text-xs">
          {model.parameters && (
            <div>
              <span className="text-muted-foreground">Parameters:</span>
              <span className="ml-1 font-medium">
                {formatNumber(model.parameters)}
              </span>
            </div>
          )}
          {model.accuracy && (
            <div>
              <span className="text-muted-foreground">Accuracy:</span>
              <span className="ml-1 font-medium">
                {(model.accuracy * 100).toFixed(1)}%
              </span>
            </div>
          )}
        </div>

        {model.languages && model.languages.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {model.languages.slice(0, 3).map((lang) => (
              <Badge key={lang} variant="outline" className="text-xs">
                {lang}
              </Badge>
            ))}
            {model.languages.length > 3 && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge variant="outline" className="text-xs cursor-help">
                    +{model.languages.length - 3}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">
                    {model.languages.slice(3).join(", ")}
                  </p>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex gap-2 pt-3 border-t">
        {onSelect && (
          <Button
            size="sm"
            onClick={() => onSelect(model.id)}
            className="flex-1"
          >
            <Download className="h-3 w-3 mr-1" />
            Select
          </Button>
        )}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              size="sm"
              variant="outline"
              asChild
              className={onSelect ? "" : "flex-1"}
            >
              <a
                href={`https://huggingface.co/${model.id}`}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="View on HuggingFace"
              >
                <ExternalLink className="h-3 w-3" />
              </a>
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>View on HuggingFace</p>
          </TooltipContent>
        </Tooltip>
      </CardFooter>
    </Card>
  );
});

HFModelCard.displayName = "HFModelCard";
