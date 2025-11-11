import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ApiKeyForm } from "@/components/ApiKeyForm";
import { getApiKeys, deleteApiKey } from "@/lib/api";

export default function Settings() {
  const queryClient = useQueryClient();

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ["apiKeys"],
    queryFn: getApiKeys,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteApiKey,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
    },
  });

  const handleRevoke = (apiKeyId: string) => {
    deleteMutation.mutate(apiKeyId);
  };

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-semibold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account and application settings
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>
            Manage your API keys for programmatic access.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <p>Loading...</p>
          ) : (
            <div className="space-y-4">
              {apiKeys?.map((apiKey: any) => (
                <Card key={apiKey.id}>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="font-semibold">{apiKey.name}</p>
                      <p className="text-sm text-muted-foreground font-mono">{apiKey.key}</p>
                      <p className="text-xs text-muted-foreground">Created on {new Date(apiKey.created_at).toLocaleDateString()}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button variant="outline">Copy</Button>
                      <Button variant="destructive" onClick={() => handleRevoke(apiKey.id)} disabled={deleteMutation.isPending}>
                        {deleteMutation.isPending ? "Revoking..." : "Revoke"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
          <Dialog>
            <DialogTrigger asChild>
              <Button>Generate New Key</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Generate New API Key</DialogTitle>
              </DialogHeader>
              <ApiKeyForm />
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
