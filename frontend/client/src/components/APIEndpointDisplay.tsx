import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Copy, Check } from "lucide-react";
import { useState } from "react";

interface APIEndpointDisplayProps {
  modelId: string;
  modelName: string;
  apiKey: string;
}

export function APIEndpointDisplay({ modelId, modelName, apiKey }: APIEndpointDisplayProps) {
  const [copied, setCopied] = useState(false);
  
  const endpoint = `https://api.mlassistant.com/v1/models/${modelId}/predict`;
  
  const curlExample = `curl -X POST ${endpoint} \\
  -H "Authorization: Bearer ${apiKey}" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "I love this product!"}'`;

  const responseExample = `{
  "prediction": "Positive",
  "confidence": 0.92,
  "model": "${modelName}"
}`;

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>API Endpoint</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Endpoint URL</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleCopy(endpoint)}
              data-testid="button-copy-endpoint"
            >
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
          <div className="rounded-md bg-muted p-3">
            <code className="text-xs font-mono break-all">{endpoint}</code>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">API Key</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleCopy(apiKey)}
              data-testid="button-copy-key"
            >
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
          <div className="rounded-md bg-muted p-3">
            <code className="text-xs font-mono">{apiKey}</code>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Example Request</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleCopy(curlExample)}
              data-testid="button-copy-curl"
            >
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
          <div className="rounded-md bg-muted p-3 overflow-x-auto">
            <pre className="text-xs font-mono">{curlExample}</pre>
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium">Example Response</p>
          <div className="rounded-md bg-muted p-3">
            <pre className="text-xs font-mono">{responseExample}</pre>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
