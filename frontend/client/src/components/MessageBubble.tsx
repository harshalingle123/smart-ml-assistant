import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  queryType?: "simple" | "data_based";
  timestamp?: Date;
}

export function MessageBubble({ role, content, queryType, timestamp }: MessageBubbleProps) {
  const isUser = role === "user";

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
