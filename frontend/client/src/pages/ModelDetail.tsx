import { useEffect, useState } from "react";
import { useParams, useLocation } from "wouter";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Download, Play, Trash2, ArrowLeft, Code } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { getModel, downloadModel, predictWithModel, deleteModel, getModelSampleData } from "@/lib/api";

interface Model {
  _id: string;
  userId: string;
  name: string;
  baseModel: string;
  version: string;
  accuracy: string;
  f1Score: string;
  loss: string;
  status: string;
  datasetId?: string;
  taskType?: string;
  metrics?: Record<string, any>;
  createdAt: string;
}

interface SampleData {
  input: Record<string, any>;
  actual_target: any;
  target_column: string;
}

export default function ModelDetail() {
  const { id } = useParams();
  const [, setLocation] = useLocation();
  const [model, setModel] = useState<Model | null>(null);
  const [loading, setLoading] = useState(true);
  const [testInput, setTestInput] = useState("{}");
  const [predicting, setPredicting] = useState(false);
  const [prediction, setPrediction] = useState<any>(null);
  const [sampleData, setSampleData] = useState<SampleData[]>([]);
  const [currentSampleIndex, setCurrentSampleIndex] = useState(0);
  const [loadingSamples, setLoadingSamples] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (id) {
      loadModel();
      loadSampleData();
    }
  }, [id]);

  const loadModel = async () => {
    try {
      setLoading(true);
      const data = await getModel(id!);
      setModel(data);
    } catch (error) {
      console.error("Failed to load model:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to load model",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadSampleData = async () => {
    try {
      setLoadingSamples(true);
      const data = await getModelSampleData(id!, 3);
      console.log("✅ Sample data loaded successfully:", data);
      setSampleData(data.samples || []);
      setCurrentSampleIndex(0);
    } catch (error) {
      console.error("❌ Failed to load sample data:", error);
      console.error("Error details:", error instanceof Error ? error.message : String(error));
      // Don't show error toast for sample data - it's optional
      setSampleData([]);
    } finally {
      setLoadingSamples(false);
    }
  };

  const loadDynamicExample = (index: number) => {
    if (sampleData.length > 0 && index >= 0 && index < sampleData.length) {
      const sample = sampleData[index];
      setTestInput(JSON.stringify(sample.input, null, 2));
      setCurrentSampleIndex(index);
    }
  };

  const handleDownload = async () => {
    if (!model) return;

    try {
      toast({
        title: "Download Started",
        description: "Preparing model for download...",
      });

      await downloadModel(model._id);

      toast({
        title: "Download Complete",
        description: "Model metadata downloaded successfully",
      });
    } catch (error) {
      console.error("Failed to download model:", error);
      toast({
        title: "Download Failed",
        description: error instanceof Error ? error.message : "Failed to download model",
        variant: "destructive",
      });
    }
  };

  const handleTestModel = async () => {
    if (!model) return;

    try {
      setPredicting(true);
      const inputData = JSON.parse(testInput);
      const result = await predictWithModel(model._id, inputData);
      setPrediction(result);

      toast({
        title: "Prediction Complete",
        description: "Model inference completed successfully",
      });
    } catch (error) {
      console.error("Failed to test model:", error);
      toast({
        title: "Prediction Failed",
        description: error instanceof Error ? error.message : "Failed to run prediction",
        variant: "destructive",
      });
    } finally {
      setPredicting(false);
    }
  };

  const handleDelete = async () => {
    if (!model) return;

    if (!confirm(`Are you sure you want to delete "${model.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await deleteModel(model._id);

      toast({
        title: "Model Deleted",
        description: "Model has been permanently deleted",
      });

      setLocation("/models");
    } catch (error) {
      console.error("Failed to delete model:", error);
      toast({
        title: "Delete Failed",
        description: error instanceof Error ? error.message : "Failed to delete model",
        variant: "destructive",
      });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ready":
        return "bg-green-500/10 text-green-500 border-green-500/20";
      case "training":
        return "bg-blue-500/10 text-blue-500 border-blue-500/20";
      case "failed":
        return "bg-red-500/10 text-red-500 border-red-500/20";
      default:
        return "bg-gray-500/10 text-gray-500 border-gray-500/20";
    }
  };

  const formatBytes = (bytes: number) => {
    if (!bytes) return "N/A";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading model...</p>
        </div>
      </div>
    );
  }

  if (!model) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="sm" onClick={() => setLocation("/models")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Models
          </Button>
        </div>
        <Card className="p-8 text-center">
          <p className="text-muted-foreground">Model not found</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => setLocation("/models")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-semibold">{model.name}</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Created {new Date(model.createdAt).toLocaleDateString()}
            </p>
          </div>
        </div>
        <Badge className={getStatusColor(model.status)}>{model.status}</Badge>
      </div>

      {/* Model Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-muted-foreground mb-1">Model ID</div>
          <div className="font-mono text-sm truncate">{model._id}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground mb-1">Base Model</div>
          <div className="font-semibold">{model.baseModel}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground mb-1">Version</div>
          <div className="font-semibold">{model.version}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground mb-1">Task Type</div>
          <div className="font-semibold capitalize">{model.taskType || "Unknown"}</div>
        </Card>
      </div>

      {/* Metrics */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Performance Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {model.taskType === "classification" ? (
            <>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Accuracy</div>
                <div className="text-2xl font-bold">{model.accuracy}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">F1 Score</div>
                <div className="text-2xl font-bold">{model.f1Score}</div>
              </div>
              {model.metrics?.precision && (
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Precision</div>
                  <div className="text-2xl font-bold">{model.metrics.precision.toFixed(3)}</div>
                </div>
              )}
              {model.metrics?.recall && (
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Recall</div>
                  <div className="text-2xl font-bold">{model.metrics.recall.toFixed(3)}</div>
                </div>
              )}
            </>
          ) : (
            <>
              {model.metrics?.r2_score && (
                <div>
                  <div className="text-sm text-muted-foreground mb-1">R² Score</div>
                  <div className="text-2xl font-bold">{model.metrics.r2_score.toFixed(3)}</div>
                </div>
              )}
              {model.metrics?.mae && (
                <div>
                  <div className="text-sm text-muted-foreground mb-1">MAE</div>
                  <div className="text-2xl font-bold">{model.metrics.mae.toLocaleString()}</div>
                </div>
              )}
              {model.metrics?.rmse && (
                <div>
                  <div className="text-sm text-muted-foreground mb-1">RMSE</div>
                  <div className="text-2xl font-bold">{model.metrics.rmse.toLocaleString()}</div>
                </div>
              )}
            </>
          )}
        </div>
      </Card>

      {/* Actions */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Actions</h2>
        <div className="flex gap-3">
          <Button onClick={handleDownload}>
            <Download className="h-4 w-4 mr-2" />
            Download Model
          </Button>
          <Button variant="outline" onClick={() => toast({ title: "Coming Soon", description: "Deployment feature is under development" })}>
            <Code className="h-4 w-4 mr-2" />
            Deploy Model
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="h-4 w-4 mr-2" />
            Delete Model
          </Button>
        </div>
      </Card>

      {/* Test Model */}
      {model.status === "ready" && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Test Model</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Run predictions using your trained model. Enter sample data in JSON format to see how the model performs.
          </p>

          {/* Dynamic Example Templates */}
          <div className="mb-4">
            <label className="text-sm font-semibold mb-2 block">
              Quick Examples {sampleData.length > 0 && `(from actual training data)`}:
            </label>
            {loadingSamples ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading examples...
              </div>
            ) : sampleData.length > 0 ? (
              <div className="flex gap-2 flex-wrap">
                {sampleData.map((sample, index) => (
                  <Button
                    key={index}
                    variant={currentSampleIndex === index ? "default" : "outline"}
                    size="sm"
                    onClick={() => loadDynamicExample(index)}
                  >
                    Example {index + 1}
                    {sample.actual_target !== null && sample.actual_target !== undefined && (
                      <span className="ml-1 text-xs opacity-70">
                        (Target: {typeof sample.actual_target === 'number'
                          ? sample.actual_target.toLocaleString()
                          : sample.actual_target})
                      </span>
                    )}
                  </Button>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setTestInput("{}")}
                >
                  Clear
                </Button>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground mb-2">
                No sample data available. Enter your own JSON below.
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Input Data (JSON)</label>
              <textarea
                className="w-full h-40 p-3 border rounded-lg font-mono text-sm bg-background resize-y"
                value={testInput}
                onChange={(e) => setTestInput(e.target.value)}
                placeholder='{"feature1": 123, "feature2": "value", "feature3": true}'
              />
              <p className="text-xs text-muted-foreground mt-1">
                💡 Tip: Use the example buttons above or enter your own JSON data
              </p>
            </div>
            <Button onClick={handleTestModel} disabled={predicting}>
              {predicting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Run Prediction
                </>
              )}
            </Button>

            {prediction && (
              <div className="mt-4 space-y-3">
                <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
                      <h3 className="font-semibold text-green-700 dark:text-green-400">Prediction Complete</h3>
                    </div>
                    {prediction.uses_real_model && (
                      <Badge variant="outline" className="bg-blue-500/10 text-blue-600 border-blue-500/20">
                        Real AutoGluon Model
                      </Badge>
                    )}
                    {prediction.uses_real_model === false && (
                      <Badge variant="outline" className="bg-amber-500/10 text-amber-600 border-amber-500/20">
                        Simulated
                      </Badge>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Predicted Value</p>
                      <p className="text-2xl font-bold">
                        {typeof prediction.prediction === 'number'
                          ? prediction.prediction.toLocaleString()
                          : prediction.prediction}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Confidence</p>
                      <p className="text-2xl font-bold">
                        {(prediction.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  {prediction.probabilities && (
                    <div className="mt-4">
                      <p className="text-xs text-muted-foreground mb-2">Class Probabilities:</p>
                      <div className="space-y-2">
                        {Object.entries(prediction.probabilities).map(([className, prob]: [string, any]) => (
                          <div key={className} className="flex items-center gap-2">
                            <span className="text-sm font-medium min-w-24">{className}:</span>
                            <div className="flex-1 bg-muted rounded-full h-2 overflow-hidden">
                              <div
                                className="bg-primary h-full transition-all"
                                style={{ width: `${prob * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-sm text-muted-foreground">{(prob * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {prediction.prediction_interval && (
                    <div className="mt-4">
                      <p className="text-xs text-muted-foreground mb-2">Prediction Interval (95%):</p>
                      <div className="flex items-center gap-2 text-sm">
                        <span className="font-mono">{prediction.prediction_interval.lower.toLocaleString()}</span>
                        <span className="text-muted-foreground">to</span>
                        <span className="font-mono">{prediction.prediction_interval.upper.toLocaleString()}</span>
                      </div>
                    </div>
                  )}

                  {/* Show actual target value when using dynamic examples */}
                  {sampleData.length > 0 && sampleData[currentSampleIndex]?.actual_target !== null &&
                   sampleData[currentSampleIndex]?.actual_target !== undefined && (
                    <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded">
                      <p className="text-xs text-muted-foreground mb-1">Actual Value (from training data)</p>
                      <div className="flex items-center gap-3">
                        <p className="text-lg font-bold text-blue-600">
                          {typeof sampleData[currentSampleIndex].actual_target === 'number'
                            ? sampleData[currentSampleIndex].actual_target.toLocaleString()
                            : sampleData[currentSampleIndex].actual_target}
                        </p>
                        {typeof prediction.prediction === 'number' &&
                         typeof sampleData[currentSampleIndex].actual_target === 'number' && (
                          <span className="text-xs text-muted-foreground">
                            (Error: {Math.abs(prediction.prediction - sampleData[currentSampleIndex].actual_target).toLocaleString()})
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <details className="p-4 bg-muted rounded-lg">
                  <summary className="cursor-pointer text-sm font-medium">Show Full Response</summary>
                  <pre className="mt-3 text-xs overflow-auto">{JSON.stringify(prediction, null, 2)}</pre>
                </details>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Full Model Metadata (for debugging/advanced users) */}
      <Card className="p-6">
        <details>
          <summary className="cursor-pointer font-semibold mb-2">Show Raw Metadata</summary>
          <pre className="mt-4 p-4 bg-muted rounded-lg text-xs overflow-auto">
            {JSON.stringify(model, null, 2)}
          </pre>
        </details>
      </Card>
    </div>
  );
}
