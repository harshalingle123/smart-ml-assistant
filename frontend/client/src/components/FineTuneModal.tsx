import { useState } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";

interface FineTuneModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onStartFineTune: (config: FineTuneConfig) => void;
  datasets?: Array<{ id: string; name: string }>;
  baseModels?: Array<{ id: string; name: string }>;
}

export interface FineTuneConfig {
  datasetId: string;
  baseModel: string;
  epochs: number;
  batchSize: number;
  learningRate: number;
}

export function FineTuneModal({
  open,
  onOpenChange,
  onStartFineTune,
  datasets = [],
  baseModels = [],
}: FineTuneModalProps) {
  const [config, setConfig] = useState<FineTuneConfig>({
    datasetId: "",
    baseModel: "",
    epochs: 10,
    batchSize: 32,
    learningRate: 0.00002,
  });

  const handleStart = () => {
    onStartFineTune(config);
    onOpenChange(false);
  };

  const isValid = config.datasetId && config.baseModel;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Start Fine-Tuning</DialogTitle>
          <DialogDescription>
            Configure your fine-tuning job parameters
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-6 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="dataset">Dataset</Label>
              <Select
                value={config.datasetId}
                onValueChange={(value) =>
                  setConfig((prev) => ({ ...prev, datasetId: value }))
                }
              >
                <SelectTrigger id="dataset" data-testid="select-dataset">
                  <SelectValue placeholder="Select dataset" />
                </SelectTrigger>
                <SelectContent>
                  {datasets.map((dataset) => (
                    <SelectItem key={dataset.id} value={dataset.id}>
                      {dataset.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="model">Base Model</Label>
              <Select
                value={config.baseModel}
                onValueChange={(value) =>
                  setConfig((prev) => ({ ...prev, baseModel: value }))
                }
              >
                <SelectTrigger id="model" data-testid="select-model">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  {baseModels.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      {model.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="epochs">Epochs</Label>
              <Input
                id="epochs"
                type="number"
                value={config.epochs}
                onChange={(e) =>
                  setConfig((prev) => ({ ...prev, epochs: parseInt(e.target.value) }))
                }
                data-testid="input-epochs"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="batchSize">Batch Size</Label>
              <Input
                id="batchSize"
                type="number"
                value={config.batchSize}
                onChange={(e) =>
                  setConfig((prev) => ({ ...prev, batchSize: parseInt(e.target.value) }))
                }
                data-testid="input-batch-size"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="learningRate">Learning Rate</Label>
              <Input
                id="learningRate"
                type="number"
                step="0.00001"
                value={config.learningRate}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    learningRate: parseFloat(e.target.value),
                  }))
                }
                data-testid="input-learning-rate"
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleStart}
            disabled={!isValid}
            data-testid="button-start-fine-tune"
          >
            Start Fine-Tuning
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
