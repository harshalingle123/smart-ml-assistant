import { useState } from "react";
import JSZip from "jszip";
import { Download, FileJson, FileText, FileArchive } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import {
  LabelingResult,
  isImageLabel,
  isTextLabel,
  isEntityExtraction,
  isTranscript,
} from "@/lib/labeling-types";

interface ExportControlsProps {
  results: LabelingResult[];
  taskType: string;
}

export function ExportControls({ results, taskType }: ExportControlsProps) {
  const { toast } = useToast();
  const [isExporting, setIsExporting] = useState(false);

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const exportJSON = () => {
    try {
      setIsExporting(true);
      const json = JSON.stringify(results, null, 2);
      const blob = new Blob([json], { type: "application/json" });
      downloadBlob(blob, `labeling-results-${Date.now()}.json`);

      toast({
        title: "Export Successful",
        description: "Results exported as JSON",
      });
    } catch (error) {
      toast({
        title: "Export Failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setIsExporting(false);
    }
  };

  const exportCSV = () => {
    try {
      setIsExporting(true);

      // Convert results to flat CSV structure
      const rows: any[] = [];

      results.forEach((result) => {
        if (isImageLabel(result)) {
          rows.push({
            type: "image",
            filename: result.filename,
            label: result.classification || result.objects?.map(o => o.label).join("; ") || "",
            confidence: result.confidence,
            description: result.scene_description || "",
          });
        } else if (isTextLabel(result)) {
          rows.push({
            type: "text",
            text: result.text.substring(0, 200),
            label: result.label,
            sentiment: result.sentiment || "",
            confidence: result.confidence,
            explanation: result.explanation || "",
          });
        } else if (isEntityExtraction(result)) {
          rows.push({
            type: "entity_extraction",
            text: result.text.substring(0, 200),
            entities: result.entities.map(e => `${e.text}(${e.type})`).join("; "),
            entity_count: result.entities.length,
            summary: result.summary || "",
          });
        } else if (isTranscript(result)) {
          rows.push({
            type: "transcript",
            filename: result.filename,
            transcript: result.transcript.substring(0, 500),
            language: result.language || "",
            confidence: result.confidence,
            summary: result.summary || "",
          });
        }
      });

      // Generate CSV
      if (rows.length === 0) {
        throw new Error("No data to export");
      }

      const headers = Object.keys(rows[0]);
      const csvContent = [
        headers.join(","),
        ...rows.map((row) =>
          headers.map((header) => {
            const value = String(row[header] || "");
            // Escape commas and quotes
            return `"${value.replace(/"/g, '""')}"`;
          }).join(",")
        ),
      ].join("\n");

      const blob = new Blob([csvContent], { type: "text/csv" });
      downloadBlob(blob, `labeling-results-${Date.now()}.csv`);

      toast({
        title: "Export Successful",
        description: "Results exported as CSV",
      });
    } catch (error) {
      toast({
        title: "Export Failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setIsExporting(false);
    }
  };

  const exportFineTuningZIP = async () => {
    try {
      setIsExporting(true);
      const zip = new JSZip();

      // Create JSONL file (one JSON object per line)
      const jsonlLines: string[] = [];

      results.forEach((result) => {
        let line: any = {};

        if (isImageLabel(result)) {
          line = {
            filename: result.filename,
            label: result.classification || "",
            task: "image_classification",
            confidence: result.confidence,
          };
        } else if (isTextLabel(result)) {
          line = {
            text: result.text,
            label: result.label,
            task: "text_classification",
            confidence: result.confidence,
          };
        } else if (isEntityExtraction(result)) {
          line = {
            text: result.text,
            entities: result.entities,
            task: "entity_extraction",
          };
        } else if (isTranscript(result)) {
          line = {
            filename: result.filename,
            transcript: result.transcript,
            task: "transcription",
            confidence: result.confidence,
          };
        }

        jsonlLines.push(JSON.stringify(line));
      });

      const jsonlContent = jsonlLines.join("\n");
      zip.file("labels.jsonl", jsonlContent);

      // Add metadata file
      const metadata = {
        task_type: taskType,
        total_samples: results.length,
        created_at: new Date().toISOString(),
        format: "jsonl",
        description: "AI-generated labels for fine-tuning",
      };
      zip.file("metadata.json", JSON.stringify(metadata, null, 2));

      // Add README
      const readme = `# Fine-tuning Dataset

This dataset was generated using AI-powered labeling.

## Contents
- labels.jsonl: Training data in JSONL format (one JSON object per line)
- metadata.json: Dataset metadata and statistics

## Format
Each line in labels.jsonl is a JSON object with the following structure:
- For images: {"filename": "...", "label": "...", "task": "image_classification", "confidence": 0.X}
- For text: {"text": "...", "label": "...", "task": "text_classification", "confidence": 0.X}
- For entities: {"text": "...", "entities": [...], "task": "entity_extraction"}

## Usage
This format is compatible with many ML training frameworks. You can use it to fine-tune models
for classification, entity recognition, or other supervised learning tasks.

Generated: ${new Date().toISOString()}
Task Type: ${taskType}
Total Samples: ${results.length}
`;
      zip.file("README.md", readme);

      // Generate and download ZIP
      const blob = await zip.generateAsync({ type: "blob" });
      downloadBlob(blob, `finetuning-dataset-${Date.now()}.zip`);

      toast({
        title: "Export Successful",
        description: "Fine-tuning dataset exported as ZIP",
      });
    } catch (error) {
      toast({
        title: "Export Failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setIsExporting(false);
    }
  };

  if (results.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">Export Results</h3>
            <p className="text-sm text-muted-foreground">
              Download your labeled data in different formats
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={exportJSON}
              disabled={isExporting}
            >
              <FileJson className="mr-2 h-4 w-4" />
              Export JSON
            </Button>

            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={exportCSV}
              disabled={isExporting}
            >
              <FileText className="mr-2 h-4 w-4" />
              Export CSV
            </Button>

            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={exportFineTuningZIP}
              disabled={isExporting}
            >
              <FileArchive className="mr-2 h-4 w-4" />
              Export ZIP (JSONL)
            </Button>
          </div>

          <p className="text-xs text-muted-foreground">
            <strong>Note:</strong> Results are not saved to the database. Export them before leaving this page.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
