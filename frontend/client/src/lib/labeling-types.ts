/**
 * TypeScript types for AI-powered data labeling
 * These mirror the backend Pydantic schemas in app/schemas/labeling_schemas.py
 */

export enum LabelingTaskType {
  IMAGE_CLASSIFICATION = "image_classification",
  OBJECT_DETECTION = "object_detection",
  TEXT_CLASSIFICATION = "text_classification",
  SENTIMENT_ANALYSIS = "sentiment_analysis",
  AUDIO_TRANSCRIPTION = "audio_transcription",
  VIDEO_ANALYSIS = "video_analysis",
  ENTITY_EXTRACTION = "entity_extraction",
  NER = "ner",
}

export interface LabelingConfig {
  task_type: LabelingTaskType;
  target_labels?: string[];
  num_suggestions?: number;
  confidence_threshold?: number;
}

export interface DetectedObject {
  label: string;
  confidence: number;
  bounding_box?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface ImageLabel {
  filename: string;
  task_type: string;
  classification?: string;
  objects?: DetectedObject[];
  scene_description?: string;
  confidence: number;
}

export interface TextLabel {
  text: string;
  label: string;
  sentiment?: string;
  confidence: number;
  explanation?: string;
}

export interface Entity {
  text: string;
  type: string;
  start_index: number;
  end_index: number;
  confidence?: number;
}

export interface EntityExtraction {
  text: string;
  entities: Entity[];
  summary?: string;
}

export interface Transcript {
  filename: string;
  transcript: string;
  language?: string;
  confidence: number;
  summary?: string;
  key_points?: string[];
}

export type LabelingResult =
  | ImageLabel
  | TextLabel
  | EntityExtraction
  | Transcript;

export interface LabelingResponse {
  results: LabelingResult[];
  task_type: string;
  total_processed: number;
  success_count: number;
  error_count?: number;
  errors?: string[];
}

export interface RefineLabelRequest {
  labels: LabelingResult[];
  feedback: string;
}

/**
 * Helper function to check if a result is an ImageLabel
 */
export function isImageLabel(result: LabelingResult): result is ImageLabel {
  return "filename" in result && ("classification" in result || "objects" in result);
}

/**
 * Helper function to check if a result is a TextLabel
 */
export function isTextLabel(result: LabelingResult): result is TextLabel {
  return "text" in result && "label" in result && !("entities" in result);
}

/**
 * Helper function to check if a result is an EntityExtraction
 */
export function isEntityExtraction(
  result: LabelingResult
): result is EntityExtraction {
  return "text" in result && "entities" in result;
}

/**
 * Helper function to check if a result is a Transcript
 */
export function isTranscript(result: LabelingResult): result is Transcript {
  return "filename" in result && "transcript" in result;
}

/**
 * Get task type display name
 */
export function getTaskTypeDisplayName(taskType: LabelingTaskType): string {
  const displayNames: Record<LabelingTaskType, string> = {
    [LabelingTaskType.IMAGE_CLASSIFICATION]: "Image Classification",
    [LabelingTaskType.OBJECT_DETECTION]: "Object Detection",
    [LabelingTaskType.TEXT_CLASSIFICATION]: "Text Classification",
    [LabelingTaskType.SENTIMENT_ANALYSIS]: "Sentiment Analysis",
    [LabelingTaskType.AUDIO_TRANSCRIPTION]: "Audio Transcription",
    [LabelingTaskType.VIDEO_ANALYSIS]: "Video Analysis",
    [LabelingTaskType.ENTITY_EXTRACTION]: "Entity Extraction",
    [LabelingTaskType.NER]: "Named Entity Recognition",
  };
  return displayNames[taskType];
}

/**
 * Get supported file types for a task type
 */
export function getSupportedFileTypes(taskType: LabelingTaskType): string {
  const fileTypes: Record<LabelingTaskType, string> = {
    [LabelingTaskType.IMAGE_CLASSIFICATION]: "image/*",
    [LabelingTaskType.OBJECT_DETECTION]: "image/*",
    [LabelingTaskType.TEXT_CLASSIFICATION]: ".txt,.csv,.md,text/*",
    [LabelingTaskType.SENTIMENT_ANALYSIS]: ".txt,.csv,.md,text/*",
    [LabelingTaskType.AUDIO_TRANSCRIPTION]: "audio/*,.mp3,.wav",
    [LabelingTaskType.VIDEO_ANALYSIS]: "video/*,.mp4,.avi,.mov",
    [LabelingTaskType.ENTITY_EXTRACTION]: ".txt,.csv,.md,text/*",
    [LabelingTaskType.NER]: ".txt,.csv,.md,text/*",
  };
  return fileTypes[taskType];
}
