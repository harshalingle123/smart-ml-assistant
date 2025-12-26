import { getApiUrl } from "./env";
import type { LabelingConfig, LabelingResponse } from "./labeling-types";

const BASE_URL = getApiUrl();

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("token");
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// Global handler for 401 errors
function handleUnauthorized(response: Response) {
  if (response.status === 401) {
    console.warn("[AUTH] Token expired or invalid, redirecting to login...");
    localStorage.removeItem("token");
    window.location.href = "/login?message=Session expired. Please log in again.";
  }
}

export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    const response = await fetch(`${BASE_URL}/health`, {
      method: "GET",
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return response.ok;
  } catch (error) {
    console.error('[API] Backend health check failed:', error);
    return false;
  }
}

export const getApiKeys = async () => {
  const response = await fetch(`${BASE_URL}/api/apikeys`, {
    headers: getAuthHeaders()
  });
  handleUnauthorized(response);
  if (!response.ok) {
    throw new Error("Failed to fetch API keys");
  }
  return response.json();
};

export const createApiKey = async (data: { name: string; model_id: string }) => {
  const response = await fetch(`${BASE_URL}/api/apikeys`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error("Failed to create API key");
  }
  return response.json();
};

export const deleteApiKey = async (apiKeyId: string) => {
  const response = await fetch(`${BASE_URL}/api/apikeys/${apiKeyId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to delete API key");
  }
  return;
};

export const getModels = async () => {
  const response = await fetch(`${BASE_URL}/api/models`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to fetch models");
  }
  return response.json();
};

export const getModel = async (modelId: string) => {
  const response = await fetch(`${BASE_URL}/api/models/${modelId}`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to fetch model");
  }
  return response.json();
};

export const downloadModel = async (modelId: string) => {
  const token = localStorage.getItem("token");
  const response = await fetch(`${BASE_URL}/api/models/${modelId}/download`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to download model");
  }

  const data = await response.json();

  // Create downloadable blob
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `model_${modelId}_${Date.now()}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
};

export const predictWithModel = async (modelId: string, inputData: any) => {
  const response = await fetch(`${BASE_URL}/api/models/${modelId}/predict`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(inputData),
  });

  handleUnauthorized(response);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to run prediction" }));
    throw new Error(error.detail || "Failed to run prediction");
  }
  return response.json();
};

export const deleteModel = async (modelId: string) => {
  const response = await fetch(`${BASE_URL}/api/models/${modelId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to delete model");
  }
  return response.json();
};

export const getModelSampleData = async (modelId: string, count: number = 3) => {
  const response = await fetch(`${BASE_URL}/api/models/${modelId}/sample-data?count=${count}`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to fetch sample data");
  }
  return response.json();
};

// Chat API
export const createChat = async (data: { title: string; model_id?: string; dataset_id?: string }) => {
  try {
    console.log('[API] Creating chat for training...', data);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout for chat creation

    const response = await fetch(`${BASE_URL}/api/chats`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to create chat" }));
      throw new Error(error.detail || `Failed to create chat: ${response.status}`);
    }

    const result = await response.json();
    console.log('[API] Chat created successfully:', result);
    return result;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timeout. Please check your connection and try again.');
    }
    console.error('[API] Create chat error:', error);
    throw error;
  }
};

export const getChats = async () => {
  const response = await fetch(`${BASE_URL}/api/chats`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to fetch chats");
  }
  return response.json();
};

export const getChat = async (chatId: string) => {
  const response = await fetch(`${BASE_URL}/api/chats/${chatId}`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to fetch chat");
  }
  return response.json();
};

export const updateChat = async (chatId: string, data: { title?: string; model_id?: string; dataset_id?: string }) => {
  const response = await fetch(`${BASE_URL}/api/chats/${chatId}`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to update chat" }));
    throw new Error(error.detail || "Failed to update chat");
  }
  return response.json();
};

export const deleteChat = async (chatId: string) => {
  console.log("Deleting chat with ID:", chatId);
  const response = await fetch(`${BASE_URL}/api/chats/${chatId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to delete chat" }));
    console.error("Delete chat failed:", error);
    throw new Error(error.detail || "Failed to delete chat");
  }
  console.log("Chat deleted successfully");
  return;
};

// Message API
export const getChatMessages = async (chatId: string) => {
  const response = await fetch(`${BASE_URL}/api/messages/chat/${chatId}`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error("Failed to fetch messages");
  }
  return response.json();
};

export const sendMessage = async (data: {
  chat_id: string;
  content: string;
  query_type?: string;
}) => {
  const response = await fetch(`${BASE_URL}/api/messages/chat`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      chat_id: data.chat_id,
      role: "user",
      content: data.content,
      query_type: data.query_type,
    }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to send message" }));
    throw new Error(error.detail || "Failed to send message");
  }
  return response.json();
};

