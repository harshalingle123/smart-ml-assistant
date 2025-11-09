import { useState } from "react";
import { FineTuneModal } from "../FineTuneModal";
import { Button } from "@/components/ui/button";

export default function FineTuneModalExample() {
  const [open, setOpen] = useState(false);

  const datasets = [
    { id: "1", name: "customer_feedback.csv" },
    { id: "2", name: "product_reviews.csv" },
  ];

  const baseModels = [
    { id: "bert-base-uncased", name: "BERT Base Uncased" },
    { id: "distilbert-base-uncased", name: "DistilBERT Base" },
  ];

  return (
    <div className="p-6">
      <Button onClick={() => setOpen(true)}>Open Fine-Tune Modal</Button>
      <FineTuneModal
        open={open}
        onOpenChange={setOpen}
        datasets={datasets}
        baseModels={baseModels}
        onStartFineTune={(config) => {
          console.log("Fine-tune config:", config);
        }}
      />
    </div>
  );
}
