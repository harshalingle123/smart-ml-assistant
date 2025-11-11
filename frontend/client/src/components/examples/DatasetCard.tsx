import { DatasetCard } from "../DatasetCard";

export default function DatasetCardExample() {
  const dataset = {
    id: "1",
    userId: "1",
    name: "customer_feedback.csv",
    fileName: "customer_feedback.csv",
    rowCount: 5420,
    columnCount: 4,
    fileSize: 524288,
    status: "ready",
    previewData: [
      { id: 1, text: "Great product!", sentiment: "positive", timestamp: "2025-01-15" },
      { id: 2, text: "Not satisfied", sentiment: "negative", timestamp: "2025-01-16" },
    ],
    uploadedAt: new Date("2025-11-01T12:00:00"),
  };

  return (
    <div className="p-6 max-w-md">
      <DatasetCard
        dataset={dataset}
        onDownload={(id) => console.log("Download dataset:", id)}
        onDelete={(id) => console.log("Delete dataset:", id)}
      />
    </div>
  );
}
