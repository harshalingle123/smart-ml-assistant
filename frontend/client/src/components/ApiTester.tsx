import { useState, memo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Copy, CheckCircle2, Play, AlertCircle, Loader2, Clock } from 'lucide-react';
import type { PredictionResponse } from '@/lib/types';

interface ApiTesterProps {
  apiKey?: string;
  endpoint?: string;
  onTest: (apiKey: string, text: string, endpoint?: string) => Promise<PredictionResponse>;
}

const CodeSnippet = memo<{ code: string; language: string }>(({ code, language }) => {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative">
      <pre className="bg-muted p-4 rounded-md text-xs overflow-x-auto">
        <code>{code}</code>
      </pre>
      <Button
        variant="ghost"
        size="sm"
        className="absolute top-2 right-2"
        onClick={copyToClipboard}
      >
        {copied ? (
          <CheckCircle2 className="h-4 w-4 text-green-600" />
        ) : (
          <Copy className="h-4 w-4" />
        )}
      </Button>
    </div>
  );
});

CodeSnippet.displayName = 'CodeSnippet';

export const ApiTester = memo<ApiTesterProps>(({ apiKey: defaultApiKey, endpoint: defaultEndpoint, onTest }) => {
  const [apiKey, setApiKey] = useState(defaultApiKey || '');
  const [endpoint, setEndpoint] = useState(defaultEndpoint || '');
  const [inputText, setInputText] = useState('');
  const [testing, setTesting] = useState(false);
  const [response, setResponse] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTest = async () => {
    if (!apiKey.trim()) {
      setError('Please enter an API key');
      return;
    }

    if (!inputText.trim()) {
      setError('Please enter text to analyze');
      return;
    }

    try {
      setTesting(true);
      setError(null);
      setResponse(null);

      const result = await onTest(apiKey, inputText, endpoint || undefined);
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'API test failed');
    } finally {
      setTesting(false);
    }
  };

  const generateCodeSnippets = () => {
    const apiKeyValue = apiKey || 'YOUR_API_KEY';
    const endpointValue = endpoint || 'https://api.yourplatform.com/v1/sentiment/vader';
    const textValue = inputText || 'Your text here';

    return {
      curl: `curl -X POST ${endpointValue} \\
  -H "Authorization: Bearer ${apiKeyValue}" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "${textValue}"}'`,

      python: `import requests

api_key = "${apiKeyValue}"
endpoint = "${endpointValue}"

response = requests.post(
    endpoint,
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={"text": "${textValue}"}
)

result = response.json()
print(result)`,

      javascript: `const apiKey = "${apiKeyValue}";
const endpoint = "${endpointValue}";

const response = await fetch(endpoint, {
  method: "POST",
  headers: {
    "Authorization": \`Bearer \${apiKey}\`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    text: "${textValue}"
  })
});

const result = await response.json();
console.log(result);`,
    };
  };

  const snippets = generateCodeSnippets();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Test Your API
          </CardTitle>
          <CardDescription>
            Test your API endpoint in real-time and see the response
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="api-key-input">API Key</Label>
            <Input
              id="api-key-input"
              type="password"
              placeholder="sk_live_..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="font-mono"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="endpoint-input">Endpoint (Optional)</Label>
            <Input
              id="endpoint-input"
              type="text"
              placeholder="https://api.yourplatform.com/v1/sentiment/vader"
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              className="font-mono text-sm"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="text-input">Text to Analyze</Label>
            <Textarea
              id="text-input"
              placeholder="Enter text to analyze (e.g., 'This product is amazing!')"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              rows={4}
            />
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button
            onClick={handleTest}
            disabled={testing || !apiKey || !inputText}
            className="w-full"
            size="lg"
          >
            {testing ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testing API...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Test API
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {response && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center justify-between">
              <span>Response</span>
              <Badge variant="secondary" className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {response.latency_ms}ms
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs font-semibold">Result</Label>
              <pre className="bg-muted p-4 rounded-md text-xs overflow-x-auto">
                {JSON.stringify(response, null, 2)}
              </pre>
            </div>

            {response.sentiment && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Sentiment</p>
                  <Badge
                    variant={
                      response.sentiment.label === 'POSITIVE'
                        ? 'default'
                        : response.sentiment.label === 'NEGATIVE'
                        ? 'destructive'
                        : 'secondary'
                    }
                  >
                    {response.sentiment.label}
                  </Badge>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Confidence</p>
                  <p className="text-sm font-semibold">
                    {((response.confidence || 0) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            )}

            {response.usage && (
              <Alert>
                <AlertDescription className="text-xs">
                  <strong>Usage:</strong> {response.usage.requests_used.toLocaleString()} /{' '}
                  {response.usage.requests_remaining.toLocaleString()} requests remaining
                  (resets {new Date(response.usage.reset_date).toLocaleDateString()})
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Code Examples</CardTitle>
          <CardDescription>
            Copy these code snippets to integrate the API into your application
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="curl" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="curl">cURL</TabsTrigger>
              <TabsTrigger value="python">Python</TabsTrigger>
              <TabsTrigger value="javascript">JavaScript</TabsTrigger>
            </TabsList>

            <TabsContent value="curl" className="space-y-2">
              <CodeSnippet code={snippets.curl} language="bash" />
            </TabsContent>

            <TabsContent value="python" className="space-y-2">
              <CodeSnippet code={snippets.python} language="python" />
            </TabsContent>

            <TabsContent value="javascript" className="space-y-2">
              <CodeSnippet code={snippets.javascript} language="javascript" />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
});

ApiTester.displayName = 'ApiTester';
