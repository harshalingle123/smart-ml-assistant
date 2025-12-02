import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User, Download, Code } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import { useLocation } from "wouter";
import { getApiUrl } from "@/lib/env";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  queryType?: "simple" | "data_based";
  timestamp?: Date;
  metadata?: {
    model_id?: string;
    best_model?: string;
    metrics?: Record<string, any>;
  };
}

export function MessageBubble({ role, content, queryType, timestamp, metadata }: MessageBubbleProps) {
  const isUser = role === "user";
  const { toast } = useToast();
  const [, setLocation] = useLocation();

  const handleDownloadModel = async () => {
    if (!metadata?.model_id) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        toast({
          title: "Authentication Required",
          description: "Please log in to download models",
          variant: "destructive",
        });
        return;
      }

      toast({
        title: "Download Started",
        description: "Preparing model for download...",
      });

      // Download model metadata as JSON
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/models/${metadata.model_id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch model");
      }

      const modelData = await response.json();

      // Create downloadable JSON file
      const blob = new Blob([JSON.stringify(modelData, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `model_${metadata.model_id}_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      toast({
        title: "Download Complete",
        description: "Model metadata downloaded successfully",
      });
    } catch (error) {
      console.error("Failed to download model:", error);
      toast({
        title: "Download Failed",
        description: error instanceof Error ? error.message : "Failed to download model",
        variant: "destructive",
      });
    }
  };

  const handleGenerateAPI = () => {
    if (!metadata?.model_id) return;

    toast({
      title: "Navigating to API",
      description: "Opening API generation page...",
    });

    // Navigate to Direct Access page (or Models page) with the model_id
    setLocation(`/models?highlight=${metadata.model_id}`);
  };

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      <div className={cn("flex flex-col gap-2 max-w-3xl", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-lg px-4 py-3",
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-card border border-card-border"
          )}
        >
          <p className="text-sm whitespace-pre-wrap">{content}</p>
        </div>

        {/* Model Action Buttons */}
        {metadata?.model_id && !isUser && (
          <div className="flex gap-2 mt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadModel}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Download Model
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerateAPI}
              className="flex items-center gap-2"
            >
              <Code className="h-4 w-4" />
              Generate API
            </Button>
          </div>
        )}

        <div className={cn("flex items-center gap-2 text-xs text-muted-foreground", isUser && "flex-row-reverse")}>
          {timestamp && (
            <span>{timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
          )}
          {queryType && !isUser && (
            <Badge variant="outline" className="text-xs">
              {queryType === "simple" ? "Simple Query" : "Data-Based Query"}
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
}