// Gemini Agent API - Uses function calling to automatically find datasets and suggest models
export const sendMessageToAgent = async (data: {
  chat_id: string;
  content: string;
}) => {
  const response = await fetch(`${BASE_URL}/api/messages/agent`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      chat_id: data.chat_id,
      role: "user",
      content: data.content,
    }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to send message to agent" }));
    throw new Error(error.detail || "Failed to send message to agent");
  }
  return response.json();
};

// Dataset API
export const getDatasets = async () => {
  try {
    console.log('[API] Fetching datasets from:', `${BASE_URL}/api/datasets`);
    const headers = getAuthHeaders();
    console.log('[API] Using headers:', { ...headers, Authorization: headers.Authorization ? 'Bearer ***' : 'none' });

    const response = await fetch(`${BASE_URL}/api/datasets`, {
      headers: headers
    });

    console.log('[API] Response status:', response.status);
    console.log('[API] Response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[API] Error response:', errorText);
      throw new Error(`Failed to fetch datasets: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    console.log('[API] Datasets fetched successfully, count:', Array.isArray(data) ? data.length : 'not an array');
    console.log('[API] First dataset sample:', data && data.length > 0 ? {
      id: data[0].id,
      name: data[0].name,
      status: data[0].status,
      source: data[0].source,
      kaggleRef: data[0].kaggleRef,
      rowCount: data[0].rowCount,
    } : 'no datasets');
    console.log('[API] Full response data:', data);
    return data;
  } catch (error) {
    console.error('[API] Network error:', error);
    throw error;
  }
};

// Get single dataset with schema and sample data from Azure
export const getDataset = async (datasetId: string) => {
  try {
    console.log('[API] Fetching single dataset from:', `${BASE_URL}/api/datasets/${datasetId}`);
    const headers = getAuthHeaders();

    const response = await fetch(`${BASE_URL}/api/datasets/${datasetId}`, {
      headers: headers
    });

    console.log('[API] Response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[API] Error response:', errorText);

      if (response.status === 404) {
        throw new Error('Dataset not found');
      }

      throw new Error(`Failed to fetch dataset: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    console.log('[API] Dataset fetched successfully:', {
      id: data.id,
      name: data.name,
      status: data.status,
      hasSchema: !!data.schema,
      hasSampleData: !!data.sampleData,
      schemaLength: data.schema?.length || 0,
      sampleDataLength: data.sampleData?.length || 0,
    });

    return data;
  } catch (error) {
    console.error('[API] Failed to fetch dataset:', error);
    throw error;
  }
};

export const addDatasetFromKaggle = async (data: {
  dataset_ref: string;
  dataset_title: string;
  dataset_size: number;
  chat_id?: string;
}) => {
  const response = await fetch(`${BASE_URL}/api/datasets/add-from-kaggle`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to add dataset" }));
    throw new Error(error.detail || "Failed to add dataset from Kaggle");
  }
  return response.json();
};

export const addDatasetFromHuggingFace = async (data: {
  dataset_name: string;
  dataset_url: string;
  chat_id?: string;
}) => {
  const response = await fetch(`${BASE_URL}/api/datasets/add-from-huggingface`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to add dataset" }));
    throw new Error(error.detail || "Failed to add dataset from HuggingFace");
  }
  return response.json();
};

export const uploadDataset = async (
  formData: FormData,
  onProgress?: (progress: number) => void
) => {
  const token = localStorage.getItem("token");

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    console.log('[UPLOAD] Starting upload to:', `${BASE_URL}/api/datasets/upload`);

    // Track upload progress
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        const percentComplete = (e.loaded / e.total) * 100;
        console.log(`[UPLOAD] Progress: ${percentComplete.toFixed(2)}%`);
        onProgress(percentComplete);
      }
    });

    // Handle completion
    xhr.addEventListener('load', () => {
      console.log(`[UPLOAD] Request completed with status: ${xhr.status}`);
      console.log(`[UPLOAD] Response text:`, xhr.responseText);

      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          console.log('[UPLOAD] ✓ Upload successful:', response);
          resolve(response);
        } catch (error) {
          console.error('[UPLOAD] Failed to parse success response:', error);
          console.error('[UPLOAD] Raw response:', xhr.responseText);
          reject(new Error('Failed to parse server response'));
        }
      } else {
        // Error response
        console.error(`[UPLOAD] Upload failed with status ${xhr.status}`);
        try {
          const error = JSON.parse(xhr.responseText);
          console.error('[UPLOAD] Error details:', error);
          const errorMessage = error.detail || `Upload failed with status ${xhr.status}`;
          reject(new Error(errorMessage));
        } catch (parseError) {
          console.error('[UPLOAD] Failed to parse error response:', parseError);
          console.error('[UPLOAD] Raw error response:', xhr.responseText);
          reject(new Error(`Upload failed: ${xhr.status} - ${xhr.statusText || 'Unknown error'}`));
        }
      }
    });

    // Handle errors
    xhr.addEventListener('error', (e) => {
      console.error('[UPLOAD] Network error:', e);
      reject(new Error('Network error during upload. Please check your connection and try again.'));
    });

    xhr.addEventListener('abort', () => {
      console.warn('[UPLOAD] Upload cancelled');
      reject(new Error('Upload cancelled'));
    });

    // Handle timeout
    xhr.addEventListener('timeout', () => {
      console.error('[UPLOAD] Request timeout');
      reject(new Error('Upload timeout. The file may be too large or the connection is slow.'));
    });

    // Open and send request
    xhr.open('POST', `${BASE_URL}/api/datasets/upload`);

    // Set timeout to 5 minutes for large files
    xhr.timeout = 300000; // 5 minutes

    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }

    console.log('[UPLOAD] Sending request...');
    xhr.send(formData);
  });
};

