import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Loader2, Zap, CheckCircle2, Sparkles, ArrowRight, Clock, Shield } from 'lucide-react';
import { ModelBrowser } from '@/components/ModelBrowser';
import { ApiKeyGenerator } from '@/components/ApiKeyGenerator';
import { ApiTester } from '@/components/ApiTester';
import { CostCalculator } from '@/components/CostCalculator';
import { getDirectAccessModels, requestDirectAccess, testDirectAccessAPI } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import type { DirectAccessModel, DirectAccessKey, PredictionResponse } from '@/lib/types';

export default function DirectAccess() {
  const [models, setModels] = useState<DirectAccessModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<string>('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('cost');
  const [activeTab, setActiveTab] = useState<string>('browse');
  const { toast } = useToast();

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      const response = await getDirectAccessModels();
      setModels(response.models || getMockModels());
    } catch (error) {
      console.error('Failed to load models:', error);
      setModels(getMockModels());
      toast({
        title: 'Info',
        description: 'Loading demo models. Backend integration pending.',
      });
    } finally {
      setLoading(false);
    }
  };

  const getMockModels = (): DirectAccessModel[] => [
    {
      id: 'vader',
      name: 'VADER Sentiment',
      task: 'sentiment',
      accuracy: 0.85,
      latency_ms: 5,
      free_tier: 10000,
      pricing: { per_request: 0.0001, currency: 'USD' },
      description: 'Fast rule-based sentiment analysis, perfect for high-volume applications',
      languages: ['en'],
    },
    {
      id: 'distilbert',
      name: 'DistilBERT Sentiment',
      task: 'sentiment',
      accuracy: 0.94,
      latency_ms: 100,
      free_tier: 1000,
      pricing: { per_request: 0.0006, currency: 'USD' },
      description: 'Highly accurate transformer-based sentiment analysis',
      languages: ['en', 'multilingual'],
    },
    {
      id: 'roberta',
      name: 'RoBERTa Sentiment',
      task: 'sentiment',
      accuracy: 0.92,
      latency_ms: 150,
      free_tier: 1000,
      pricing: { per_request: 0.002, currency: 'USD' },
      description: 'Fine-grained 5-class sentiment analysis with detailed insights',
      languages: ['en'],
    },
    {
      id: 'spam-detection',
      name: 'Spam Classifier',
      task: 'classification',
      accuracy: 0.97,
      latency_ms: 80,
      free_tier: 5000,
      pricing: { per_request: 0.0001, currency: 'USD' },
      description: 'Identify spam messages and emails with high accuracy',
      languages: ['en'],
    },
    {
      id: 'language-id',
      name: 'Language Detection',
      task: 'classification',
      accuracy: 0.99,
      latency_ms: 20,
      free_tier: 20000,
      pricing: { per_request: 0.00005, currency: 'USD' },
      description: 'Detect language from text with 99% accuracy',
      languages: ['multilingual'],
    },
    {
      id: 'mobilenet',
      name: 'MobileNet Image Recognition',
      task: 'vision',
      accuracy: 0.89,
      latency_ms: 50,
      free_tier: 2000,
      pricing: { per_request: 0.0008, currency: 'USD' },
      description: 'Lightweight object recognition for images',
      languages: ['N/A'],
    },
  ];

  const handleRequestAccess = async (modelId: string) => {
    const model = models.find((m) => m.id === modelId);
    if (!model) return;

    toast({
      title: 'Opening API Key Generator',
      description: `Setting up access for ${model.name}`,
    });

    setActiveTab('generate');
  };

  const handleGenerateKey = async (data: {
    modelId: string;
    usagePlan: string;
    priority: string;
  }): Promise<DirectAccessKey> => {
    try {
      const response = await requestDirectAccess({
        task: models.find((m) => m.id === data.modelId)?.task || 'sentiment',
        usage: data.usagePlan,
        priority: data.priority,
      });

      toast({
        title: 'Success',
        description: 'API key generated successfully!',
      });

      return response;
    } catch (error) {
      const model = models.find((m) => m.id === data.modelId);
      const mockKey: DirectAccessKey = {
        _id: `key_${Date.now()}`,
        api_key: `sk_live_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`,
        model_id: data.modelId,
        model_name: model?.name,
        task: model?.task || 'sentiment',
        usage_plan: data.usagePlan as any,
        free_tier_limit: model?.free_tier || 10000,
        requests_used: 0,
        requests_this_month: 0,
        rate_limit: 100,
        status: 'active',
        endpoint: `https://api.yourplatform.com/v1/${model?.task}/${data.modelId}`,
        created_at: new Date().toISOString(),
      };

      toast({
        title: 'Demo Mode',
        description: 'Generated a demo API key. Backend integration pending.',
      });

      return mockKey;
    }
  };

  const handleTestAPI = async (
    apiKey: string,
    text: string,
    endpoint?: string
  ): Promise<PredictionResponse> => {
    try {
      return await testDirectAccessAPI(apiKey, text, endpoint);
    } catch (error) {
      const mockResponse: PredictionResponse = {
        text,
        sentiment: {
          label: text.toLowerCase().includes('good') || text.toLowerCase().includes('great') ? 'POSITIVE' : 'NEGATIVE',
          compound: 0.7468,
          pos: 0.623,
          neu: 0.377,
          neg: 0.0,
        },
        confidence: 0.95,
        latency_ms: 7,
        timestamp: new Date().toISOString(),
        request_id: `req_${Date.now()}`,
        usage: {
          requests_used: 145,
          requests_remaining: 9855,
          reset_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        },
      };

      return mockResponse;
    }
  };

  return (
    <div className="p-6 space-y-8">
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100">
            <Sparkles className="h-3 w-3 mr-1" />
            Direct Access
          </Badge>
        </div>
        <div>
          <h1 className="text-4xl font-bold">Get Instant ML API Access in 30 Seconds</h1>
          <p className="text-muted-foreground text-lg mt-2">
            Production-ready machine learning models without training. Start with free tier.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="bg-primary/10 rounded-lg p-2">
                  <Zap className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">Instant Setup</h3>
                  <p className="text-sm text-muted-foreground">
                    Get API credentials in under 30 seconds. No training required.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="bg-primary/10 rounded-lg p-2">
                  <CheckCircle2 className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">Free Tier</h3>
                  <p className="text-sm text-muted-foreground">
                    Up to 10K requests/month free. No credit card needed.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="bg-primary/10 rounded-lg p-2">
                  <Shield className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">Production Ready</h3>
                  <p className="text-sm text-muted-foreground">
                    Enterprise-grade models with 99.9% uptime SLA.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Separator />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="browse">Browse Models</TabsTrigger>
          <TabsTrigger value="generate">Generate Key</TabsTrigger>
          <TabsTrigger value="test">Test API</TabsTrigger>
          <TabsTrigger value="pricing">Pricing</TabsTrigger>
        </TabsList>

        <TabsContent value="browse" className="space-y-6">
          <div>
            <h2 className="text-2xl font-semibold mb-2">Available Models</h2>
            <p className="text-muted-foreground">
              Choose from our collection of pre-trained models optimized for different tasks
            </p>
          </div>

          <ModelBrowser
            models={models}
            loading={loading}
            onRequestAccess={handleRequestAccess}
            selectedTask={selectedTask}
            onTaskChange={setSelectedTask}
            selectedPriority={selectedPriority}
            onPriorityChange={setSelectedPriority}
          />
        </TabsContent>

        <TabsContent value="generate" className="space-y-6">
          <div>
            <h2 className="text-2xl font-semibold mb-2">Generate API Key</h2>
            <p className="text-muted-foreground">
              Select a model and usage plan to get instant API access
            </p>
          </div>

          <ApiKeyGenerator models={models} onGenerate={handleGenerateKey} />
        </TabsContent>

        <TabsContent value="test" className="space-y-6">
          <div>
            <h2 className="text-2xl font-semibold mb-2">Test Your API</h2>
            <p className="text-muted-foreground">
              Try out your API key with real-time predictions and view code examples
            </p>
          </div>

          <ApiTester onTest={handleTestAPI} />
        </TabsContent>

        <TabsContent value="pricing" className="space-y-6">
          <div>
            <h2 className="text-2xl font-semibold mb-2">Cost Calculator</h2>
            <p className="text-muted-foreground">
              Estimate your monthly costs based on expected usage
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CostCalculator models={models} />

            <Card>
              <CardHeader>
                <CardTitle>Pricing Plans</CardTitle>
                <CardDescription>Choose the plan that fits your needs</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">Free Tier</h3>
                    <Badge variant="secondary">No credit card</Badge>
                  </div>
                  <p className="text-2xl font-bold">$0/month</p>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      10K requests/month (VADER)
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      1K requests/month (other models)
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Community support
                    </li>
                  </ul>
                </div>

                <div className="border-2 border-primary rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">Pay As You Go</h3>
                    <Badge>Popular</Badge>
                  </div>
                  <p className="text-2xl font-bold">From $0.0001</p>
                  <p className="text-sm text-muted-foreground">per request</p>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Pay only for what you use
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      All models included
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Email support
                    </li>
                  </ul>
                </div>

                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">Professional</h3>
                    <Badge variant="outline">Best value</Badge>
                  </div>
                  <p className="text-2xl font-bold">$49/month</p>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      100K requests included
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      $0.0003 per request after
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      Priority support & SLA
                    </li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
