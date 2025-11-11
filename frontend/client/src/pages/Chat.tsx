import { useState } from "react";
import { MessageBubble } from "@/components/MessageBubble";
import { ChatInput } from "@/components/ChatInput";
import { SmartChart } from "@/components/SmartChart";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Key } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Message {
  role: "user" | "assistant";
  content: string;
  queryType?: "simple" | "data_based";
  timestamp: Date;
  charts?: any[];
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Welcome to Smart ML Assistant! I can help you with sentiment analysis, text classification, and more. You can either:\n\n• Ask me to classify text directly\n• Upload a CSV dataset for analysis and fine-tuning\n\nHow can I help you today?",
      timestamp: new Date(),
    },
  ]);

  const handleSendMessage = (content: string, file?: File) => {
    const userMessage = {
      role: "user" as const,
      content: file ? `Uploaded: ${file.name}\n${content}` : content,
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);

    setTimeout(() => {
      const hasFile = !!file;
      const queryType = hasFile || content.toLowerCase().includes("analyze") || content.toLowerCase().includes("dataset")
        ? "data_based" as const
        : "simple" as const;

      const assistantMessage = {
        role: "assistant" as const,
        content: queryType === "simple"
          ? "Detected Query Type: Simple. Running sentiment analysis using bert-base-uncased model...\n\nPrediction: Positive\nConfidence: 92%"
          : "Detected Query Type: Data-Based. I found your dataset has 5,420 rows with sentiment patterns. Would you like to fine-tune a model for better accuracy?",
        queryType,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (queryType === "simple") {
        setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant" as const,
              content: "",
              timestamp: new Date(),
              charts: [
                {
                  type: "bar" as const,
                  title: "Prediction Confidence",
                  data: { Positive: 0.92, Negative: 0.08 },
                },
              ],
            },
          ]);
        }, 500);
      } else {
        setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant" as const,
              content: "",
              timestamp: new Date(),
              charts: [
                {
                  type: "pie" as const,
                  title: "Sentiment Distribution",
                  data: { Positive: 0.65, Negative: 0.25, Neutral: 0.10 },
                },
                {
                  type: "line" as const,
                  title: "Sentiment Over Time",
                  data: [
                    { date: "Jan", positive: 65, negative: 35 },
                    { date: "Feb", positive: 70, negative: 30 },
                    { date: "Mar", positive: 75, negative: 25 },
                    { date: "Apr", positive: 72, negative: 28 },
                  ],
                },
              ],
            },
          ]);
        }, 500);
      }
    }, 1000);
  };

  return (
    <div className="flex flex-col h-full">
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
                />
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

              {(message as any).role === "assistant" && (message as any).content.includes("Complete") && (
                <div className="mt-4 flex gap-2">
                  <Button variant="outline" size="sm" data-testid="button-download-model">
                    <Download className="h-4 w-4 mr-1" />
                    Download Model
                  </Button>
                  <Button variant="outline" size="sm" data-testid="button-generate-api">
                    <Key className="h-4 w-4 mr-1" />
                    Generate API
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      <ChatInput onSend={handleSendMessage} />
    </div>
  );
}