export const deleteDataset = async (datasetId: string) => {
  console.log("Deleting dataset with ID:", datasetId);
  const response = await fetch(`${BASE_URL}/api/datasets/${datasetId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to delete dataset" }));
    console.error("Delete failed:", error);
    throw new Error(error.detail || "Failed to delete dataset");
  }
  console.log("Dataset deleted successfully");
  return;
};

export const inspectDataset = async (datasetId: string, userQuery?: string) => {
  console.log("Inspecting dataset with ID:", datasetId);
  const response = await fetch(`${BASE_URL}/api/datasets/inspect`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      dataset_id: datasetId,
      user_query: userQuery,
    }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to inspect dataset" }));
    console.error("Inspect failed:", error);
    throw new Error(error.detail || "Failed to inspect dataset");
  }
  console.log("Dataset inspected successfully");
  return response.json();
};

export const checkKaggleStatus = async () => {
  const response = await fetch(`${BASE_URL}/api/kaggle/status`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to check Kaggle status" }));
    throw new Error(error.detail || "Failed to check Kaggle status");
  }
  return response.json();
};

export const updateDataset = async (datasetId: string, data: { target_column?: string }) => {
  const response = await fetch(`${BASE_URL}/api/datasets/${datasetId}`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to update dataset" }));
    throw new Error(error.detail || "Failed to update dataset");
  }
  return response.json();
};

export const downloadDataset = async (datasetId: string, source: "Kaggle" | "HuggingFace") => {
  const response = await fetch(`${BASE_URL}/api/datasets/download-dataset`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      dataset_id: datasetId,
      source: source,
    }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to download dataset" }));
    throw new Error(error.detail || "Failed to download dataset");
  }
  return response.json();
};

export const downloadDatasetWithProgress = (
  datasetId: string,
  source: "Kaggle" | "HuggingFace",
  onProgress: (progress: number, message: string) => void,
  onComplete: (result: any) => void,
  onError: (error: string) => void
) => {
  const token = localStorage.getItem("token");
  const url = `${BASE_URL}/api/datasets/download-progress/${encodeURIComponent(datasetId)}?source=${source}`;

  const eventSource = new EventSource(
    token ? `${url}&token=${token}` : url
  );

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      if (data.status === "error") {
        eventSource.close();
        onError(data.message || "Download failed");
        return;
      }

      if (data.status === "completed") {
        eventSource.close();
        onProgress(100, "Download complete!");
        onComplete(data.result || { success: true });
        return;
      }

      // Report progress
      onProgress(data.progress || 0, data.message || "Downloading...");
    } catch (error) {
      console.error("Error parsing SSE data:", error);
    }
  };

  eventSource.onerror = (error) => {
    console.error("SSE connection error:", error);
    eventSource.close();
    onError("Connection error during download");
  };

  // Return cleanup function
  return () => eventSource.close();
};

// Model Search & Selection
export interface ModelSearchFilters {
  task?: string;
  language?: string;
  minDownloads?: number;
  maxSize?: string;
  sortBy?: "relevance" | "downloads" | "recent";
}

export const searchModels = async (query: string, filters?: ModelSearchFilters) => {
  const params = new URLSearchParams({ query });
  if (filters?.task) params.append("task", filters.task);
  if (filters?.language) params.append("language", filters.language);
  if (filters?.minDownloads) params.append("min_downloads", filters.minDownloads.toString());
  if (filters?.maxSize) params.append("max_size", filters.maxSize);
  if (filters?.sortBy) params.append("sort_by", filters.sortBy);

  const response = await fetch(`${BASE_URL}/api/models/search?${params}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to search models");
  }
  return response.json();
};

