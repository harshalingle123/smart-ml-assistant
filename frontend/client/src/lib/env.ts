export const isProduction = () => {
  return import.meta.env.PROD ||
         window.location.hostname !== 'localhost';
};

export const getApiUrl = () => {
  return import.meta.env.VITE_API_URL || 'http://localhost:8000';
};

export const isBackendReachable = async (): Promise<boolean> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${getApiUrl()}/health`, {
      method: 'GET',
      mode: 'cors',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return response.ok;
  } catch {
    return false;
  }
};
