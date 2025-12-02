export const isProduction = () => {
  return import.meta.env.PROD ||
         window.location.hostname !== 'localhost';
};

export const getApiUrl = () => {
  // If VITE_API_URL is explicitly set, use it
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // Auto-detect based on current location
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;

    // Production detection: if not localhost, construct backend URL
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      // Common production patterns
      if (hostname.includes('netlify.app') || hostname.includes('vercel.app')) {
        // Frontend on Netlify/Vercel, backend on Render
        return 'https://smart-ml-backend.onrender.com';
      } else if (hostname.includes('onrender.com')) {
        // Both on Render, use current protocol and host
        return `${protocol}//${hostname}`;
      } else if (hostname.includes('darshix.com')) {
        // Custom domain pointing to backend
        return 'https://smart-ml-backend.onrender.com';
      } else {
        // Other hosting - assume backend on same origin
        return `${protocol}//${hostname}`;
      }
    }
  }

  // Default to localhost for development
  return 'http://localhost:8000';
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
