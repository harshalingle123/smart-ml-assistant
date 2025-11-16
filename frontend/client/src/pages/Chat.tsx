import { useState, useEffect } from "react";
import { MessageBubble } from "@/components/MessageBubble";
import { ChatInput } from "@/components/ChatInput";
import { SmartChart } from "@/components/SmartChart";
import { KaggleDatasetCard } from "@/components/KaggleDatasetCard";
import { HuggingFaceDatasetCard } from "@/components/HuggingFaceDatasetCard";
import { Card, CardHeader, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Database, ExternalLink, Sparkles } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { createChat, sendMessage, sendMessageToAgent, getChatMessages, updateChat } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

interface KaggleDataset {
  ref: string;
  title: string;
  size: number;
  last_updated: string;
  download_count: number;
  vote_count: number;
  usability_rating: number;
}

interface MessageMetadata {
  kaggle_datasets?: KaggleDataset[];
  search_query?: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  queryType?: "simple" | "data_based" | "dataset_search";
  timestamp: Date;
  charts?: any[];
  metadata?: MessageMetadata;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatId, setChatId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [useAgent, setUseAgent] = useState(true); // Default to agent mode
  const { toast } = useToast();

  // Start training with SSE using fetch (supports auth headers)
  const startTraining = async (datasetId: string, currentChatId: string) => {
    try {
      setIsLoading(true);

      // Get auth token
      const token = localStorage.getItem("token");
      if (!token) {
        toast({
          title: "Authentication Required",
          description: "Please log in to train models",
          variant: "destructive",
        });
        setIsLoading(false);
        return;
      }

      // Use fetch with streaming instead of EventSource (allows auth headers)
      const response = await fetch(
        `http://localhost:8000/api/automl/train/${datasetId}?chat_id=${currentChatId}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'text/event-stream',
          },
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Training request failed:", response.status, errorText);
        throw new Error(`Training request failed: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (!reader) {
        throw new Error("Response body is not readable");
      }

      // Read SSE stream
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          console.log("SSE stream ended");
          break;
        }

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE messages
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // Keep incomplete message in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6); // Remove 'data: ' prefix

            try {
              const data = JSON.parse(dataStr);

              if (data.type === "status" || data.type === "progress") {
                // Add status message to chat
                setMessages((prev) => [
                  ...prev,
                  {
                    role: "assistant",
                    content: data.message,
                    timestamp: new Date(),
                  },
                ]);
              } else if (data.type === "complete") {
                // Add final message
                setMessages((prev) => [
                  ...prev,
                  {
                    role: "assistant",
                    content: data.message,
                    timestamp: new Date(),
                    metadata: {
                      model_id: data.model_id,
                      best_model: data.best_model,
                      metrics: data.metrics,
                    },
                  },
                ]);

                setIsLoading(false);

                // Clear URL params
                window.history.pushState({}, '', `/?chat=${currentChatId}`);

                toast({
                  title: "Training Complete!",
                  description: `Model trained successfully with ${data.best_model}`,
                });

                return; // Exit the loop
              } else if (data.type === "error") {
                // Handle error
                setMessages((prev) => [
                  ...prev,
                  {
                    role: "assistant",
                    content: data.message,
                    timestamp: new Date(),
                  },
                ]);

                setIsLoading(false);

                toast({
                  title: "Training Failed",
                  description: data.message,
                  variant: "destructive",
                });

                return; // Exit the loop
              }
            } catch (parseError) {
              console.error("Failed to parse SSE message:", dataStr, parseError);
            }
          }
        }
      }

      setIsLoading(false);

    } catch (error) {
      console.error("Failed to start training:", error);
      setIsLoading(false);

      toast({
        title: "Connection Error",
        description: error instanceof Error ? error.message : "Lost connection to training server",
        variant: "destructive",
      });
    }
  };

  // Initialize chat on mount
  useEffect(() => {
    const initializeChat = async () => {
      try {
        // Check if there's a chat parameter in the URL
        const urlParams = new URLSearchParams(window.location.search);
        const existingChatId = urlParams.get('chat');
        const datasetId = urlParams.get('dataset');
        const shouldTrain = urlParams.get('train') === 'true';

        if (existingChatId) {
          // Load existing chat
          console.log("Loading existing chat:", existingChatId);
          setChatId(existingChatId);

          // Load messages for this chat
          const chatMessages = await getChatMessages(existingChatId);
          const formattedMessages = chatMessages.map((msg: any) => ({
            role: msg.role,
            content: msg.content,
            queryType: msg.query_type,
            timestamp: new Date(msg.timestamp),
            charts: msg.charts,
            metadata: msg.metadata,
          }));
          setMessages(formattedMessages);

          // Start training if requested
          if (shouldTrain && datasetId) {
            startTraining(datasetId, existingChatId);
          }
        } else {
          // Don't create chat yet - wait for first user message
          // Just show welcome message
          setMessages([
            {
              role: "assistant",
              content: "Welcome to Smart ML Assistant! I'm powered by Google Gemini with AI Agent capabilities and can help you with:\n\n✨ **Agent Mode (Recommended)**\nI automatically:\n• Understand your ML requirements\n• Find relevant datasets from Kaggle & HuggingFace\n• Suggest the best models for your task\n• Provide cost & time estimates\n\n💬 **You can ask me:**\n• \"I need a dataset to predict house prices\"\n• \"Find sentiment analysis datasets\"\n• \"Classify customer support tickets with <200ms latency\"\n• \"What's the best model for image classification?\"\n\nAgent Mode is ON by default. Toggle it off for regular chat.\n\nHow can I help you today?",
              timestamp: new Date(),
            },
          ]);
        }
      } catch (error) {
        console.error("Failed to initialize chat:", error);
        toast({
          variant: "destructive",
          title: "Error",
          description: "Failed to load chat. Please refresh the page.",
        });
      } finally {
        setIsInitializing(false);
      }
    };

    initializeChat();
  }, [toast]);

  // Helper function to generate chat title from query
  const generateChatTitle = (query: string): string => {
    const lowerQuery = query.toLowerCase();

    // Extract key topics from the query
    if (lowerQuery.includes('sentiment') || lowerQuery.includes('emotion')) {
      return 'Sentiment Analysis';
    } else if (lowerQuery.includes('house') && lowerQuery.includes('price')) {
      return 'House Price Prediction';
    } else if (lowerQuery.includes('stock') || lowerQuery.includes('financial')) {
      return 'Stock/Financial Analysis';
    } else if (lowerQuery.includes('image') || lowerQuery.includes('vision')) {
      return 'Image Analysis';
    } else if (lowerQuery.includes('nlp') || lowerQuery.includes('text') || lowerQuery.includes('language')) {
      return 'NLP/Text Analysis';
    } else if (lowerQuery.includes('classif')) {
      return 'Classification Task';
    } else if (lowerQuery.includes('regression') || lowerQuery.includes('predict')) {
      return 'Regression/Prediction';
    } else if (lowerQuery.includes('cluster')) {
      return 'Clustering Analysis';
    } else if (lowerQuery.includes('recommend')) {
      return 'Recommendation System';
    } else if (lowerQuery.includes('fraud') || lowerQuery.includes('anomaly')) {
      return 'Fraud/Anomaly Detection';
    } else if (lowerQuery.includes('customer') || lowerQuery.includes('support')) {
      return 'Customer Support Analysis';
    } else if (lowerQuery.includes('sales') || lowerQuery.includes('revenue')) {
      return 'Sales Analysis';
    } else if (lowerQuery.includes('churn')) {
      return 'Churn Prediction';
    } else {
      // Extract first few meaningful words
      const words = query.split(' ').filter(w => w.length > 3).slice(0, 3);
      return words.length > 0 ? words.join(' ') : 'New Chat';
    }
  };

  const handleSendMessage = async (content: string, file?: File) => {
    // Create chat on first message if it doesn't exist
    let currentChatId = chatId;

    if (!currentChatId) {
      try {
        // Generate title based on user's query
        const chatTitle = generateChatTitle(content);
        console.log("Creating new chat with title:", chatTitle);

        const chat = await createChat({
          title: chatTitle,
        });
        currentChatId = chat._id;
        setChatId(currentChatId);

        // Update URL to include chat ID
        window.history.pushState({}, '', `/?chat=${currentChatId}`);
      } catch (error) {
        console.error("Failed to create chat:", error);
        toast({
          variant: "destructive",
          title: "Error",
          description: "Failed to create chat. Please try again.",
        });
        return;
      }
    }

    // Add user message to UI immediately
    const userMessage: Message = {
      role: "user",
      content: file ? `Uploaded: ${file.name}\n${content}` : content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Send message to backend - use agent or regular chat based on toggle
      const response = useAgent
        ? await sendMessageToAgent({
            chat_id: currentChatId,
            content: userMessage.content,
          })
        : await sendMessage({
            chat_id: currentChatId,
            content: userMessage.content,
          });

      // Add assistant response to UI
      const assistantMessage: Message = {
        role: "assistant",
        content: response.content,
        queryType: response.query_type,
        timestamp: new Date(response.timestamp),
        metadata: {
          ...response.metadata,
          // Agent returns resources at top level, merge into metadata
          kaggle_datasets: response.kaggle_datasets || response.metadata?.kaggle_datasets,
          huggingface_datasets: response.huggingface_datasets || response.metadata?.huggingface_datasets,
          huggingface_models: response.huggingface_models || response.metadata?.huggingface_models
        },
      };

      // Debug: Log datasets if present
      const datasetsFound = response.kaggle_datasets || response.metadata?.kaggle_datasets;
      if (datasetsFound && datasetsFound.length > 0) {
        console.log("Received datasets:", datasetsFound);

        // Update chat title if this was the first message (chat just created)
        // and datasets were found
        if (messages.length <= 2) { // Welcome message + user message
          try {
            // Enhance the title based on the type of datasets found
            const enhancedTitle = generateChatTitle(content);
            await updateChat(currentChatId, { title: enhancedTitle });
            console.log("Updated chat title to:", enhancedTitle);
          } catch (error) {
            console.error("Failed to update chat title:", error);
            // Don't show error to user, title update is not critical
          }
        }
      }

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Failed to send message:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send message. Please try again.",
      });

      // Remove the user message if sending failed
      setMessages((prev) => prev.filter((msg) => msg !== userMessage));
    } finally {
      setIsLoading(false);
    }
  };

  if (isInitializing) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Initializing chat...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Agent Mode Toggle */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-4xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sparkles className="h-5 w-5 text-primary" />
              <div>
                <Label htmlFor="agent-mode" className="text-sm font-medium cursor-pointer">
                  AI Agent Mode
                </Label>
                <p className="text-xs text-muted-foreground">
                  {useAgent
                    ? "Agent will automatically find datasets & suggest models"
                    : "Regular chat mode - manual dataset search"}
                </p>
              </div>
            </div>
            <Switch
              id="agent-mode"
              checked={useAgent}
              onCheckedChange={setUseAgent}
            />
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="max-w-4xl mx-auto p-6 space-y-6">
          {messages.map((message, index) => (
            <div key={index}>
              {message.content && (
                <MessageBubble
                  role={message.role}
                  content={message.content}
                  queryType={(message as any).queryType}
                  timestamp={message.timestamp}
                  metadata={(message as any).metadata}
                />
              )}

              {/* Display Kaggle Dataset Suggestions */}
              {message.metadata?.kaggle_datasets && message.metadata.kaggle_datasets.length > 0 && (
                <div className="mt-4 space-y-3">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Database className="h-4 w-4 text-primary" />
                    <span>Suggested Datasets from Kaggle</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {message.metadata.kaggle_datasets.map((dataset, idx) => (
                      <KaggleDatasetCard
                        key={idx}
                        dataset={dataset}
                        chatId={chatId || ""}
                        onDatasetAdded={() => {
                          // Optionally refresh datasets or show a success message
                          toast({
                            title: "Success!",
                            description: "Dataset added to your collection. Check the Datasets tab!",
                          });
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Display HuggingFace Dataset Suggestions */}
              {message.metadata?.huggingface_datasets && message.metadata.huggingface_datasets.length > 0 && (
                <div className="mt-4 space-y-3">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Database className="h-4 w-4 text-orange-500" />
                    <span>Suggested Datasets from HuggingFace</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {message.metadata.huggingface_datasets.map((dataset: any, idx: number) => (
                      <HuggingFaceDatasetCard
                        key={idx}
                        dataset={dataset}
                        chatId={chatId || ""}
                        onDatasetAdded={() => {
                          toast({
                            title: "Success!",
                            description: "Dataset added to your collection. Check the Datasets tab!",
                          });
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Display HuggingFace Model Suggestions */}
              {message.metadata?.huggingface_models && message.metadata.huggingface_models.length > 0 && (
                <div className="mt-4 space-y-3">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Sparkles className="h-4 w-4 text-purple-500" />
                    <span>Recommended Models from HuggingFace</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {message.metadata.huggingface_models.map((model: any, idx: number) => (
                      <Card key={idx} className="hover:shadow-md transition-shadow">
                        <CardHeader className="pb-3">
                          <h3 className="font-semibold text-sm truncate">{model.name}</h3>
                        </CardHeader>
                        <CardFooter className="pt-0">
                          <Button
                            size="sm"
                            variant="outline"
                            className="w-full"
                            onClick={() => window.open(model.url, '_blank')}
                          >
                            <ExternalLink className="h-3 w-3 mr-2" />
                            View Model
                          </Button>
                        </CardFooter>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {(message as any).charts && (
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(message as any).charts.map((chart: any, chartIndex: number) => (
                    <SmartChart key={chartIndex} chart={chart} />
                  ))}
                </div>
              )}

              {(message as any).queryType === "data_based" && index === messages.length - 1 && (
                <Card className="mt-4 p-4 bg-accent/50">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-sm">Fine-tuning Recommended</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Your dataset shows unique patterns that could benefit from fine-tuning
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" data-testid="button-start-fine-tune">
                        Start Fine-tuning
                      </Button>
                    </div>
                  </div>
                </Card>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Gemini is thinking...</span>
            </div>
          )}
        </div>
      </ScrollArea>

      <ChatInput onSend={handleSendMessage} disabled={isLoading} />
    </div>
  );
}
