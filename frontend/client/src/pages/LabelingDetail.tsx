import { useState, useEffect } from "react";
import { useRoute, useLocation } from "wouter";
import {
  ArrowLeft,
  Upload,
  Play,
  Download,
  FileText,
  Image as ImageIcon,
  Video,
  Music,
  FileIcon,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
} from "lucide-react";
import {
  getLabelingDataset,
  uploadLabelingFiles,
  analyzeLabelingFiles,
  exportLabelingDataset,
  deleteLabelingFile,
} from "../lib/api";
import { LabelingDatasetDetail, LabelingFile, MediaType } from "../types/labeling";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { useToast } from "../hooks/use-toast";
import { Progress } from "../components/ui/progress";

export default function LabelingDetail() {
  const [, params] = useRoute("/labeling/:id");
  const [, setLocation] = useLocation();
  const [dataset, setDataset] = useState<LabelingDatasetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [selectedFile, setSelectedFile] = useState<LabelingFile | null>(null);
  const { toast } = useToast();

  const loadDataset = async () => {
    if (!params?.id) return;

    try {
      setLoading(true);
      const data = await getLabelingDataset(params.id);
      setDataset(data);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDataset();
  }, [params?.id]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !dataset) return;

    try {
      setUploading(true);
      const fileArray = Array.from(files);
      await uploadLabelingFiles(dataset.id, fileArray);
      toast({
        title: "Success",
        description: `Uploaded ${fileArray.length} file(s)`,
      });
      loadDataset();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyzeAll = async () => {
    if (!dataset) return;

    const pendingFiles = dataset.files.filter((f) => f.status === "pending");
    if (pendingFiles.length === 0) {
      toast({
        title: "No files to analyze",
        description: "All files have been processed",
      });
      return;
    }

    try {
      setAnalyzing(true);
      await analyzeLabelingFiles(pendingFiles.map((f) => f.id));
      toast({
        title: "Processing started",
        description: `Analyzing ${pendingFiles.length} file(s)`,
      });

      // Poll for updates
      const interval = setInterval(() => {
        loadDataset();
      }, 3000);

      setTimeout(() => {
        clearInterval(interval);
        setAnalyzing(false);
      }, 30000);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
      setAnalyzing(false);
    }
  };

  const handleExport = async (format: "json" | "csv" | "zip") => {
    if (!dataset) return;

    try {
      await exportLabelingDataset(dataset.id, format);
      toast({
        title: "Success",
        description: `Dataset exported as ${format.toUpperCase()}`,
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  const getMediaIcon = (mediaType: MediaType) => {
    switch (mediaType) {
      case MediaType.IMAGE:
        return <ImageIcon className="w-4 h-4" />;
      case MediaType.VIDEO:
        return <Video className="w-4 h-4" />;
      case MediaType.AUDIO:
        return <Music className="w-4 h-4" />;
      case MediaType.TEXT:
        return <FileText className="w-4 h-4" />;
      case MediaType.PDF:
        return <FileIcon className="w-4 h-4" />;
      default:
        return <FileIcon className="w-4 h-4" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge className="bg-green-500"><CheckCircle2 className="w-3 h-3 mr-1" />Completed</Badge>;
      case "failed":
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />Failed</Badge>;
      case "processing":
        return <Badge className="bg-blue-500"><Loader2 className="w-3 h-3 mr-1 animate-spin" />Processing</Badge>;
      default:
        return <Badge variant="secondary"><Clock className="w-3 h-3 mr-1" />Pending</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="container mx-auto p-6">
        <p>Dataset not found</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <Button variant="ghost" onClick={() => setLocation("/labeling")} className="mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Datasets
        </Button>

        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold">{dataset.name}</h1>
            <p className="text-muted-foreground mt-1">{dataset.task}</p>
          </div>

          <div className="flex gap-2">
            <input
              type="file"
              multiple
              accept="image/*,video/*,audio/*,.pdf,.txt,.csv,.json"
              onChange={handleFileUpload}
              className="hidden"
              id="file-upload"
              disabled={uploading}
            />
            <Button variant="outline" onClick={() => document.getElementById("file-upload")?.click()} disabled={uploading}>
              {uploading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
              Upload Files
            </Button>
            <Button onClick={handleAnalyzeAll} disabled={analyzing}>
              {analyzing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
              Analyze All
            </Button>
            <Button variant="outline" onClick={() => handleExport("json")}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mt-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Total Files</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dataset.total_files}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">{dataset.completed_files}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Failed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-destructive">{dataset.failed_files}</div>
            </CardContent>
          </Card>
        </div>

        {dataset.total_files > 0 && (
          <div className="mt-4">
            <Progress value={(dataset.completed_files / dataset.total_files) * 100} className="h-2" />
            <p className="text-sm text-muted-foreground mt-2">
              {Math.round((dataset.completed_files / dataset.total_files) * 100)}% complete
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Files ({dataset.files.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {dataset.files.length === 0 ? (
                  <p className="text-center text-muted-foreground py-8">
                    No files uploaded yet. Click "Upload Files" to get started.
                  </p>
                ) : (
                  dataset.files.map((file) => (
                    <div
                      key={file.id}
                      className={`p-3 border rounded-lg cursor-pointer hover:bg-accent transition-colors ${
                        selectedFile?.id === file.id ? "bg-accent" : ""
                      }`}
                      onClick={() => setSelectedFile(file)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          {getMediaIcon(file.media_type as MediaType)}
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{file.original_name}</p>
                            <p className="text-xs text-muted-foreground">
                              {(file.file_size / 1024).toFixed(1)} KB
                            </p>
                          </div>
                        </div>
                        {getStatusBadge(file.status)}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle>Results</CardTitle>
              <CardDescription>
                {selectedFile ? selectedFile.original_name : "Select a file to view results"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!selectedFile ? (
                <p className="text-center text-muted-foreground py-8">
                  Select a file from the list to view its labeling results
                </p>
              ) : !selectedFile.result ? (
                <p className="text-center text-muted-foreground py-8">
                  {selectedFile.status === "failed"
                    ? `Error: ${selectedFile.error_message || "Unknown error"}`
                    : selectedFile.status === "processing"
                    ? "Processing..."
                    : "Not yet analyzed"}
                </p>
              ) : (
                <div className="space-y-4">
                  {selectedFile.result.summary && (
                    <div>
                      <h4 className="font-semibold mb-1">Summary</h4>
                      <p className="text-sm text-muted-foreground">{selectedFile.result.summary}</p>
                    </div>
                  )}

                  {selectedFile.result.sentiment && (
                    <div>
                      <h4 className="font-semibold mb-1">Sentiment</h4>
                      <Badge>{selectedFile.result.sentiment}</Badge>
                    </div>
                  )}

                  {selectedFile.result.topics && selectedFile.result.topics.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2">Topics</h4>
                      <div className="flex flex-wrap gap-1">
                        {selectedFile.result.topics.map((topic, i) => (
                          <Badge key={i} variant="secondary">
                            {topic}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedFile.result.entities && selectedFile.result.entities.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2">Entities</h4>
                      <div className="space-y-1">
                        {selectedFile.result.entities.map((entity, i) => (
                          <div key={i} className="text-sm flex justify-between">
                            <span>{entity.name}</span>
                            <Badge variant="outline" className="text-xs">
                              {entity.type}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedFile.result.objects && selectedFile.result.objects.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2">Objects Detected</h4>
                      <div className="space-y-2">
                        {selectedFile.result.objects.map((obj, i) => (
                          <div key={i} className="text-sm border rounded p-2">
                            <div className="flex justify-between items-center">
                              <span className="font-medium">{obj.label}</span>
                              <Badge variant="secondary">
                                {Math.round(obj.confidence * 100)}%
                              </Badge>
                            </div>
                            {obj.location && (
                              <p className="text-xs text-muted-foreground mt-1">{obj.location}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedFile.result.safety_flags && selectedFile.result.safety_flags.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2">Safety Flags</h4>
                      <div className="flex flex-wrap gap-1">
                        {selectedFile.result.safety_flags.map((flag, i) => (
                          <Badge key={i} variant="destructive">
                            {flag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
