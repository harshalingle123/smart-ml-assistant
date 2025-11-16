import { DatasetCard } from "@/components/DatasetCard";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Upload, Loader2, RefreshCw, X } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { getDatasets, uploadDataset, deleteDataset } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useLocation } from "wouter";

interface Dataset {
  id: string;
  name: string;
  fileName?: string;
  description?: string;
  size?: string;
  rowCount?: number;
  columnCount?: number;
  fileSize?: number;
  format?: string;
  status?: string;
  uploadedAt?: string;
  previewData?: any;
  source?: string;
  kaggleRef?: string;
  huggingfaceDatasetId?: string;
  huggingfaceUrl?: string;
  downloadPath?: string;
  schema?: any;
  sampleData?: any;
  targetColumn?: string;
  [key: string]: any;
}

export default function Datasets() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadingFileName, setUploadingFileName] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const [location] = useLocation();

  // Load datasets on mount and when navigating to this page
  useEffect(() => {
    if (location === "/datasets") {
      console.log("Navigated to Datasets - loading datasets...");
      loadDatasets();
    }
  }, [location]);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      console.log("[Datasets] Fetching datasets from API...");
      const response = await getDatasets();
      console.log("[Datasets] Raw API Response:", response);
      console.log("[Datasets] Response type:", typeof response);
      console.log("[Datasets] Is Array:", Array.isArray(response));

      // Backend returns array directly, not { datasets: [] }
      const datasetsList = Array.isArray(response) ? response : (response.datasets || []);
      console.log("[Datasets] Dataset list length:", datasetsList.length);
      console.log("[Datasets] Dataset list:", datasetsList);

      // Map _id to id if needed, and ensure all ObjectId fields are converted to strings
      const mappedDatasets = datasetsList.map((ds: any, index: number) => {
        console.log(`[Datasets] Processing dataset ${index}:`, ds);

        // Convert ObjectId to string for id field
        const id = typeof ds.id === 'string' ? ds.id :
                   (ds._id && typeof ds._id === 'object' && '$oid' in ds._id) ? ds._id.$oid :
                   ds._id?.toString() || ds.id?.toString() || '';

        const mapped = {
          ...ds,
          id,
          _id: undefined, // Remove _id to avoid confusion
        };

        console.log(`[Datasets] Mapped dataset ${index}:`, mapped);
        return mapped;
      });

      console.log("[Datasets] Total loaded datasets:", mappedDatasets.length);
      if (mappedDatasets.length > 0) {
        console.log("[Datasets] First dataset details:", {
          id: mappedDatasets[0].id,
          name: mappedDatasets[0].name,
          status: mappedDatasets[0].status,
          source: mappedDatasets[0].source,
          kaggleRef: mappedDatasets[0].kaggleRef,
          rowCount: mappedDatasets[0].rowCount,
          columnCount: mappedDatasets[0].columnCount,
        });
      }

      setDatasets(mappedDatasets);
    } catch (error) {
      console.error("[Datasets] Failed to load datasets:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to load datasets";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (id: string) => {
    toast({
      title: "Download Started",
      description: "Your dataset download will begin shortly",
    });
    // In production, implement actual download logic
    console.log("Download dataset:", id);
  };

  const handleDelete = async (id: string) => {
    try {
      console.log("Deleting dataset with ID:", id);
      await deleteDataset(id);
      toast({
        title: "Success",
        description: "Dataset deleted successfully",
      });
      // Reload datasets
      await loadDatasets();
    } catch (error) {
      console.error("Failed to delete dataset:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to delete dataset";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      console.log("[Upload] No file selected");
      return;
    }

    console.log("\n" + "=".repeat(80));
    console.log("[Upload] File selected:", file.name);
    console.log("[Upload] File size:", (file.size / (1024 * 1024)).toFixed(2), "MB");
    console.log("[Upload] File type:", file.type);
    console.log("=".repeat(80) + "\n");

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      console.error("[Upload] Invalid file type - not a CSV");
      toast({
        title: "Invalid File",
        description: "Please upload a CSV file",
        variant: "destructive",
      });
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      setUploadingFileName(file.name);
      console.log("[Upload] ✓ Starting upload process...");

      const formData = new FormData();
      formData.append('file', file);
      console.log("[Upload] ✓ FormData created");

      const result = await uploadDataset(formData, (progress) => {
        setUploadProgress(progress);
      });

      console.log("\n" + "=".repeat(80));
      console.log("[Upload] ✓✓✓ UPLOAD SUCCESSFUL ✓✓✓");
      console.log("[Upload] Result:", result);
      console.log("=".repeat(80) + "\n");

      toast({
        title: "Success",
        description: `Dataset "${file.name}" uploaded successfully`,
      });

      // Reload datasets
      console.log("[Upload] Reloading datasets...");
      await loadDatasets();
      console.log("[Upload] ✓ Datasets reloaded");

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error("\n" + "!".repeat(80));
      console.error("[Upload] ❌ UPLOAD FAILED ❌");
      console.error("[Upload] Error object:", error);
      console.error("[Upload] Error type:", error instanceof Error ? error.constructor.name : typeof error);
      if (error instanceof Error) {
        console.error("[Upload] Error message:", error.message);
        console.error("[Upload] Error stack:", error.stack);
      }
      console.error("!".repeat(80) + "\n");

      const errorMessage = error instanceof Error ? error.message : "Failed to upload dataset. Please try again.";
      toast({
        title: "Upload Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setUploading(false);
      setUploadProgress(0);
      setUploadingFileName("");
      console.log("[Upload] Upload process completed (cleaning up state)");
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Datasets</h1>
          <p className="text-muted-foreground mt-1">
            Manage your uploaded datasets for training and analysis
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={loadDatasets}
            disabled={loading}
            title="Refresh datasets"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="hidden"
          />
          <Button
            onClick={handleUploadClick}
            data-testid="button-upload-dataset"
            disabled={uploading}
          >
            {uploading ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-1" />
                Upload Dataset
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Upload Progress Indicator */}
      {uploading && (
        <div className="bg-card border rounded-lg p-4 space-y-3 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                <Upload className="h-5 w-5 text-primary animate-pulse" />
              </div>
              <div>
                <p className="font-medium">Uploading Dataset</p>
                <p className="text-sm text-muted-foreground">{uploadingFileName}</p>
              </div>
            </div>
            <span className="text-sm font-medium text-primary">
              {Math.round(uploadProgress)}%
            </span>
          </div>
          <Progress value={uploadProgress} className="h-2" />
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : datasets.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 border-2 border-dashed rounded-lg">
          <Upload className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No datasets yet</h3>
          <p className="text-muted-foreground mb-4">Upload a CSV file or add from Kaggle/HuggingFace</p>
          <Button onClick={handleUploadClick}>
            <Upload className="h-4 w-4 mr-1" />
            Upload Your First Dataset
          </Button>
        </div>
      ) : (
        <div>
          <div className="mb-4 text-sm text-muted-foreground">
            Showing {datasets.length} dataset{datasets.length !== 1 ? 's' : ''}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {datasets.map((dataset, index) => {
              console.log(`[Datasets Render] Rendering dataset ${index}:`, dataset.id, dataset.name);
              return (
                <DatasetCard
                  key={dataset.id || `dataset-${index}`}
                  dataset={dataset}
                  onDownload={handleDownload}
                  onDelete={handleDelete}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
