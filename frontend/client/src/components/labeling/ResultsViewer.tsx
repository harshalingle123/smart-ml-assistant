import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Edit2, Check } from "lucide-react";
import {
  LabelingResult,
  isImageLabel,
  isTextLabel,
  isEntityExtraction,
  isTranscript,
} from "@/lib/labeling-types";

interface ResultsViewerProps {
  results: LabelingResult[];
  taskType: string;
  onEditLabel?: (index: number, updatedLabel: string) => void;
}

export function ResultsViewer({
  results,
  taskType,
  onEditLabel,
}: ResultsViewerProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");

  const startEditing = (index: number, currentLabel: string) => {
    setEditingIndex(index);
    setEditValue(currentLabel);
  };

  const saveEdit = (index: number) => {
    if (onEditLabel) {
      onEditLabel(index, editValue);
    }
    setEditingIndex(null);
  };

  const cancelEdit = () => {
    setEditingIndex(null);
    setEditValue("");
  };

  const renderImageResult = (result: LabelingResult, index: number) => {
    if (!isImageLabel(result)) return null;

    return (
      <Card key={index}>
        <CardHeader>
          <CardTitle className="text-base flex items-center justify-between">
            <span className="truncate">{result.filename}</span>
            <Badge variant={result.confidence >= 0.8 ? "default" : "secondary"}>
              {(result.confidence * 100).toFixed(0)}%
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {result.classification && (
            <div>
              <p className="text-sm text-muted-foreground mb-1">Classification:</p>
              <div className="flex items-center gap-2">
                {editingIndex === index ? (
                  <>
                    <Input
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      className="flex-1"
                    />
                    <Button size="icon" variant="ghost" onClick={() => saveEdit(index)}>
                      <Check className="h-4 w-4" />
                    </Button>
                  </>
                ) : (
                  <>
                    <Badge variant="outline" className="font-medium">
                      {result.classification}
                    </Badge>
                    {onEditLabel && (
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => startEditing(index, result.classification || "")}
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                    )}
                  </>
                )}
              </div>
            </div>
          )}

          {result.objects && result.objects.length > 0 && (
            <div>
              <p className="text-sm text-muted-foreground mb-2">
                Detected Objects ({result.objects.length}):
              </p>
              <div className="flex flex-wrap gap-2">
                {result.objects.map((obj, objIndex) => (
                  <Badge key={objIndex} variant="secondary">
                    {obj.label} ({(obj.confidence * 100).toFixed(0)}%)
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {result.scene_description && (
            <div>
              <p className="text-sm text-muted-foreground mb-1">Description:</p>
              <p className="text-sm">{result.scene_description}</p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderTextResult = (result: LabelingResult, index: number) => {
    if (!isTextLabel(result)) return null;

    return (
      <Card key={index}>
        <CardHeader>
          <CardTitle className="text-base flex items-center justify-between">
            <span>Text Label</span>
            <Badge variant={result.confidence >= 0.8 ? "default" : "secondary"}>
              {(result.confidence * 100).toFixed(0)}%
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Text:</p>
            <p className="text-sm bg-muted p-2 rounded max-h-24 overflow-y-auto">
              {result.text.length > 200 ? `${result.text.substring(0, 200)}...` : result.text}
            </p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-1">Label:</p>
            <div className="flex items-center gap-2">
              {editingIndex === index ? (
                <>
                  <Input
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    className="flex-1"
                  />
                  <Button size="icon" variant="ghost" onClick={() => saveEdit(index)}>
                    <Check className="h-4 w-4" />
                  </Button>
                </>
              ) : (
                <>
                  <Badge variant="outline" className="font-medium">
                    {result.label}
                  </Badge>
                  {onEditLabel && (
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => startEditing(index, result.label)}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                  )}
                </>
              )}
            </div>
          </div>

          {result.sentiment && (
            <div>
              <p className="text-sm text-muted-foreground mb-1">Sentiment:</p>
              <Badge variant="secondary">{result.sentiment}</Badge>
            </div>
          )}

          {result.explanation && (
            <div>
              <p className="text-sm text-muted-foreground mb-1">Explanation:</p>
              <p className="text-sm">{result.explanation}</p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderEntityResult = (result: LabelingResult, index: number) => {
    if (!isEntityExtraction(result)) return null;

    return (
      <Card key={index}>
        <CardHeader>
          <CardTitle className="text-base">Entity Extraction</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Text:</p>
            <p className="text-sm bg-muted p-2 rounded max-h-24 overflow-y-auto">
              {result.text.length > 200 ? `${result.text.substring(0, 200)}...` : result.text}
            </p>
          </div>

          {result.entities.length > 0 && (
            <div>
              <p className="text-sm text-muted-foreground mb-2">
                Entities ({result.entities.length}):
              </p>
              <div className="space-y-2">
                {result.entities.map((entity, entityIndex) => (
                  <div key={entityIndex} className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline">{entity.text}</Badge>
                    <Badge variant="secondary" className="text-xs">
                      {entity.type}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.summary && (
            <div>
              <p className="text-sm text-muted-foreground mb-1">Summary:</p>
              <p className="text-sm">{result.summary}</p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderTranscriptResult = (result: LabelingResult, index: number) => {
    if (!isTranscript(result)) return null;

    return (
      <Card key={index}>
        <CardHeader>
          <CardTitle className="text-base flex items-center justify-between">
            <span className="truncate">{result.filename}</span>
            <Badge variant={result.confidence >= 0.8 ? "default" : "secondary"}>
              {(result.confidence * 100).toFixed(0)}%
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Transcript:</p>
            <p className="text-sm bg-muted p-2 rounded max-h-40 overflow-y-auto">
              {result.transcript}
            </p>
          </div>

          {result.language && (
            <div>
              <p className="text-sm text-muted-foreground mb-1">Language:</p>
              <Badge variant="secondary">{result.language}</Badge>
            </div>
          )}

          {result.summary && (
            <div>
              <p className="text-sm text-muted-foreground mb-1">Summary:</p>
              <p className="text-sm">{result.summary}</p>
            </div>
          )}

          {result.key_points && result.key_points.length > 0 && (
            <div>
              <p className="text-sm text-muted-foreground mb-2">Key Points:</p>
              <ul className="list-disc list-inside space-y-1">
                {result.key_points.map((point, pointIndex) => (
                  <li key={pointIndex} className="text-sm">
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  if (results.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>No results to display</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Labeling Results ({results.length})</h3>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {results.map((result, index) => {
          if (isImageLabel(result)) return renderImageResult(result, index);
          if (isTextLabel(result)) return renderTextResult(result, index);
          if (isEntityExtraction(result)) return renderEntityResult(result, index);
          if (isTranscript(result)) return renderTranscriptResult(result, index);
          return null;
        })}
      </div>
    </div>
  );
}
