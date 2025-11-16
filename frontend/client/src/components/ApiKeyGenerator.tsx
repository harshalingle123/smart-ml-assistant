import { useState, memo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Copy, CheckCircle2, Key, Calendar, Zap, AlertCircle, Loader2 } from 'lucide-react';
import type { DirectAccessModel, DirectAccessKey } from '@/lib/types';

interface ApiKeyGeneratorProps {
  models: DirectAccessModel[];
  onGenerate: (data: {
    modelId: string;
    usagePlan: string;
    priority: string;
  }) => Promise<DirectAccessKey>;
}

interface GeneratedKeyDisplayProps {
  apiKey: DirectAccessKey;
  model: DirectAccessModel;
}

const GeneratedKeyDisplay = memo<GeneratedKeyDisplayProps>(({ apiKey, model }) => {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const expiryDate = apiKey.expires_at
    ? new Date(apiKey.expires_at).toLocaleDateString()
    : 'Never';

  return (
    <div className="space-y-4">
      <Alert className="border-green-200 bg-green-50 dark:bg-green-950 dark:border-green-800">
        <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
        <AlertDescription className="text-green-800 dark:text-green-200">
          Your API key has been generated successfully! Copy it now - you won't be able to see it again.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">API Credentials</CardTitle>
          <CardDescription>Use these credentials to access the {model.name}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label className="text-xs font-semibold">API Key</Label>
            <div className="flex gap-2">
              <Input
                value={apiKey.api_key}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => copyToClipboard(apiKey.api_key)}
              >
                {copied ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-xs font-semibold">Endpoint URL</Label>
            <div className="flex gap-2">
              <Input
                value={apiKey.endpoint}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => copyToClipboard(apiKey.endpoint)}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Model</p>
              <p className="text-sm font-medium">{model.name}</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Task</p>
              <p className="text-sm font-medium capitalize">{apiKey.task}</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Free Tier Limit</p>
              <p className="text-sm font-medium">
                {apiKey.free_tier_limit.toLocaleString()} requests/month
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Expires</p>
              <p className="text-sm font-medium">{expiryDate}</p>
            </div>
          </div>

          <div className="pt-2">
            <Badge variant="secondary" className="text-xs">
              Status: {apiKey.status}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Quick Start</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold mb-2">cURL</p>
              <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
{`curl -X POST ${apiKey.endpoint} \\
  -H "Authorization: Bearer ${apiKey.api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Your text here"}'`}
              </pre>
            </div>

            <div>
              <p className="text-xs font-semibold mb-2">Python</p>
              <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
{`import requests

response = requests.post(
    "${apiKey.endpoint}",
    headers={"Authorization": "Bearer ${apiKey.api_key}"},
    json={"text": "Your text here"}
)
print(response.json())`}
              </pre>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
});

GeneratedKeyDisplay.displayName = 'GeneratedKeyDisplay';

