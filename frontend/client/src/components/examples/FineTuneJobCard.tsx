import { FineTuneJobCard } from "../FineTuneJobCard";

export default function FineTuneJobCardExample() {
  const jobInProgress = {
    id: "1",
    userId: "1",
    modelId: null,
    datasetId: "1",
    baseModel: "bert-base-uncased",
    status: "training",
    progress: 67,
    currentStep: "Training - Epoch 7/10",
    logs: "Loss: 0.245, Accuracy: 91.3%",
    createdAt: new Date("2025-11-05T10:00:00"),
    completedAt: null,
  };

  const jobCompleted = {
    id: "2",
    userId: "1",
    modelId: "1",
    datasetId: "1",
    baseModel: "distilbert-base-uncased",
    status: "completed",
    progress: 100,
    currentStep: "Deployed",
    logs: "Training completed successfully",
    createdAt: new Date("2025-11-03T13:00:00"),
    completedAt: new Date("2025-11-03T14:00:00"),
  };

  return (
    <div className="grid gap-6 p-6 max-w-2xl">
      <FineTuneJobCard job={jobInProgress} />
      <FineTuneJobCard job={jobCompleted} />
    </div>
  );
}
