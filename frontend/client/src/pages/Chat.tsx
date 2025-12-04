import { useState, useEffect } from "react";
import { MessageBubble } from "@/components/MessageBubble";
import { ChatInput } from "@/components/ChatInput";
import { SmartChart } from "@/components/SmartChart";
import { KaggleDatasetCard } from "@/components/KaggleDatasetCard";
import { HuggingFaceDatasetCard } from "@/components/HuggingFaceDatasetCard";
import { DownloadableDatasetCard } from "@/components/DownloadableDatasetCard";
import { Card, CardHeader, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Database, ExternalLink, Sparkles, Package } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getChatMessages } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useChat } from "@/hooks/useChat";
import { useTraining } from "@/hooks/useTraining";
import { Message } from "@/types/chat";

export default function Chat() {
  const { messages, setMessages, chatId, setChatId, isLoading, handleSendMessage, addMessage } = useChat();
  const { isTraining, startTraining } = useTraining();
  const [isInitializing, setIsInitializing] = useState(true);
  const [useAgent, setUseAgent] = useState(true);
  const { toast } = useToast();

  // Initialize chat
  useEffect(() => {
    const initializeChat = async () => {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const existingChatId = urlParams.get('chat');
        const datasetId = urlParams.get('dataset');
        const shouldTrain = urlParams.get('train') === 'true';

        if (existingChatId) {
          console.log("Loading existing chat:", existingChatId);
          setChatId(existingChatId);

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

          if (shouldTrain && datasetId) {
            handleStartTraining(datasetId, existingChatId);
          }
        } else {
          setMessages([
            {
              role: "assistant",
              content: "Welcome to AutoML! I'm powered by Google Gemini with AI Agent capabilities and can help you with:\n\n✨ **Agent Mode (Recommended)**\nI automatically:\n• Understand your ML requirements\n• Find relevant datasets from Kaggle & HuggingFace\n• Suggest the best models for your task\n• Provide cost & time estimates\n\n💬 **You can ask me:**\n• \"I need a dataset to predict house prices\"\n• \"Find sentiment analysis datasets\"\n• \"Classify customer support tickets with <200ms latency\"\n• \"What's the best model for image classification?\"\n\nAgent Mode is ON by default. Toggle it off for regular chat.\n\nHow can I help you today?",
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
  }, [setChatId, setMessages, toast]);

  const handleStartTraining = (datasetId: string, currentChatId: string) => {
    startTraining(datasetId, currentChatId, (data) => {
      if (data.type === "status" || data.type === "progress" || data.type === "error") {
        addMessage({
          role: "assistant",
          content: data.message,
          timestamp: new Date()
        });
      } else if (data.type === "complete") {
        addMessage({
          role: "assistant",
          content: data.message,
          timestamp: new Date(),
          metadata: {
            model_id: data.model_id,
            best_model: data.best_model,
            metrics: data.metrics
          }
        });
        window.history.pushState({}, '', `/?chat=${currentChatId}`);
      }
    });
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
                  queryType={message.queryType}
                  timestamp={message.timestamp}
                  metadata={message.metadata}
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
                    {message.metadata.kaggle_datasets.map((dataset: any, idx: number) => (
                      <KaggleDatasetCard
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

              {/* Display Downloadable Datasets Section */}
              {message.metadata?.downloadable_datasets && message.metadata.downloadable_datasets.length > 0 && (
                <div className="mt-4 space-y-3">
                  <div className="flex items-center gap-2 px-3 py-2 bg-primary/5 rounded-lg border border-primary/20">
                    <Package className="h-5 w-5 text-primary" />
                    <span className="font-semibold text-sm">Download Options</span>
                    <Badge variant="secondary" className="ml-auto">
                      {message.metadata.downloadable_datasets.length} datasets
                    </Badge>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {message.metadata.downloadable_datasets.map((dataset: any, idx: number) => (
                      <DownloadableDatasetCard
                        key={`${dataset.source}-${dataset.id}-${idx}`}
                        id={dataset.id}
                        title={dataset.title}
                        source={dataset.source}
                        url={dataset.url}
                        downloads={dataset.downloads}
                        relevance_score={dataset.relevance_score}
                      />
                    ))}
                  </div>
                </div>
              )}

              {message.charts && (
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                  {message.charts.map((chart: any, chartIndex: number) => (
                    <SmartChart key={chartIndex} chart={chart} />
                  ))}
                </div>
              )}

              {message.queryType === "data_based" && index === messages.length - 1 && (
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
          {(isLoading || isTraining) && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">{isTraining ? "Training model..." : "AutoML is thinking..."}</span>
            </div>
          )}
        </div>
      </ScrollArea>

      <ChatInput onSend={(content, file) => handleSendMessage(content, useAgent, file)} disabled={isLoading || isTraining} />
    </div>
  );
}

