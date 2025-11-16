import { useState, useCallback } from "react";
import { ModelSearch } from "@/components/ModelSearch";
import { HFModelCard } from "@/components/HFModelCard";
import { ModelComparison } from "@/components/ModelComparison";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { GitCompare, AlertCircle } from "lucide-react";
import { searchModels, type ModelSearchFilters } from "@/lib/api";
import type { HuggingFaceModel } from "@/lib/types";
import { useToast } from "@/hooks/use-toast";

export default function ModelSelection() {
  const [models, setModels] = useState<HuggingFaceModel[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [selectedForComparison, setSelectedForComparison] = useState<string[]>([]);
  const [isComparisonOpen, setIsComparisonOpen] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const { toast } = useToast();

  const handleSearch = useCallback(
    async (query: string, filters: ModelSearchFilters) => {
      if (!query.trim()) return;

      setIsLoading(true);
      setError(null);
      setSearchPerformed(true);

      try {
        const results = await searchModels(query, filters);
        setModels(results.models || []);
        if (!results.models || results.models.length === 0) {
          setError("No models found matching your search criteria.");
        }
      } catch (err) {
        console.error("Search error:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to search models. Please try again."
        );
        toast({
          variant: "destructive",
          title: "Search failed",
          description: "Unable to fetch models from HuggingFace.",
        });
      } finally {
        setIsLoading(false);
      }
    },
    [toast]
  );

  const handleSelectModel = useCallback(
    (modelId: string) => {
      const model = models.find((m) => m.id === modelId);
      if (model) {
        toast({
          title: "Model selected",
          description: `${model.name} is ready to use for training.`,
        });
      }
    },
    [models, toast]
  );

  const handleCompareToggle = useCallback((modelId: string, checked: boolean) => {
    setSelectedForComparison((prev) => {
      if (checked && prev.length >= 3) {
        return prev;
      }
      return checked ? [...prev, modelId] : prev.filter((id) => id !== modelId);
    });
  }, []);

  const handleCompare = useCallback(() => {
    if (selectedForComparison.length >= 2) {
      setIsComparisonOpen(true);
    }
  }, [selectedForComparison]);

  const modelsToCompare = models.filter((m) =>
    selectedForComparison.includes(m.id)
  );

  return (
    <div className="p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold">Model Selection</h1>
        <p className="text-muted-foreground">
          Search and select models from HuggingFace for your training jobs
        </p>
      </div>

      <ModelSearch onSearch={handleSearch} isLoading={isLoading} />

      {selectedForComparison.length > 0 && (
        <div className="flex items-center justify-between p-4 border rounded-lg bg-accent/50">
          <div className="flex items-center gap-2">
            <GitCompare className="h-4 w-4" />
            <span className="text-sm font-medium">
              {selectedForComparison.length} model{selectedForComparison.length !== 1 ? "s" : ""} selected
            </span>
            {selectedForComparison.length < 2 && (
              <span className="text-xs text-muted-foreground">
                (Select at least 2 models to compare)
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedForComparison([])}
            >
              Clear
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsComparing(!isComparing)}
            >
              {isComparing ? "Done" : "Select Models"}
            </Button>
            <Button
              size="sm"
              onClick={handleCompare}
              disabled={selectedForComparison.length < 2}
            >
              Compare
            </Button>
          </div>
        </div>
      )}

      {!searchPerformed && !isLoading && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            Start by searching for models above
          </p>
        </div>
      )}

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="space-y-3 border rounded-lg p-4">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ))}
        </div>
      )}

      {error && !isLoading && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!isLoading && !error && models.length > 0 && (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Found {models.length} model{models.length !== 1 ? "s" : ""}
            </p>
            {!isComparing && models.length > 1 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsComparing(true)}
              >
                <GitCompare className="h-4 w-4 mr-1" />
                Compare Models
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {models.map((model) => (
              <HFModelCard
                key={model.id}
                model={model}
                onSelect={handleSelectModel}
                onCompare={handleCompareToggle}
                isComparing={isComparing}
                isSelected={selectedForComparison.includes(model.id)}
              />
            ))}
          </div>
        </>
      )}

      <ModelComparison
        models={modelsToCompare}
        open={isComparisonOpen}
        onOpenChange={setIsComparisonOpen}
        onSelectModel={handleSelectModel}
      />
    </div>
  );
}