export const getModelDetails = async (modelId: string) => {
  const response = await fetch(`${BASE_URL}/api/models/${encodeURIComponent(modelId)}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch model details");
  }
  return response.json();
};

export const compareModels = async (modelIds: string[]) => {
  const response = await fetch(`${BASE_URL}/api/models/compare`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ model_ids: modelIds }),
  });
  if (!response.ok) {
    throw new Error("Failed to compare models");
  }
  return response.json();
};

// Training Jobs
export interface CreateTrainingJobData {
  model_id: string;
  dataset_id: string;
  hyperparameters?: {
    learning_rate?: number;
    epochs?: number;
    batch_size?: number;
    [key: string]: any;
  };
  job_name?: string;
}

export const createTrainingJob = async (data: CreateTrainingJobData) => {
  const response = await fetch(`${BASE_URL}/api/training/jobs`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to create training job" }));
    throw new Error(error.detail || "Failed to create training job");
  }
  return response.json();
};

export const getTrainingJobs = async () => {
  const response = await fetch(`${BASE_URL}/api/training/jobs`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch training jobs");
  }
  return response.json();
};

export const getTrainingJob = async (jobId: string) => {
  const response = await fetch(`${BASE_URL}/api/training/jobs/${jobId}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch training job");
  }
  return response.json();
};

export const cancelTrainingJob = async (jobId: string) => {
  const response = await fetch(`${BASE_URL}/api/training/jobs/${jobId}/cancel`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to cancel training job");
  }
  return response.json();
};

export const getTrainingLogs = async (jobId: string) => {
  const response = await fetch(`${BASE_URL}/api/training/jobs/${jobId}/logs`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch training logs");
  }
  return response.json();
};

// Pre-built Models
export const getPrebuiltModels = async () => {
  const response = await fetch(`${BASE_URL}/api/prebuilt-models`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch pre-built models");
  }
  return response.json();
};

export const deployPrebuiltModel = async (modelId: string, deploymentName?: string) => {
  const response = await fetch(`${BASE_URL}/api/prebuilt-models/${modelId}/deploy`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ deployment_name: deploymentName }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to deploy model" }));
    throw new Error(error.detail || "Failed to deploy pre-built model");
  }
  return response.json();
};

export const testPrebuiltModel = async (modelId: string, input: any) => {
  const response = await fetch(`${BASE_URL}/api/prebuilt-models/${modelId}/test`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ input }),
  });
  if (!response.ok) {
    throw new Error("Failed to test model");
  }
  return response.json();
};

// Deployments
export interface CreateDeploymentData {
  model_id: string;
  deployment_name: string;
  instance_type?: string;
  auto_scaling?: boolean;
  min_instances?: number;
  max_instances?: number;
}

export const getDeployments = async () => {
  const response = await fetch(`${BASE_URL}/api/deployments`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch deployments");
  }
  return response.json();
};

export const createDeployment = async (data: CreateDeploymentData) => {
  const response = await fetch(`${BASE_URL}/api/deployments`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to create deployment" }));
    throw new Error(error.detail || "Failed to create deployment");
  }
  return response.json();
};

export const getDeployment = async (deploymentId: string) => {
  const response = await fetch(`${BASE_URL}/api/deployments/${deploymentId}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch deployment");
  }
  return response.json();
};

export const deleteDeployment = async (deploymentId: string) => {
  const response = await fetch(`${BASE_URL}/api/deployments/${deploymentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to delete deployment");
  }
  return;
};

export const toggleDeployment = async (deploymentId: string, action: "start" | "stop") => {
  const response = await fetch(`${BASE_URL}/api/deployments/${deploymentId}/${action}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to ${action} deployment`);
  }
  return response.json();
};

