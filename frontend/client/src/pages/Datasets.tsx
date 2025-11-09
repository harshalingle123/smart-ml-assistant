import { DatasetCard } from "@/components/DatasetCard";
import { MOCK_DATASETS } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import { Upload } from "lucide-react";

export default function Datasets() {
  const handleDownload = (id: string) => {
    console.log("Download dataset:", id);
  };

  const handleDelete = (id: string) => {
    console.log("Delete dataset:", id);
  };

  const handleUpload = () => {
    console.log("Upload new dataset");
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
        <Button onClick={handleUpload} data-testid="button-upload-dataset">
          <Upload className="h-4 w-4 mr-1" />
          Upload Dataset
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {MOCK_DATASETS.map((dataset) => (
          <DatasetCard
            key={dataset.id}
            dataset={dataset}
            onDownload={handleDownload}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  );
}
