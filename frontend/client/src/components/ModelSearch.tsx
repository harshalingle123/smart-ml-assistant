import { memo, useState, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, SlidersHorizontal, X } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import type { ModelSearchFilters } from "@/lib/api";

interface ModelSearchProps {
  onSearch: (query: string, filters: ModelSearchFilters) => void;
  isLoading?: boolean;
}

export const ModelSearch = memo<ModelSearchProps>(({ onSearch, isLoading }) => {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<ModelSearchFilters>({});
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);

  const handleSearch = useCallback(() => {
    onSearch(query, filters);
  }, [query, filters, onSearch]);

  const handleKeyPress = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        handleSearch();
      }
    },
    [handleSearch]
  );

  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);

  const activeFiltersCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search HuggingFace models (e.g., sentiment analysis, text classification)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            className="pl-10"
            disabled={isLoading}
            aria-label="Search models"
          />
        </div>
        <Popover open={isFiltersOpen} onOpenChange={setIsFiltersOpen}>
          <PopoverTrigger asChild>
            <Button variant="outline" className="gap-2" disabled={isLoading}>
              <SlidersHorizontal className="h-4 w-4" />
              Filters
              {activeFiltersCount > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {activeFiltersCount}
                </Badge>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80" align="end">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-sm">Search Filters</h4>
                {activeFiltersCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearFilters}
                    className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
                  >
                    Clear all
                  </Button>
                )}
              </div>

              <div className="space-y-3">
                <div>
                  <Label htmlFor="task" className="text-xs">
                    Task Type
                  </Label>
                  <Select
                    value={filters.task || ""}
                    onValueChange={(value) =>
                      setFilters((prev) => ({ ...prev, task: value || undefined }))
                    }
                  >
                    <SelectTrigger id="task" className="mt-1">
                      <SelectValue placeholder="All tasks" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All tasks</SelectItem>
                      <SelectItem value="text-classification">Text Classification</SelectItem>
                      <SelectItem value="sentiment-analysis">Sentiment Analysis</SelectItem>
                      <SelectItem value="question-answering">Question Answering</SelectItem>
                      <SelectItem value="summarization">Summarization</SelectItem>
                      <SelectItem value="translation">Translation</SelectItem>
                      <SelectItem value="text-generation">Text Generation</SelectItem>
                      <SelectItem value="token-classification">Token Classification</SelectItem>
                      <SelectItem value="fill-mask">Fill Mask</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="language" className="text-xs">
                    Language
                  </Label>
                  <Select
                    value={filters.language || ""}
                    onValueChange={(value) =>
                      setFilters((prev) => ({ ...prev, language: value || undefined }))
                    }
                  >
                    <SelectTrigger id="language" className="mt-1">
                      <SelectValue placeholder="All languages" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All languages</SelectItem>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                      <SelectItem value="zh">Chinese</SelectItem>
                      <SelectItem value="multilingual">Multilingual</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="sortBy" className="text-xs">
                    Sort By
                  </Label>
                  <Select
                    value={filters.sortBy || "relevance"}
                    onValueChange={(value) =>
                      setFilters((prev) => ({
                        ...prev,
                        sortBy: value as ModelSearchFilters["sortBy"],
                      }))
                    }
                  >
                    <SelectTrigger id="sortBy" className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="relevance">Relevance</SelectItem>
                      <SelectItem value="downloads">Most Downloads</SelectItem>
                      <SelectItem value="recent">Recently Updated</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="maxSize" className="text-xs">
                    Max Model Size
                  </Label>
                  <Select
                    value={filters.maxSize || ""}
                    onValueChange={(value) =>
                      setFilters((prev) => ({ ...prev, maxSize: value || undefined }))
                    }
                  >
                    <SelectTrigger id="maxSize" className="mt-1">
                      <SelectValue placeholder="Any size" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">Any size</SelectItem>
                      <SelectItem value="100M">Up to 100M parameters</SelectItem>
                      <SelectItem value="1B">Up to 1B parameters</SelectItem>
                      <SelectItem value="10B">Up to 10B parameters</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </PopoverContent>
        </Popover>
        <Button onClick={handleSearch} disabled={isLoading || !query}>
          Search
        </Button>
      </div>

      {activeFiltersCount > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-muted-foreground">Active filters:</span>
          {filters.task && (
            <Badge variant="secondary" className="gap-1">
              Task: {filters.task}
              <button
                onClick={() => setFilters((prev) => ({ ...prev, task: undefined }))}
                className="ml-1 hover:text-foreground"
                aria-label="Remove task filter"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          )}
          {filters.language && (
            <Badge variant="secondary" className="gap-1">
              Language: {filters.language}
              <button
                onClick={() => setFilters((prev) => ({ ...prev, language: undefined }))}
                className="ml-1 hover:text-foreground"
                aria-label="Remove language filter"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          )}
          {filters.maxSize && (
            <Badge variant="secondary" className="gap-1">
              Max size: {filters.maxSize}
              <button
                onClick={() => setFilters((prev) => ({ ...prev, maxSize: undefined }))}
                className="ml-1 hover:text-foreground"
                aria-label="Remove size filter"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          )}
        </div>
      )}
    </div>
  );
});

ModelSearch.displayName = "ModelSearch";
