import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import {
  LabelingTaskType,
  LabelingConfig,
  getTaskTypeDisplayName,
} from "@/lib/labeling-types";

interface ConfigurationModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (config: LabelingConfig) => void;
  fileCount: number;
  files?: File[];
}

/**
 * Detect the most appropriate default task type based on uploaded files
 */
function detectDefaultTaskType(files: File[]): LabelingTaskType {
  if (!files || files.length === 0) {
    return LabelingTaskType.TEXT_CLASSIFICATION;
  }

  const fileTypes = files.map((file) => {
    const type = file.type || "";
    const name = file.name.toLowerCase();

    if (type.startsWith("image/") || /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(name)) {
      return "image";
    } else if (type.startsWith("audio/") || /\.(mp3|wav|m4a|ogg)$/i.test(name)) {
      return "audio";
    } else if (type.startsWith("video/") || /\.(mp4|avi|mov|wmv|flv)$/i.test(name)) {
      return "video";
    } else {
      return "text";
    }
  });

  // Return the most common file type
  const typeCounts = fileTypes.reduce((acc, type) => {
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const dominantType = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0][0];

  switch (dominantType) {
    case "image":
      return LabelingTaskType.IMAGE_CLASSIFICATION;
    case "audio":
      return LabelingTaskType.AUDIO_TRANSCRIPTION;
    case "video":
      return LabelingTaskType.VIDEO_ANALYSIS;
    case "text":
    default:
      return LabelingTaskType.TEXT_CLASSIFICATION;
  }
}

export function ConfigurationModal({
  open,
  onClose,
  onSubmit,
  fileCount,
  files = [],
}: ConfigurationModalProps) {
  const [taskType, setTaskType] = useState<LabelingTaskType>(
    detectDefaultTaskType(files)
  );

  // Update task type when files change
  useEffect(() => {
    if (open && files.length > 0) {
      setTaskType(detectDefaultTaskType(files));
    }
  }, [open, files]);

  const [targetLabels, setTargetLabels] = useState("");
  const [numSuggestions, setNumSuggestions] = useState(5);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.7);

  // Update default labels when task type changes
  useEffect(() => {
    if (taskType === LabelingTaskType.TEXT_CLASSIFICATION) {
      setTargetLabels("Technology, Business, Finance, Politics, Science, Sports, Entertainment, Health");
    } else if (taskType === LabelingTaskType.IMAGE_CLASSIFICATION) {
      setTargetLabels("");
    } else {
      setTargetLabels("");
    }
  }, [taskType]);

  const handleSubmit = () => {
    const config: LabelingConfig = {
      task_type: taskType,
      target_labels: targetLabels
        ? targetLabels.split(",").map((label) => label.trim()).filter(Boolean)
        : undefined,
      num_suggestions: numSuggestions,
      confidence_threshold: confidenceThreshold,
    };
    onSubmit(config);
  };

  const taskTypeOptions = [
    { value: LabelingTaskType.IMAGE_CLASSIFICATION, category: "Image" },
    { value: LabelingTaskType.OBJECT_DETECTION, category: "Image" },
    { value: LabelingTaskType.TEXT_CLASSIFICATION, category: "Text" },
    { value: LabelingTaskType.SENTIMENT_ANALYSIS, category: "Text" },
    { value: LabelingTaskType.ENTITY_EXTRACTION, category: "Text" },
    { value: LabelingTaskType.NER, category: "Text" },
    { value: LabelingTaskType.AUDIO_TRANSCRIPTION, category: "Audio" },
    { value: LabelingTaskType.VIDEO_ANALYSIS, category: "Video" },
  ];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Configure Labeling Task</DialogTitle>
          <DialogDescription>
            Configure how you want to label your {fileCount} file{fileCount !== 1 ? "s" : ""}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Task Type Selection */}
          <div className="space-y-2">
            <Label htmlFor="task-type">Labeling Task Type</Label>
            <Select
              value={taskType}
              onValueChange={(value) => setTaskType(value as LabelingTaskType)}
            >
              <SelectTrigger id="task-type">
                <SelectValue placeholder="Select task type" />
              </SelectTrigger>
              <SelectContent>
                {/* Group by category */}
                <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                  Image Tasks
                </div>
                {taskTypeOptions
                  .filter((opt) => opt.category === "Image")
                  .map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {getTaskTypeDisplayName(opt.value)}
                    </SelectItem>
                  ))}

                <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                  Text Tasks
                </div>
                {taskTypeOptions
                  .filter((opt) => opt.category === "Text")
                  .map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {getTaskTypeDisplayName(opt.value)}
                    </SelectItem>
                  ))}

                <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                  Audio/Video Tasks
                </div>
                {taskTypeOptions
                  .filter((opt) => opt.category === "Audio" || opt.category === "Video")
                  .map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {getTaskTypeDisplayName(opt.value)}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>

          {/* Target Labels (Optional) */}
          {(taskType === LabelingTaskType.IMAGE_CLASSIFICATION ||
            taskType === LabelingTaskType.TEXT_CLASSIFICATION ||
            taskType === LabelingTaskType.OBJECT_DETECTION) && (
            <div className="space-y-2">
              <Label htmlFor="target-labels">
                Target Labels (Optional)
              </Label>
              <Textarea
                id="target-labels"
                placeholder="Enter labels separated by commas (e.g., cat, dog, bird)"
                value={targetLabels}
                onChange={(e) => setTargetLabels(e.target.value)}
                rows={3}
              />
              <p className="text-xs text-muted-foreground">
                Leave empty to let AI suggest labels automatically
              </p>
            </div>
          )}

          {/* Number of Suggestions */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="num-suggestions">Number of Suggestions</Label>
              <span className="text-sm text-muted-foreground">{numSuggestions}</span>
            </div>
            <Slider
              id="num-suggestions"
              min={1}
              max={20}
              step={1}
              value={[numSuggestions]}
              onValueChange={(value) => setNumSuggestions(value[0])}
            />
          </div>

          {/* Confidence Threshold */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="confidence-threshold">Confidence Threshold</Label>
              <span className="text-sm text-muted-foreground">
                {(confidenceThreshold * 100).toFixed(0)}%
              </span>
            </div>
            <Slider
              id="confidence-threshold"
              min={0}
              max={1}
              step={0.05}
              value={[confidenceThreshold]}
              onValueChange={(value) => setConfidenceThreshold(value[0])}
            />
            <p className="text-xs text-muted-foreground">
              Only show labels with confidence above this threshold
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>
            Start Labeling
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
