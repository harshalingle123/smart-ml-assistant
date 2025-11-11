export const MOCK_USER = {
  id: "1",
  username: "demo@mlassistant.com",
  password: "",
  currentPlan: "pro",
  queriesUsed: 432,
  fineTuneJobs: 3,
  datasetsCount: 2,
  billingCycle: "2025-11",
};

export const PLAN_LIMITS = {
  free: { queries: 100, fineTunes: 1, datasets: 1 },
  pro: { queries: 1000, fineTunes: 5, datasets: 5 },
  enterprise: { queries: Infinity, fineTunes: Infinity, datasets: Infinity },
};

export const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "/month",
    features: [
      "100 queries per month",
      "1 fine-tune job",
      "1 dataset",
      "Basic model library",
      "Community support",
    ],
    id: "free",
  },
  {
    name: "Pro",
    price: "$9.99",
    period: "/month",
    features: [
      "1,000 queries per month",
      "5 fine-tune jobs",
      "5 datasets",
      "Advanced models",
      "Priority support",
      "API access",
    ],
    id: "pro",
    popular: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    features: [
      "Unlimited queries",
      "Unlimited fine-tuning",
      "Unlimited datasets",
      "Custom models",
      "Dedicated support",
      "SLA guarantee",
    ],
    id: "enterprise",
  },
];

export const MOCK_CHATS = [
  {
    id: "1",
    userId: "1",
    title: "Sentiment Analysis Project",
    modelId: "1",
    datasetId: "1",
    lastUpdated: new Date("2025-11-05T10:30:00"),
  },
  {
    id: "2",
    userId: "1",
    title: "Customer Feedback Classification",
    modelId: null,
    datasetId: null,
    lastUpdated: new Date("2025-11-04T15:20:00"),
  },
];

export const MOCK_MODELS = [
  {
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
  },
  {
    id: "2",
    userId: "1",
    name: "distilbert-sentiment",
    baseModel: "distilbert-base-uncased",
    version: "1.0",
    accuracy: "92.8%",
    f1Score: "0.91",
    loss: "0.18",
    status: "ready",
    datasetId: "2",
    createdAt: new Date("2025-10-28T09:15:00"),
  },
];

export const MOCK_DATASETS = [
  {
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
      { id: 3, text: "Amazing service", sentiment: "positive", timestamp: "2025-01-17" },
    ],
    uploadedAt: new Date("2025-11-01T12:00:00"),
  },
  {
    id: "2",
    userId: "1",
    name: "product_reviews.csv",
    fileName: "product_reviews.csv",
    rowCount: 3200,
    columnCount: 3,
    fileSize: 312000,
    status: "ready",
    previewData: [
      { id: 1, review: "Excellent quality", rating: 5 },
      { id: 2, review: "Could be better", rating: 3 },
    ],
    uploadedAt: new Date("2025-10-25T16:30:00"),
  },
];

export const MOCK_FINE_TUNE_JOBS = [
  {
    id: "1",
    userId: "1",
    modelId: "1",
    datasetId: "1",
    baseModel: "bert-base-uncased",
    status: "completed",
    progress: 100,
    currentStep: "Deployed",
    logs: "Training completed successfully",
    createdAt: new Date("2025-11-03T13:00:00"),
    completedAt: new Date("2025-11-03T14:00:00"),
  },
  {
    id: "2",
    userId: "1",
    modelId: null,
    datasetId: "2",
    baseModel: "distilbert-base-uncased",
    status: "training",
    progress: 67,
    currentStep: "Training",
    logs: "Epoch 7/10...",
    createdAt: new Date("2025-11-05T10:00:00"),
    completedAt: null,
  },
];

export const BASE_MODELS = [
  { id: "bert-base-uncased", name: "BERT Base Uncased", task: "text-classification" },
  { id: "distilbert-base-uncased", name: "DistilBERT Base", task: "text-classification" },
  { id: "roberta-base", name: "RoBERTa Base", task: "text-classification" },
  { id: "albert-base-v2", name: "ALBERT Base v2", task: "text-classification" },
];