export const ApiKeyGenerator = memo<ApiKeyGeneratorProps>(({ models, onGenerate }) => {
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [usagePlan, setUsagePlan] = useState<string>('free');
  const [priority, setPriority] = useState<string>('speed');
  const [generating, setGenerating] = useState(false);
  const [generatedKey, setGeneratedKey] = useState<DirectAccessKey | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedModel = models.find((m) => m.id === selectedModelId);

  const handleGenerate = async () => {
    if (!selectedModelId) {
      setError('Please select a model');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      const key = await onGenerate({
        modelId: selectedModelId,
        usagePlan,
        priority,
      });
      setGeneratedKey(key);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate API key');
    } finally {
      setGenerating(false);
    }
  };

  const handleReset = () => {
    setGeneratedKey(null);
    setSelectedModelId('');
    setUsagePlan('free');
    setPriority('speed');
    setError(null);
  };

  if (generatedKey && selectedModel) {
    return (
      <div className="space-y-4">
        <GeneratedKeyDisplay apiKey={generatedKey} model={selectedModel} />
        <Button onClick={handleReset} variant="outline" className="w-full">
          Generate Another Key
        </Button>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Key className="h-5 w-5" />
          Generate API Key
        </CardTitle>
        <CardDescription>
          Select a model and usage plan to generate your instant API access
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-2">
          <Label htmlFor="model-select">Select Model</Label>
          <Select value={selectedModelId} onValueChange={setSelectedModelId}>
            <SelectTrigger id="model-select">
              <SelectValue placeholder="Choose a model...">
                {selectedModelId
                  ? models.find((m) => m.id === selectedModelId)?.name || "Choose a model..."
                  : "Choose a model..."
                }
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              {models.map((model) => (
                <SelectItem key={model.id} value={model.id}>
                  <div className="flex items-center justify-between w-full gap-4">
                    <span>{model.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {model.latency_ms}ms • {(model.accuracy * 100).toFixed(0)}%
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedModel && (
            <p className="text-xs text-muted-foreground">
              {selectedModel.description}
            </p>
          )}
        </div>

        <div className="space-y-3">
          <Label>Usage Plan</Label>
          <RadioGroup value={usagePlan} onValueChange={setUsagePlan}>
            <div className="flex items-start space-x-3 border rounded-lg p-3 hover:bg-muted/50 transition-colors">
              <RadioGroupItem value="free" id="plan-free" className="mt-0.5" />
              <Label htmlFor="plan-free" className="flex-1 cursor-pointer">
                <div className="font-medium">Free Tier</div>
                <div className="text-xs text-muted-foreground">
                  {selectedModel
                    ? `${selectedModel.free_tier.toLocaleString()} requests/month`
                    : 'Up to 10K requests/month'}
                </div>
              </Label>
            </div>

            <div className="flex items-start space-x-3 border rounded-lg p-3 hover:bg-muted/50 transition-colors">
              <RadioGroupItem value="pay_as_you_go" id="plan-payg" className="mt-0.5" />
              <Label htmlFor="plan-payg" className="flex-1 cursor-pointer">
                <div className="font-medium">Pay As You Go</div>
                <div className="text-xs text-muted-foreground">
                  {selectedModel
                    ? `$${(selectedModel.pricing.per_request * 1000).toFixed(2)} per 1K requests`
                    : 'Pay only for what you use'}
                </div>
              </Label>
            </div>

            <div className="flex items-start space-x-3 border rounded-lg p-3 hover:bg-muted/50 transition-colors">
              <RadioGroupItem value="professional" id="plan-pro" className="mt-0.5" />
              <Label htmlFor="plan-pro" className="flex-1 cursor-pointer">
                <div className="font-medium">Professional</div>
                <div className="text-xs text-muted-foreground">
                  $49/month • 100K requests included
                </div>
              </Label>
            </div>
          </RadioGroup>
        </div>

        <div className="space-y-3">
          <Label>Priority</Label>
          <RadioGroup value={priority} onValueChange={setPriority}>
            <div className="flex items-start space-x-3 border rounded-lg p-3 hover:bg-muted/50 transition-colors">
              <RadioGroupItem value="speed" id="priority-speed" className="mt-0.5" />
              <Label htmlFor="priority-speed" className="flex-1 cursor-pointer">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  <span className="font-medium">Speed</span>
                </div>
                <div className="text-xs text-muted-foreground">Lowest latency</div>
              </Label>
            </div>

            <div className="flex items-start space-x-3 border rounded-lg p-3 hover:bg-muted/50 transition-colors">
              <RadioGroupItem value="accuracy" id="priority-accuracy" className="mt-0.5" />
              <Label htmlFor="priority-accuracy" className="flex-1 cursor-pointer">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" />
                  <span className="font-medium">Accuracy</span>
                </div>
                <div className="text-xs text-muted-foreground">Best results</div>
              </Label>
            </div>

            <div className="flex items-start space-x-3 border rounded-lg p-3 hover:bg-muted/50 transition-colors">
              <RadioGroupItem value="cost" id="priority-cost" className="mt-0.5" />
              <Label htmlFor="priority-cost" className="flex-1 cursor-pointer">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span className="font-medium">Cost</span>
                </div>
                <div className="text-xs text-muted-foreground">Most economical</div>
              </Label>
            </div>
          </RadioGroup>
        </div>

        <Button
          onClick={handleGenerate}
          disabled={!selectedModelId || generating}
          className="w-full"
          size="lg"
        >
          {generating ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Generating Key...
            </>
          ) : (
            <>
              <Key className="h-4 w-4 mr-2" />
              Generate API Key
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
});

ApiKeyGenerator.displayName = 'ApiKeyGenerator';
