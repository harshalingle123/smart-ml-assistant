export interface HuggingFaceModel {
  id: string;
  name: string;
  author?: string;
  downloads: number;
  likes: number;
  task: string;
  languages?: string[];
  tags?: string[];
  library?: string;
  pipeline_tag?: string;
  modelSize?: string;
  parameters?: number;
  accuracy?: number;
  lastModified?: string;
  description?: string;
}

export interface TrainingJob {
  _id: string;
  job_name: string;
  model_id: string;
  dataset_id: string;
  status: "queued" | "training" | "completed" | "failed" | "cancelled";
  progress: number;
  current_epoch?: number;
  total_epochs?: number;
  estimated_completion?: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  metrics?: {
    accuracy?: number;
    loss?: number;
    validation_accuracy?: number;
    validation_loss?: number;
    [key: string]: any;
  };
  cost?: {
    estimated: number;
    actual: number;
    currency: string;
  };
  hyperparameters?: {
    learning_rate?: number;
    epochs?: number;
    batch_size?: number;
    [key: string]: any;
  };
  error_message?: string;
}

export interface PrebuiltModel {
  _id: string;
  name: string;
  model_id: string;
  task: string;
  description: string;
  languages: string[];
  accuracy?: number;
  latency_ms?: number;
  parameters?: number;
  license?: string;
  example_input?: string;
  example_output?: string;
  tags?: string[];
  deployment_ready: boolean;
  pricing?: {
    per_request: number;
    per_hour: number;
    currency: string;
  };
}

export interface Deployment {
  _id: string;
  deployment_name: string;
  model_id: string;
  model_name?: string;
  status: "active" | "inactive" | "deploying" | "failed";
  api_endpoint: string;
  api_key?: string;
  created_at: string;
  updated_at: string;
  instance_type?: string;
  auto_scaling?: boolean;
  min_instances?: number;
  max_instances?: number;
  current_instances?: number;
  metrics?: {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    avg_latency_ms: number;
    requests_per_hour: number;
  };
  cost?: {
    hourly: number;
    total: number;
    currency: string;
  };
}

export interface DeploymentMetrics {
  deployment_id: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  requests_per_hour: number;
  requests_per_day: number;
  error_rate: number;
  uptime_percentage: number;
  last_24h_requests: Array<{
    timestamp: string;
    count: number;
  }>;
}

export interface TrainingLog {
  timestamp: string;
  level: "info" | "warning" | "error";
  message: string;
  metrics?: Record<string, any>;
}

export interface DirectAccessModel {
  id: string;
  name: string;
  task: string;
  subtask?: string;
  accuracy: number;
  latency_ms: number;
  free_tier: number;
  pricing: {
    per_request: number;
    currency: string;
  };
  parameters?: number;
  description?: string;
  languages?: string[];
  example_input?: string;
  example_output?: string;
}

export interface DirectAccessKey {
  _id: string;
  api_key: string;
  model_id: string;
  model_name?: string;
  task: string;
  usage_plan: "free" | "pay_as_you_go" | "professional";
  free_tier_limit: number;
  requests_used: number;
  requests_this_month: number;
  rate_limit: number;
  status: "active" | "suspended" | "expired";
  endpoint: string;
  created_at: string;
  expires_at?: string;
  last_used_at?: string;
}

export interface UsageStatistics {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  average_latency_ms: number;
  by_model: Record<string, {
    requests: number;
    cost: number;
    free_tier_used: number;
    free_tier_remaining: number;
  }>;
  time_series: Array<{
    timestamp: string;
    requests: number;
  }>;
}

export interface CostBreakdown {
  current_month: {
    total_cost: number;
    free_tier_used: number;
    paid_requests: number;
  };
  projected_month: {
    estimated_cost: number;
    based_on_current_rate: boolean;
  };
  by_model: Record<string, {
    cost: number;
    requests: number;
  }>;
}

export interface PredictionResponse {
  text: string;
  sentiment?: {
    label: string;
    compound: number;
    pos: number;
    neu: number;
    neg: number;
  };
  confidence?: number;
  latency_ms: number;
  timestamp: string;
  request_id: string;
  usage?: {
    requests_used: number;
    requests_remaining: number;
    reset_date: string;
  };
}
