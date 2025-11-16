import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getModels, createApiKey } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

const formSchema = z.object({
  model_id: z.string().min(1, "Model is required"),
});

interface ApiKeyFormProps {
  onSuccess?: () => void;
}

export function ApiKeyForm({ onSuccess }: ApiKeyFormProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: models, isLoading: isLoadingModels } = useQuery({
    queryKey: ["models"],
    queryFn: getModels,
  });

  const mutation = useMutation({
    mutationFn: createApiKey,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
      toast({
        title: "API Key Generated",
        description: "Your new API key has been created successfully.",
      });
      // Reset form after success
      form.reset();
      // Call onSuccess callback if provided
      onSuccess?.();
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.message || "Failed to generate API key.",
        variant: "destructive",
      });
    },
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      model_id: "",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    // Generate a default name based on timestamp
    const keyName = `api-key-${Date.now()}`;
    mutation.mutate({ name: keyName, model_id: values.model_id });
  }

  const selectedModel = models?.find((m: any) =>
    (m._id || m.id) === form.watch("model_id")
  );

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="model_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Select Model</FormLabel>
              <Select
                onValueChange={field.onChange}
                value={field.value}
                defaultValue={field.value}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a model">
                      {field.value && models
                        ? models?.find((m: any) => (m._id || m.id) === field.value)?.name ||
                          models?.find((m: any) => (m._id || m.id) === field.value)?.baseModel ||
                          "Select a model"
                        : "Select a model"
                      }
                    </SelectValue>
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {isLoadingModels ? (
                    <SelectItem value="loading" disabled>
                      Loading models...
                    </SelectItem>
                  ) : !models || models.length === 0 ? (
                    <SelectItem value="no-models" disabled>
                      No models available. Train a model first.
                    </SelectItem>
                  ) : (
                    models?.map((model: any) => {
                      const modelId = model._id || model.id;
                      const modelName = model.name || model.baseModel || 'Unnamed Model';
                      const modelStatus = model.status || '';

                      return (
                        <SelectItem
                          key={modelId}
                          value={modelId}
                          disabled={modelStatus !== 'completed' && modelStatus !== 'ready'}
                        >
                          <div className="flex flex-col">
                            <span className="font-medium">{modelName}</span>
                            {model.baseModel && model.name !== model.baseModel && (
                              <span className="text-xs text-muted-foreground">
                                Base: {model.baseModel}
                              </span>
                            )}
                            {modelStatus && (
                              <span className={`text-xs ${
                                modelStatus === 'completed' || modelStatus === 'ready'
                                  ? 'text-green-600'
                                  : 'text-yellow-600'
                              }`}>
                                Status: {modelStatus}
                              </span>
                            )}
                          </div>
                        </SelectItem>
                      );
                    })
                  )}
                </SelectContent>
              </Select>
              <FormMessage />
              {selectedModel && (
                <div className="text-xs text-muted-foreground mt-2 p-2 bg-muted rounded">
                  <p><strong>Model:</strong> {selectedModel.name || selectedModel.baseModel}</p>
                  {selectedModel.accuracy && (
                    <p><strong>Accuracy:</strong> {selectedModel.accuracy}</p>
                  )}
                  {selectedModel.taskType && (
                    <p><strong>Task:</strong> {selectedModel.taskType}</p>
                  )}
                </div>
              )}
            </FormItem>
          )}
        />
        <Button type="submit" disabled={mutation.isPending || !form.watch("model_id")} className="w-full">
          {mutation.isPending ? "Generating Key..." : "Generate Key"}
        </Button>
      </form>
    </Form>
  );
}
