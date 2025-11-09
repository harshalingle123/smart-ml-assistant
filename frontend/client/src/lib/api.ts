const BASE_URL = "http://localhost:8000";

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

export const getApiKeys = async () => {
  const response = await fetch(`${BASE_URL}/api/apikeys`, {
    headers: getAuthHeaders()
  });
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