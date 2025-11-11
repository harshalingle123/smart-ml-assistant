import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, Trash2, ExternalLink } from "lucide-react";
import { MOCK_CHATS } from "@/lib/mock-data";
import { Link } from "wouter";

export default function Chats() {
  const handleDelete = (id: string) => {
    console.log("Delete chat:", id);
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">My Chats</h1>
        <p className="text-muted-foreground mt-1">
          View and manage your chat history
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {MOCK_CHATS.map((chat) => (
          <Card key={chat.id} className="hover-elevate" data-testid={`card-chat-${chat.id}`}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-muted-foreground" />
                  <CardTitle className="text-lg font-semibold">{chat.title}</CardTitle>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleDelete(chat.id)}
                  data-testid={`button-delete-chat-${chat.id}`}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>

            <CardContent className="space-y-3">
              <div className="flex items-center gap-2">
                {chat.modelId && (
                  <Badge variant="outline" className="text-xs">
                    Model: {chat.modelId}
                  </Badge>
                )}
                {chat.datasetId && (
                  <Badge variant="outline" className="text-xs">
                    Dataset: {chat.datasetId}
                  </Badge>
                )}
              </div>

              <div className="text-xs text-muted-foreground">
                Last updated: {chat.lastUpdated.toLocaleString()}
              </div>

              <Link href="/">
                <Button variant="outline" size="sm" className="w-full" data-testid={`button-open-chat-${chat.id}`}>
                  <ExternalLink className="h-4 w-4 mr-1" />
                  Open Chat
                </Button>
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
