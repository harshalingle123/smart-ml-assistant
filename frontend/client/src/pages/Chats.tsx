import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, Trash2, ExternalLink, Loader2, RefreshCw } from "lucide-react";
import { Link, useLocation } from "wouter";
import { useState, useEffect } from "react";
import { getChats, deleteChat } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface Chat {
  _id: string;
  id?: string;
  title: string;
  model_id?: string;
  dataset_id?: string;
  last_updated: string;
  created_at: string;
}

export default function Chats() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();
  const [location] = useLocation();

  // Load chats on mount and when navigating to this page
  useEffect(() => {
    if (location === "/chats") {
      loadChats();
    }
  }, [location]);

  const loadChats = async () => {
    try {
      setLoading(true);
      const response = await getChats();
      const chatsList = Array.isArray(response) ? response : (response.chats || []);

      // Map _id to id if needed
      const mappedChats = chatsList.map((chat: any) => ({
        ...chat,
        id: chat.id || chat._id,
      }));

      console.log("Loaded chats:", mappedChats.length);
      setChats(mappedChats);
    } catch (error) {
      console.error("Failed to load chats:", error);
      toast({
        title: "Error",
        description: "Failed to load chats",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      console.log("Deleting chat with ID:", id);
      await deleteChat(id);
      toast({
        title: "Success",
        description: "Chat deleted successfully",
      });
      // Reload chats
      await loadChats();
    } catch (error) {
      console.error("Failed to delete chat:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to delete chat";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">My Chats</h1>
          <p className="text-muted-foreground mt-1">
            View and manage your chat history
          </p>
        </div>
        <Button
          variant="outline"
          size="icon"
          onClick={loadChats}
          disabled={loading}
          title="Refresh chats"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : chats.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 border-2 border-dashed rounded-lg">
          <MessageSquare className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No chats yet</h3>
          <p className="text-muted-foreground mb-4">Start a new conversation to see it here</p>
          <Link href="/">
            <Button>
              <MessageSquare className="h-4 w-4 mr-1" />
              Start New Chat
            </Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {chats.map((chat) => (
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
                    onClick={() => handleDelete(chat.id!)}
                    data-testid={`button-delete-chat-${chat.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>

              <CardContent className="space-y-3">
                <div className="flex items-center gap-2 flex-wrap">
                  {chat.model_id && (
                    <Badge variant="outline" className="text-xs">
                      Model: {chat.model_id}
                    </Badge>
                  )}
                  {chat.dataset_id && (
                    <Badge variant="outline" className="text-xs">
                      Dataset: {chat.dataset_id}
                    </Badge>
                  )}
                </div>

                <div className="text-xs text-muted-foreground">
                  Last updated: {new Date(chat.last_updated).toLocaleString()}
                </div>

                <Link href={`/?chat=${chat.id}`}>
                  <Button variant="outline" size="sm" className="w-full" data-testid={`button-open-chat-${chat.id}`}>
                    <ExternalLink className="h-4 w-4 mr-1" />
                    Open Chat
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
