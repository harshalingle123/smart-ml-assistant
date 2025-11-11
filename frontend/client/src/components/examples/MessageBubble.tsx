import { MessageBubble } from "../MessageBubble";

export default function MessageBubbleExample() {
  return (
    <div className="flex flex-col gap-6 p-6 max-w-4xl">
      <MessageBubble
        role="user"
        content="Classify this sentence: 'I love this product!'"
        timestamp={new Date()}
      />
      <MessageBubble
        role="assistant"
        content="Detected Query Type: Simple. Running sentiment analysis using bert-base-uncased model..."
        queryType="simple"
        timestamp={new Date()}
      />
      <MessageBubble
        role="user"
        content="Analyze my customer_feedback.csv and find trends."
        timestamp={new Date()}
      />
      <MessageBubble
        role="assistant"
        content="Detected Query Type: Data-Based. I found your dataset has new patterns. Would you like to fine-tune bert-base-uncased for better accuracy?"
        queryType="data_based"
        timestamp={new Date()}
      />
    </div>
  );
}
