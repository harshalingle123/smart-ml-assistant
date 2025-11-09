import { APIEndpointDisplay } from "../APIEndpointDisplay";

export default function APIEndpointDisplayExample() {
  return (
    <div className="p-6 max-w-3xl">
      <APIEndpointDisplay
        modelId="model_abc123"
        modelName="bert-user-v3.1"
        apiKey="sk_test_abc123xyz789..."
      />
    </div>
  );
}
