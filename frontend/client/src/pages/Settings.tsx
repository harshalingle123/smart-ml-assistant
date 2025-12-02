import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ApiKeyForm } from "@/components/ApiKeyForm";
import { getApiKeys, deleteApiKey, getModel, getModelSampleData } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth";
import { useToast } from "@/hooks/use-toast";
import { Copy, CheckCircle2, Code } from "lucide-react";
import { getApiUrl } from "@/lib/env";

export default function Settings() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [expandedExamples, setExpandedExamples] = useState<{ [key: string]: boolean }>({});
  const [modelDetails, setModelDetails] = useState<{ [key: string]: any }>({});
  const [sampleData, setSampleData] = useState<{ [key: string]: any }>({});
  const [loadingExamples, setLoadingExamples] = useState<{ [key: string]: boolean }>({});
  const [currentUserEmail, setCurrentUserEmail] = useState<string>("your-email@example.com");

  // Get API URL dynamically (production or localhost)
  const apiUrl = getApiUrl();

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ["apiKeys"],
    queryFn: getApiKeys,
  });

  // Fetch current user's email
  useEffect(() => {
    const fetchUserEmail = async () => {
      try {
        const token = localStorage.getItem("token");
        if (token) {
          const user = await getCurrentUser(token);
          if (user.email) {
            setCurrentUserEmail(user.email);
          }
        }
      } catch (error) {
        console.error("Failed to fetch user email:", error);
      }
    };
    fetchUserEmail();
  }, []);

  const deleteMutation = useMutation({
    mutationFn: deleteApiKey,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
      toast({
        title: "API Key Revoked",
        description: "The API key has been successfully revoked.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.message || "Failed to revoke API key.",
        variant: "destructive",
      });
    },
  });

  const handleCopy = (apiKey: string) => {
    navigator.clipboard.writeText(apiKey);
    setCopiedKey(apiKey);
    toast({
      title: "Copied!",
      description: "API key copied to clipboard.",
    });
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleRevoke = (apiKeyId: string) => {
    if (confirm("Are you sure you want to revoke this API key? This action cannot be undone.")) {
      deleteMutation.mutate(apiKeyId);
    }
  };

  const handleShowExample = async (apiKeyId: string, modelId: string) => {
    const isExpanded = expandedExamples[apiKeyId];

    // Toggle expansion
    setExpandedExamples(prev => ({ ...prev, [apiKeyId]: !isExpanded }));

    // If collapsing, just return
    if (isExpanded) return;

    // If expanding and we don't have data yet, fetch it
    if (!modelDetails[modelId] || !sampleData[modelId]) {
      setLoadingExamples(prev => ({ ...prev, [apiKeyId]: true }));

      try {
        // Fetch model details and sample data in parallel
        const [model, samples] = await Promise.all([
          getModel(modelId),
          getModelSampleData(modelId, 2)
        ]);

        setModelDetails(prev => ({ ...prev, [modelId]: model }));
        setSampleData(prev => ({ ...prev, [modelId]: samples }));
      } catch (error) {
        console.error("Failed to fetch example data:", error);
        toast({
          title: "Error",
          description: "Failed to load example data. Make sure the model has training data.",
          variant: "destructive",
        });
      } finally {
        setLoadingExamples(prev => ({ ...prev, [apiKeyId]: false }));
      }
    }
  };

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-semibold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account and application settings
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>
            Manage your API keys for programmatic access to your trained models.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <p>Loading...</p>
          ) : apiKeys && apiKeys.length === 0 ? (
            <div className="text-center p-8 border-2 border-dashed rounded-lg">
              <p className="text-muted-foreground mb-4">No API keys yet. Generate your first API key to get started.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {apiKeys?.map((apiKey: any) => {
                const apiKeyId = apiKey.id || apiKey._id;
                const modelId = apiKey.model_id;
                const isExpanded = expandedExamples[apiKeyId];
                const isLoading = loadingExamples[apiKeyId];
                const model = modelDetails[modelId];
                const samples = sampleData[modelId];

                return (
                  <Card key={apiKeyId}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="space-y-1 flex-1">
                          <p className="font-semibold">{apiKey.name}</p>
                          <p className="text-sm text-muted-foreground font-mono break-all">
                            {apiKey.key || apiKey.api_key || '••••••••••••••••'}
                          </p>
                          <div className="flex gap-4 text-xs text-muted-foreground">
                            <span>Created: {new Date(apiKey.created_at || apiKey.createdAt).toLocaleDateString()}</span>
                            {modelId && (
                              <span>Model ID: {modelId}</span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleCopy(apiKey.key || apiKey.api_key)}
                          >
                            {copiedKey === (apiKey.key || apiKey.api_key) ? (
                              <>
                                <CheckCircle2 className="h-4 w-4 mr-1 text-green-600" />
                                Copied
                              </>
                            ) : (
                              <>
                                <Copy className="h-4 w-4 mr-1" />
                                Copy
                              </>
                            )}
                          </Button>
                          {modelId && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleShowExample(apiKeyId, modelId)}
                              disabled={isLoading}
                            >
                              <Code className="h-4 w-4 mr-1" />
                              {isLoading ? "Loading..." : isExpanded ? "Hide Example" : "Show Example"}
                            </Button>
                          )}
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleRevoke(apiKeyId)}
                            disabled={deleteMutation.isPending}
                          >
                            {deleteMutation.isPending ? "Revoking..." : "Revoke"}
                          </Button>
                        </div>
                      </div>

                      {isExpanded && model && (
                        <div className="mt-4 pt-4 border-t space-y-4">
                          <div className="bg-muted/50 p-4 rounded-lg space-y-3">
                            <div>
                              <h4 className="text-sm font-semibold mb-2">Model Information</h4>
                              <div className="grid grid-cols-2 gap-2 text-xs">
                                <div>
                                  <span className="text-muted-foreground">Name:</span>
                                  <span className="ml-2 font-medium">{model.name || model.base_model}</span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground">Task:</span>
                                  <span className="ml-2 font-medium">{model.task_type || 'classification'}</span>
                                </div>
                                {model.accuracy && (
                                  <div>
                                    <span className="text-muted-foreground">Accuracy:</span>
                                    <span className="ml-2 font-medium">{model.accuracy}</span>
                                  </div>
                                )}
                              </div>
                            </div>

                            {samples && samples.samples && samples.samples.length > 0 && (
                              <div>
                                <h4 className="text-sm font-semibold mb-2">Sample Input (from training data)</h4>
                                <pre className="bg-background p-3 rounded text-xs overflow-x-auto border">
{JSON.stringify(samples.samples[0].input, null, 2)}
                                </pre>
                                {samples.samples[0].actual_target !== null && (
                                  <p className="text-xs text-muted-foreground mt-1">
                                    Expected output: <span className="font-medium">{samples.samples[0].actual_target}</span>
                                  </p>
                                )}
                              </div>
                            )}

                            <div>
                              <h4 className="text-sm font-semibold mb-2">Python Example (ready to copy & run!)</h4>
                              <pre className="bg-background p-3 rounded text-xs overflow-x-auto border">
{`import requests

# Login to get JWT token
login_response = requests.post(
    "${apiUrl}/api/auth/login",
    json={
        "email": "${currentUserEmail}",  # Your email
        "password": "your-password"  # UPDATE THIS
    }
)
token = login_response.json()["access_token"]

# Make prediction with real model
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Real model ID
model_id = "${modelId}"

# Sample input (from your training data)
input_data = ${samples && samples.samples && samples.samples[0] ? JSON.stringify(samples.samples[0].input, null, 2) : '{\n    "text": "Your input here"\n}'}

response = requests.post(
    f"${apiUrl}/api/models/{model_id}/predict",
    headers=headers,
    json=input_data
)

result = response.json()
print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['confidence']}")

# Optional: Print probabilities if available
if 'probabilities' in result:
    print("\\nProbabilities:")
    for key, value in result['probabilities'].items():
        print(f"  {key}: {value:.4f}")`}
                              </pre>
                              <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">
                                ⚠️ Only update your password, then copy & run!
                              </p>
                            </div>

                            <div>
                              <h4 className="text-sm font-semibold mb-2">cURL Example (ready to copy & run!)</h4>
                              <pre className="bg-background p-3 rounded text-xs overflow-x-auto border">
{`# First, login to get token
TOKEN=$(curl -X POST "${apiUrl}/api/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "${currentUserEmail}", "password": "your-password"}' \\
  | jq -r '.access_token')

# Make prediction
curl -X POST "${apiUrl}/api/models/${modelId}/predict" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '${samples && samples.samples && samples.samples[0] ? JSON.stringify(samples.samples[0].input) : '{"text": "Your input here"}'}'`}
                              </pre>
                              <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">
                                ⚠️ Replace "your-password" with your actual password, then copy & run!
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>Generate New Key</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Generate New API Key</DialogTitle>
                <DialogDescription>
                  Select a model to generate a new API key for programmatic access.
                </DialogDescription>
              </DialogHeader>
              <ApiKeyForm onSuccess={() => setIsDialogOpen(false)} />
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
