import { ModelCard } from "../ModelCard";

export default function ModelCardExample() {
  const model = {
    id: "1",
    userId: "1",
    name: "bert-user-v3.1",
    baseModel: "bert-base-uncased",
    version: "3.1",
    accuracy: "95.2%",
    f1Score: "0.94",
    loss: "0.12",
    status: "ready",
    datasetId: "1",
    createdAt: new Date("2025-11-03T14:00:00"),
  };

  return (
    <div className="p-6 max-w-md">
      <ModelCard
        model={model}
        onDownload={(id) => console.log("Download model:", id)}
        onGenerateAPI={(id) => console.log("Generate API for:", id)}
        onDelete={(id) => console.log("Delete model:", id)}
      />
    </div>
  );
}
