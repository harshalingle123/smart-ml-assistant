import { useState, useEffect } from "react";
import { useRoute, useLocation } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, ArrowLeft, Download, Target, Table2, FileText, CheckCircle, Brain } from "lucide-react";
import { getDataset, getDatasets, inspectDataset, checkKaggleStatus, updateDataset, createChat, checkBackendHealth } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Dataset {
  _id: string;
  id?: string;
  name: string;
  fileName: string;
  rowCount: number;
  columnCount: number;
  fileSize: number;
  status: string;
  source?: string;
  kaggleRef?: string;
  schema?: Array<{
    name: string;
    dtype: string;
    nullCount?: number;
    uniqueCount?: number;
  }>;
  columnSchema?: Array<{
    name: string;
    dtype: string;
    nullCount?: number;
    uniqueCount?: number;
  }>;
  sampleData?: Array<Record<string, any>>;
  targetColumn?: string;
}

export default function DatasetDetails() {
  const [, params] = useRoute("/datasets/:id");
  const [, setLocation] = useLocation();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [loading, setLoading] = useState(true);
  const [inspecting, setInspecting] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState<string>("");
  const [kaggleConfigured, setKaggleConfigured] = useState<boolean>(false);
  const [checkingKaggle, setCheckingKaggle] = useState(true);
  const [training, setTraining] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 2;
  const { toast } = useToast();

  useEffect(() => {
    if (params?.id) {
      loadDataset(params.id);
    }
    checkKaggleConfiguration();
  }, [params?.id]);

  const checkKaggleConfiguration = async () => {
    try {
      setCheckingKaggle(true);
      const status = await checkKaggleStatus();
      setKaggleConfigured(status.configured);
    } catch (error) {
      console.error("Failed to check Kaggle status:", error);
      setKaggleConfigured(false);
    } finally {
      setCheckingKaggle(false);
    }
  };

  const loadDataset = async (id: string) => {
    try {
      setLoading(true);
      console.log("[DatasetDetails] Loading dataset:", id);

      // Fetch single dataset with schema and sample data from Azure
      const data = await getDataset(id);

      // Normalize schema field (handle both 'schema' and 'columnSchema')
      const schema = data.schema || data.columnSchema || [];

      const mappedDataset = {
        ...data,
        id: data.id || data._id,
        schema: schema,
      };

      console.log("[DatasetDetails] Loaded dataset:", mappedDataset);
      console.log("[DatasetDetails] Schema:", mappedDataset.schema);
      console.log("[DatasetDetails] Schema length:", schema.length);
      console.log("[DatasetDetails] Sample Data:", mappedDataset.sampleData);
      console.log("[DatasetDetails] Sample Data length:", mappedDataset.sampleData?.length || 0);
      console.log("[DatasetDetails] Target Column:", mappedDataset.targetColumn);
      console.log("[DatasetDetails] Azure URL:", data.azureDatasetUrl);

      setDataset(mappedDataset);
      setSelectedTarget(mappedDataset.targetColumn || "");
    } catch (error) {
      console.error("Failed to load dataset:", error);

      const errorMessage = error instanceof Error ? error.message : "Failed to load dataset";

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });

      // Redirect to datasets list if dataset not found
      if (errorMessage.includes('not found')) {
        setTimeout(() => {
          setLocation('/datasets');
        }, 2000);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInspect = async () => {
    if (!dataset?.id) return;

    try {
      setInspecting(true);
      const result = await inspectDataset(dataset.id);

      // Reload dataset to get updated data
      await loadDataset(dataset.id);

      toast({
        title: "Success!",
        description: `Dataset inspected: ${result.rows} rows, ${result.columns} columns`,
      });
    } catch (error) {
      console.error("Failed to inspect dataset:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to inspect dataset",
        variant: "destructive",
      });
    } finally {
      setInspecting(false);
    }
  };

  const handleTargetColumnChange = async (newTarget: string) => {
    if (!dataset?.id) return;

    try {
      setSelectedTarget(newTarget);
      await updateDataset(dataset.id, { target_column: newTarget });

      toast({
        title: "Target Column Updated",
        description: `Target column set to: ${newTarget}`,
      });

      // Reload dataset to reflect changes
      await loadDataset(dataset.id);
    } catch (error) {
      console.error("Failed to update target column:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update target column",
        variant: "destructive",
      });
      // Revert selection on error
      setSelectedTarget(dataset.targetColumn || "");
    }
  };

  const handleTrainModel = async () => {
    if (!dataset?.id || !dataset.targetColumn) {
      toast({
        title: "Cannot Train",
        description: "Please select a target column first",
        variant: "destructive",
      });
      return;
    }

    if (dataset.status !== "ready") {
      toast({
        title: "Cannot Train",
        description: "Dataset must be inspected first. Click 'Download & Inspect Dataset'",
        variant: "destructive",
      });
      return;
    }

    try {
      setTraining(true);

      // 1. Check backend connectivity first
      console.log('[Training] Checking backend health...');
      const isHealthy = await checkBackendHealth();
      if (!isHealthy) {
        throw new Error('Backend server is not responding. Please try again later.');
      }

      // 2. Create or get chat for this dataset
      console.log('[Training] Creating chat for dataset:', dataset.id);

      let chat;
      try {
        chat = await createChat({
          title: `Training: ${dataset.name}`,
          dataset_id: dataset.id,
        });
      } catch (chatError) {
        console.error('[Training] Chat creation failed:', chatError);

        // Handle retry logic for Failed to fetch errors
        if (chatError instanceof Error && chatError.message.includes('Failed to fetch') && retryCount < MAX_RETRIES) {
          console.log(`[Training] Retry attempt ${retryCount + 1}/${MAX_RETRIES}`);
          setRetryCount(prev => prev + 1);

          toast({
            title: "Retrying...",
            description: `Connection failed. Retrying (${retryCount + 1}/${MAX_RETRIES})...`,
          });

          // Wait 2 seconds before retry
          await new Promise(resolve => setTimeout(resolve, 2000));
          return handleTrainModel(); // Recursive retry
        }

        // Provide specific error message
        if (chatError instanceof Error) {
          if (chatError.message.includes('timeout')) {
            throw new Error('Connection timeout. Please check your internet connection and try again.');
          } else if (chatError.message.includes('CORS')) {
            throw new Error('Server configuration error. Please contact support.');
          } else {
            throw new Error(`Failed to initialize training: ${chatError.message}`);
          }
        } else {
          throw new Error('Failed to initialize training. Please try again.');
        }
      }

      // 3. Get the chat ID from response
      const chatId = chat._id || chat.id;

      if (!chatId) {
        throw new Error("Failed to get chat ID from response. Please try again.");
      }

      console.log('[Training] Chat created successfully:', chatId);

      // Reset retry count on success
      setRetryCount(0);

      // 4. Navigate to chat page with dataset and training params
      setLocation(`/?chat=${chatId}&dataset=${dataset.id}&train=true`);

      toast({
        title: "Starting Training",
        description: "Opening chat view to show live progress...",
      });
    } catch (error) {
      console.error("[Training] Failed to start training:", error);

      // Show user-friendly error message
      let errorMessage = "Failed to start training. Please try again.";

      if (error instanceof Error) {
        if (error.message.includes('timeout')) {
          errorMessage = "Connection timeout. Please check your internet connection.";
        } else if (error.message.includes('not responding')) {
          errorMessage = "Backend server is not responding. Please try again in a few moments.";
        } else if (error.message.includes('Failed to fetch')) {
          errorMessage = "Network error. Please check your connection and try again.";
        } else {
          errorMessage = error.message;
        }
      }

      toast({
        title: "Training Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setTraining(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes || isNaN(bytes) || bytes === 0) return "Unknown";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-muted-foreground">Dataset not found</p>
        <Button onClick={() => setLocation("/datasets")} className="mt-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Datasets
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setLocation("/datasets")}
            className="mb-2"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Datasets
          </Button>
          <h1 className="text-3xl font-semibold">{dataset.name}</h1>
          <p className="text-muted-foreground mt-1">{dataset.fileName}</p>
        </div>
        <Badge
          variant={
            dataset.status === "ready" ? "default" :
            dataset.status === "pending" || dataset.status === "pending_download" ? "secondary" :
            "outline"
          }
          className={
            dataset.status === "pending" ? "bg-yellow-500/10 text-yellow-700 border-yellow-500/20" :
            dataset.status === "pending_download" ? "bg-blue-500/10 text-blue-700 border-blue-500/20" :
            dataset.status === "ready" ? "bg-green-500/10 text-green-700 border-green-500/20" :
            ""
          }
        >
          {dataset.status === "pending_download" ? "Linked" :
           dataset.status === "pending" ? "Pending - Not Loaded" :
           dataset.status === "ready" ? "Ready" :
           dataset.status}
        </Badge>
      </div>

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Dataset Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Rows</p>
              <p className="text-2xl font-bold">{dataset.rowCount > 0 ? dataset.rowCount.toLocaleString() : "N/A"}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Columns</p>
              <p className="text-2xl font-bold">{dataset.columnCount > 0 ? dataset.columnCount : "N/A"}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Size</p>
              <p className="text-2xl font-bold">{formatFileSize(dataset.fileSize)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Source</p>
              <p className="text-2xl font-bold">{dataset.source || "Upload"}</p>
            </div>
          </div>

          {/* Inspect button for pending datasets */}
          {(dataset.status === "pending_download" && dataset.kaggleRef) && (
            <div className="mt-4 space-y-3">
              <Button onClick={handleInspect} disabled={inspecting || !kaggleConfigured}>
                {inspecting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Inspecting Dataset...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Download & Inspect Dataset
                  </>
                )}
              </Button>

              {checkingKaggle ? (
                <Card className="bg-accent/50 border-accent">
                  <CardContent className="pt-4">
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <p className="text-sm text-muted-foreground">Checking Kaggle API configuration...</p>
                    </div>
                  </CardContent>
                </Card>
              ) : kaggleConfigured ? (
                <Card className="bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
                  <CardContent className="pt-4">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                      <p className="text-sm font-medium text-green-700 dark:text-green-300">Kaggle API: Connected</p>
                    </div>
                    <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                      Ready to download and inspect datasets from Kaggle
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-accent/50 border-accent">
                  <CardContent className="pt-4">
                    <div className="space-y-2">
                      <h4 className="text-sm font-semibold flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        Kaggle API Setup Required
                      </h4>
                      <p className="text-xs text-muted-foreground">
                        To download and inspect this dataset, configure your Kaggle API credentials:
                      </p>
                      <ol className="text-xs text-muted-foreground space-y-1 ml-4 list-decimal">
                        <li>Go to <a href="https://www.kaggle.com/settings" target="_blank" rel="noopener noreferrer" className="underline text-primary">kaggle.com/settings</a></li>
                        <li>Click "Create New API Token" (downloads kaggle.json)</li>
                        <li>Add credentials to backend/.env file:
                          <pre className="mt-1 p-2 bg-background rounded text-xs">
KAGGLE_USERNAME=your_username{'\n'}
KAGGLE_KEY=your_key_here
                          </pre>
                        </li>
                        <li>Restart the backend server</li>
                      </ol>
                      <p className="text-xs text-muted-foreground pt-2">
                        See <a href="/KAGGLE_API_SETUP.md" className="underline text-primary">KAGGLE_API_SETUP.md</a> for detailed instructions.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Inspect button for HuggingFace pending datasets */}
          {dataset.status === "pending" && dataset.source === "huggingface" && (
            <div className="mt-4 space-y-3">
              <div className="p-4 bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    <svg className="h-5 w-5 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold text-yellow-800 dark:text-yellow-300">
                      Dataset Not Loaded
                    </h3>
                    <p className="text-sm text-yellow-700 dark:text-yellow-400 mt-1">
                      This HuggingFace dataset has been added but not yet loaded. Click the button below to load the dataset and view its schema and sample data.
                    </p>
                  </div>
                </div>
              </div>

              <Button onClick={handleInspect} disabled={inspecting} className="w-full">
                {inspecting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Loading Dataset from HuggingFace...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Inspect Dataset
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Target Column Selection */}
      {dataset.schema && dataset.schema.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Target Column
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Select the column you want to predict (target variable)
              </p>
              <div className="flex items-center gap-3">
                <Select value={selectedTarget} onValueChange={handleTargetColumnChange}>
                  <SelectTrigger className="w-[300px]">
                    <SelectValue placeholder="Select target column" />
                  </SelectTrigger>
                  <SelectContent>
                    {dataset.schema.map((col) => (
                      <SelectItem key={col.name} value={col.name}>
                        {col.name} ({col.dtype})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {dataset.targetColumn && selectedTarget === dataset.targetColumn && (
                  <Badge variant="secondary">
                    Auto-detected
                  </Badge>
                )}
                {dataset.targetColumn && selectedTarget !== dataset.targetColumn && (
                  <Badge variant="default">
                    Manually Selected
                  </Badge>
                )}
              </div>

              {/* Train Model Button */}
              <div className="pt-2 border-t">
                <Button
                  onClick={handleTrainModel}
                  disabled={training || !dataset.targetColumn || dataset.status !== "ready"}
                  size="lg"
                  className="w-full sm:w-auto"
                >
                  {training ? (
                    <>
                      <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      Starting Training...
                    </>
                  ) : (
                    <>
                      <Brain className="h-5 w-5 mr-2" />
                      Train Model with AutoML
                    </>
                  )}
                </Button>
                {dataset.targetColumn && dataset.status === "ready" ? (
                  <p className="text-xs text-muted-foreground mt-2">
                    Start automatic machine learning training with live progress in chat view
                  </p>
                ) : (
                  <div className="text-xs text-amber-600 dark:text-amber-400 mt-2 space-y-1">
                    {dataset.status !== "ready" && (
                      <p>⚠️ Dataset must be inspected first. Click 'Download & Inspect Dataset' above.</p>
                    )}
                    {!dataset.targetColumn && dataset.status === "ready" && (
                      <p>⚠️ Please select a target column first.</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Schema */}
      {dataset.schema && dataset.schema.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Table2 className="h-5 w-5" />
              Schema ({dataset.schema.length} columns)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-3 font-medium">Column</th>
                    <th className="text-left py-2 px-3 font-medium">Type</th>
                    <th className="text-right py-2 px-3 font-medium">Unique</th>
                    <th className="text-right py-2 px-3 font-medium">Nulls</th>
                  </tr>
                </thead>
                <tbody>
                  {dataset.schema.map((col, idx) => (
                    <tr key={idx} className="border-b hover:bg-accent/50">
                      <td className="py-2 px-3 font-medium">{col.name}</td>
                      <td className="py-2 px-3">
                        <Badge variant="outline">{col.dtype}</Badge>
                      </td>
                      <td className="py-2 px-3 text-right text-muted-foreground">
                        {col.uniqueCount !== undefined ? col.uniqueCount.toLocaleString() : "—"}
                      </td>
                      <td className="py-2 px-3 text-right text-muted-foreground">
                        {col.nullCount !== undefined ? col.nullCount.toLocaleString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sample Data */}
      {dataset.sampleData && dataset.sampleData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Table2 className="h-5 w-5" />
              Sample Data (first 20 rows)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    {dataset.schema?.map((col) => (
                      <th key={col.name} className="text-left py-2 px-3 font-medium whitespace-nowrap">
                        {col.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dataset.sampleData.map((row, idx) => (
                    <tr key={idx} className="border-b hover:bg-accent/50">
                      {dataset.schema?.map((col) => (
                        <td key={col.name} className="py-2 px-3 text-muted-foreground whitespace-nowrap">
                          {String(row[col.name]).substring(0, 50)}
                          {String(row[col.name]).length > 50 ? "..." : ""}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Processed Data Preview (First 5 Rows) */}
      {dataset.sampleData && dataset.sampleData.length > 0 && (
        <Card className="border-primary/20 bg-primary/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-primary">
              <Table2 className="h-5 w-5" />
              ✅ Processed data shows these 5 rows
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Preview of cleaned and processed data ready for model training
            </p>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-primary/20">
                    {dataset.schema?.map((col) => (
                      <th key={col.name} className="text-left py-2 px-3 font-medium whitespace-nowrap">
                        {col.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dataset.sampleData.slice(0, 5).map((row, idx) => (
                    <tr key={idx} className="border-b border-primary/10 hover:bg-primary/10">
                      {dataset.schema?.map((col) => (
                        <td key={col.name} className="py-2 px-3 text-muted-foreground whitespace-nowrap font-mono">
                          {row[col.name] === null || row[col.name] === undefined ? (
                            <span className="text-orange-500 italic">null</span>
                          ) : (
                            <>
                              {String(row[col.name]).substring(0, 30)}
                              {String(row[col.name]).length > 30 ? "..." : ""}
                            </>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