export const predictWithDeployment = async (deploymentId: string, input: any) => {
  const response = await fetch(`${BASE_URL}/api/deployments/${deploymentId}/predict`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ input }),
  });
  if (!response.ok) {
    throw new Error("Failed to make prediction");
  }
  return response.json();
};

export const getDeploymentMetrics = async (deploymentId: string) => {
  const response = await fetch(`${BASE_URL}/api/deployments/${deploymentId}/metrics`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch deployment metrics");
  }
  return response.json();
};

// Direct Access API
export const requestDirectAccess = async (data: {
  task: string;
  subtask?: string;
  usage: string;
  language?: string;
  priority: string;
}) => {
  const response = await fetch(`${BASE_URL}/api/direct-access`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to request direct access" }));
    throw new Error(error.detail || "Failed to request direct access");
  }
  return response.json();
};

export const getDirectAccessModels = async (filters?: {
  task?: string;
  priority?: string;
  language?: string;
}) => {
  const params = new URLSearchParams(filters as any);
  const response = await fetch(`${BASE_URL}/api/direct-access/models?${params}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch direct access models");
  }
  return response.json();
};

export const getDirectAccessKeys = async () => {
  const response = await fetch(`${BASE_URL}/api/direct-access/keys`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch direct access keys");
  }
  return response.json();
};

export const revokeDirectAccessKey = async (keyId: string) => {
  const response = await fetch(`${BASE_URL}/api/direct-access/keys/${keyId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to revoke API key");
  }
  return response.json();
};

export const testDirectAccessAPI = async (apiKey: string, text: string, endpoint?: string) => {
  const url = endpoint || `${BASE_URL}/v1/sentiment/vader`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "API test failed" }));
    throw new Error(error.detail || "API test failed");
  }
  return response.json();
};

export const getUsageStatistics = async (timeframe: string = '30d') => {
  const response = await fetch(`${BASE_URL}/api/dashboard/usage?timeframe=${timeframe}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch usage statistics");
  }
  return response.json();
};

export const getCostBreakdown = async () => {
  const response = await fetch(`${BASE_URL}/api/dashboard/costs`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch cost breakdown");
  }
  return response.json();
};

// ========================================
// Data Labeling API
// ========================================

/**
 * Generate labels for uploaded files using AI
 * Uses XMLHttpRequest for progress tracking
 */
export const generateLabels = async (
  files: File[],
  config: LabelingConfig,
  onProgress?: (progress: number) => void
): Promise<LabelingResponse> => {
  return new Promise((resolve, reject) => {
    const formData = new FormData();

    // Append all files
    files.forEach((file) => {
      formData.append("files", file);
    });

    // Append config as JSON string
    formData.append("config", JSON.stringify(config));

    // Create XMLHttpRequest for progress tracking
    const xhr = new XMLHttpRequest();

    // Track upload progress
    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable && onProgress) {
        const progress = (e.loaded / e.total) * 100;
        onProgress(progress);
      }
    });

    // Handle completion
    xhr.addEventListener("load", () => {
      if (xhr.status === 200) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch (e) {
          reject(new Error("Failed to parse response"));
        }
      } else if (xhr.status === 401) {
        handleUnauthorized({ status: 401 } as Response);
        reject(new Error("Unauthorized"));
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || "Labeling failed"));
        } catch (e) {
          reject(new Error(`Request failed with status ${xhr.status}`));
        }
      }
    });

    // Handle errors
    xhr.addEventListener("error", () => {
      reject(new Error("Network error occurred"));
    });

    // Handle timeout
    xhr.addEventListener("timeout", () => {
      reject(new Error("Request timed out"));
    });

    // Open and send request
    xhr.open("POST", `${BASE_URL}/api/labeling/generate-labels`);

    // Set auth header
    const token = localStorage.getItem("token");
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    // Set timeout (5 minutes for large files)
    xhr.timeout = 300000;

    // Send request
    xhr.send(formData);
  });
};

/**
 * Refine labels based on user feedback
 */
export const refineLabels = async (
  labels: any[],
  feedback: string
): Promise<any> => {
  const response = await fetch(`${BASE_URL}/api/labeling/refine-analysis`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ labels, feedback }),
  });

  handleUnauthorized(response);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to refine labels" }));
    throw new Error(error.detail || "Failed to refine labels");
  }

  return response.json();
};