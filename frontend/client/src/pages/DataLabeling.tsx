import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { AlertCircle, ArrowLeft, Loader2, Tag, Sparkles } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { FileUploadZone } from "@/components/labeling/FileUploadZone";
import { ConfigurationModal } from "@/components/labeling/ConfigurationModal";
import { ResultsViewer } from "@/components/labeling/ResultsViewer";
import { ExportControls } from "@/components/labeling/ExportControls";
import { generateLabels } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import {
  LabelingConfig,
  LabelingResponse,
  LabelingResult,
  getSupportedFileTypes,
} from "@/lib/labeling-types";

type Step = "upload" | "configure" | "processing" | "results";

export default function DataLabeling() {
  const { toast } = useToast();
  const [step, setStep] = useState<Step>("upload");
  const [files, setFiles] = useState<File[]>([]);
  const [config, setConfig] = useState<LabelingConfig | null>(null);
  const [results, setResults] = useState<LabelingResult[]>([]);
  const [taskType, setTaskType] = useState<string>("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);

  const handleFilesChange = (newFiles: File[]) => {
    setFiles(newFiles);
    setError(null);
  };

  const handleConfigure = () => {
    if (files.length === 0) {
      toast({
        title: "No Files Selected",
        description: "Please upload at least one file to label",
        variant: "destructive",
      });
      return;
    }
    setShowConfigModal(true);
  };

  const handleConfigSubmit = async (configuration: LabelingConfig) => {
    setConfig(configuration);
    setTaskType(configuration.task_type);
    setShowConfigModal(false);
    setStep("processing");
    setIsProcessing(true);
    setError(null);
    setUploadProgress(0);

    try {
      const response: LabelingResponse = await generateLabels(
        files,
        configuration,
        (progress) => {
          setUploadProgress(progress);
        }
      );

      setResults(response.results);
      setTaskType(response.task_type);
      setStep("results");

      toast({
        title: "Labeling Complete",
        description: `Successfully labeled ${response.success_count} of ${response.total_processed} files`,
      });

      if (response.error_count && response.error_count > 0) {
        toast({
          title: "Some Errors Occurred",
          description: `${response.error_count} file(s) could not be labeled`,
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Labeling error:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
      setStep("upload");

      toast({
        title: "Labeling Failed",
        description: error instanceof Error ? error.message : "An unknown error occurred",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
      setUploadProgress(0);
    }
  };

  const handleStartOver = () => {
    setStep("upload");
    setFiles([]);
    setConfig(null);
    setResults([]);
    setTaskType("");
    setError(null);
    setUploadProgress(0);
  };

  const handleEditLabel = (index: number, updatedLabel: string) => {
    const updatedResults = [...results];
    const result = updatedResults[index];

    // Update the label based on result type
    if ("classification" in result && result.classification !== undefined) {
      updatedResults[index] = { ...result, classification: updatedLabel };
    } else if ("label" in result) {
      updatedResults[index] = { ...result, label: updatedLabel };
    }

    setResults(updatedResults);

    toast({
      title: "Label Updated",
      description: "Label has been updated successfully",
    });
  };

  const getAcceptedFileTypes = () => {
    if (!config) return undefined;
    return getSupportedFileTypes(config.task_type);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-primary/10">
            <Tag className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-3xl font-bold">Data Labeling</h1>
        </div>
        <p className="text-muted-foreground">
          Use AI to automatically label your images, text, audio, and video files
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Step: Upload */}
      {step === "upload" && (
        <div className="space-y-6">
          <FileUploadZone
            files={files}
            onFilesChange={handleFilesChange}
            accept={getAcceptedFileTypes()}
            maxFiles={100}
          />

          {files.length > 0 && (
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setFiles([])}>
                Clear All
              </Button>
              <Button onClick={handleConfigure} className="gap-2">
                <Sparkles className="h-4 w-4" />
                Configure & Label
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Step: Processing */}
      {step === "processing" && (
        <div className="max-w-2xl mx-auto">
          <div className="space-y-6 py-12">
            <div className="text-center">
              <Loader2 className="h-16 w-16 mx-auto mb-4 animate-spin text-primary" />
              <h2 className="text-2xl font-semibold mb-2">Processing Files...</h2>
              <p className="text-muted-foreground">
                AI is analyzing and labeling your {files.length} file{files.length !== 1 ? "s" : ""}
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Upload Progress</span>
                <span>{Math.round(uploadProgress)}%</span>
              </div>
              <Progress value={uploadProgress} className="h-2" />
            </div>

            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                This may take a few moments depending on the number of files...
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Step: Results */}
      {step === "results" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <Button variant="outline" onClick={handleStartOver} className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Start Over
            </Button>
          </div>

          <ExportControls results={results} taskType={taskType} />

          <ResultsViewer
            results={results}
            taskType={taskType}
            onEditLabel={handleEditLabel}
          />
        </div>
      )}

      {/* Configuration Modal */}
      <ConfigurationModal
        open={showConfigModal}
        onClose={() => setShowConfigModal(false)}
        onSubmit={handleConfigSubmit}
        fileCount={files.length}
        files={files}
      />
    </div>
  );
}
