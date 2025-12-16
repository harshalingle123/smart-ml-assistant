export enum LabelingTask {
  GENERAL = "general_analysis",
  OBJECT_DETECTION = "object_detection",
  SEGMENTATION = "segmentation",
  CAPTIONING = "image_captioning",
  SENTIMENT = "sentiment_analysis",
  TRANSCRIPTION = "transcription",
  ENTITY_EXTRACTION = "entity_extraction",
  SUMMARIZATION = "summarization"
}

export enum MediaType {
  IMAGE = "image",
  VIDEO = "video",
  AUDIO = "audio",
  TEXT = "text",
  PDF = "pdf",
  UNKNOWN = "unknown"
}

export enum FileStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed"
}

export interface LabelData {
  summary?: string;
  sentiment?: string;
  objects?: Array<{
    label: string;
    confidence: number;
    location?: string;
    box_2d?: number[];
  }>;
  topics?: string[];
  events?: Array<{
    timestamp: string;
    description: string;
  }>;
  entities?: Array<{
    name: string;
    type: string;
  }>;
  safety_flags?: string[];
}

export interface LabelingFile {
  id: string;
  dataset_id: string;
  filename: string;
  original_name: string;
  media_type: MediaType;
  file_size: number;
  azure_blob_path: string;
  preview_url?: string;
  status: FileStatus;
  result?: LabelData;
  error_message?: string;
  uploaded_at: string;
  processed_at?: string;
}

export interface LabelingDataset {
  id: string;
  name: string;
  task: LabelingTask;
  target_labels?: string[];
  total_files: number;
  completed_files: number;
  failed_files: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface LabelingDatasetDetail extends LabelingDataset {
  files: LabelingFile[];
}

export interface CreateDatasetRequest {
  name: string;
  task: LabelingTask;
  target_labels?: string[];
}

export interface UpdateDatasetRequest {
  name?: string;
  target_labels?: string[];
}

export interface RefineLabelsRequest {
  verified_labels: string[];
}

export interface LabelSuggestionsRequest {
  file_ids: string[];
}

export interface LabelSuggestionsResponse {
  suggested_labels: string[];
}

export interface AnalyzeFilesRequest {
  file_ids: string[];
}
