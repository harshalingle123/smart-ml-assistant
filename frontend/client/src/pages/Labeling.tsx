import { useState, useEffect } from "react";
import { useNavigate } from "wouter";
import {Plus, Tag, FileText, Loader2, Trash2, Calendar, CheckCircle2, XCircle, Clock } from "lucide-react";
import { getLabelingDatasets, createLabelingDataset, deleteLabelingDataset } from "../lib/api";
import { LabelingDataset, LabelingTask } from "../types/labeling";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { useToast } from "../hooks/use-toast";

export default function Labeling() {
  const [datasets, setDatasets] = useState<LabelingDataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [newDatasetName, setNewDatasetName] = useState("");
  const [newDatasetTask, setNewDatasetTask] = useState<string>(LabelingTask.GENERAL);
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const data = await getLabelingDatasets();
      setDatasets(data);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDatasets();
  }, []);

  const handleCreateDataset = async () => {
    if (!newDatasetName.trim()) {
      toast({
        title: "Error",
        description: "Please enter a dataset name",
        variant: "destructive",
      });
      return;
    }

    try {
      setCreating(true);
      await createLabelingDataset({
        name: newDatasetName,
        task: newDatasetTask,
      });
      toast({
        title: "Success",
        description: "Dataset created successfully",
      });
      setCreateOpen(false);
      setNewDatasetName("");
      setNewDatasetTask(LabelingTask.GENERAL);
      loadDatasets();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteDataset = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this dataset? All files will be removed.")) {
      return;
    }

    try {
      await deleteLabelingDataset(id);
      toast({
        title: "Success",
        description: "Dataset deleted successfully",
      });
      loadDatasets();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  const getTaskDisplayName = (task: string) => {
    const taskMap: Record<string, string> = {
      [LabelingTask.GENERAL]: "General Analysis",
      [LabelingTask.OBJECT_DETECTION]: "Object Detection",
      [LabelingTask.SEGMENTATION]: "Segmentation",
      [LabelingTask.CAPTIONING]: "Image Captioning",
      [LabelingTask.SENTIMENT]: "Sentiment Analysis",
      [LabelingTask.TRANSCRIPTION]: "Transcription",
      [LabelingTask.ENTITY_EXTRACTION]: "Entity Extraction",
      [LabelingTask.SUMMARIZATION]: "Summarization",
    };
    return taskMap[task] || task;
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Labeling Datasets</h1>
          <p className="text-muted-foreground mt-1">
            AI-powered multi-modal data labeling
          </p>
        </div>

        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Dataset
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Labeling Dataset</DialogTitle>
              <DialogDescription>
                Create a new dataset for AI-powered labeling
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div>
                <Label htmlFor="name">Dataset Name</Label>
                <Input
                  id="name"
                  value={newDatasetName}
                  onChange={(e) => setNewDatasetName(e.target.value)}
                  placeholder="My Images Dataset"
                />
              </div>

              <div>
                <Label htmlFor="task">Labeling Task</Label>
                <Select value={newDatasetTask} onValueChange={setNewDatasetTask}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={LabelingTask.GENERAL}>
                      General Analysis
                    </SelectItem>
                    <SelectItem value={LabelingTask.OBJECT_DETECTION}>
                      Object Detection
                    </SelectItem>
                    <SelectItem value={LabelingTask.SEGMENTATION}>
                      Segmentation
                    </SelectItem>
                    <SelectItem value={LabelingTask.CAPTIONING}>
                      Image Captioning
                    </SelectItem>
                    <SelectItem value={LabelingTask.SENTIMENT}>
                      Sentiment Analysis
                    </SelectItem>
                    <SelectItem value={LabelingTask.TRANSCRIPTION}>
                      Transcription
                    </SelectItem>
                    <SelectItem value={LabelingTask.ENTITY_EXTRACTION}>
                      Entity Extraction
                    </SelectItem>
                    <SelectItem value={LabelingTask.SUMMARIZATION}>
                      Summarization
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateDataset} disabled={creating}>
                {creating && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Create Dataset
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : datasets.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center p-12">
            <Tag className="w-12 h-12 text-muted-foreground mb-4" />
            <h3 className="text-xl font-semibold mb-2">No Datasets Yet</h3>
            <p className="text-muted-foreground text-center mb-4">
              Create your first labeling dataset to get started with AI-powered data labeling
            </p>
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Create Dataset
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {datasets.map((dataset) => (
            <Card
              key={dataset.id}
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => navigate(`/labeling/${dataset.id}`)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{dataset.name}</CardTitle>
                    <CardDescription className="mt-1">
                      {getTaskDisplayName(dataset.task)}
                    </CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => handleDeleteDataset(dataset.id, e)}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Total Files</span>
                    <span className="font-medium">{dataset.total_files}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-green-500" />
                      Completed
                    </span>
                    <span className="font-medium">{dataset.completed_files}</span>
                  </div>
                  {dataset.failed_files > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <XCircle className="w-3 h-3 text-red-500" />
                        Failed
                      </span>
                      <span className="font-medium text-destructive">
                        {dataset.failed_files}
                      </span>
                    </div>
                  )}
                  <div className="flex items-center justify-between pt-2 border-t">
                    <span className="text-muted-foreground flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      Created
                    </span>
                    <span className="text-xs">
                      {new Date(dataset.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {dataset.total_files > 0 && (
                  <div className="mt-4">
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className="bg-primary rounded-full h-2 transition-all"
                        style={{
                          width: `${(dataset.completed_files / dataset.total_files) * 100}%`,
                        }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 text-center">
                      {Math.round((dataset.completed_files / dataset.total_files) * 100)}% complete
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
