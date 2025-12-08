import { User, Token } from "@/types/api";
import { getApiUrl } from "./env";

const BASE_URL = getApiUrl();

interface LoginCredentials {
  email: string;
  password: string;
}

interface RegisterData {
  email: string;
  name: string;
  password: string;
}

interface SendOTPData {
  email: string;
  purpose?: string;
}

interface RegisterWithOTPData {
  email: string;
  name: string;
  password: string;
  otp: string;
}

export const login = async (credentials: LoginCredentials): Promise<Token> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(`${BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(credentials),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to login" }));
      throw new Error(error.detail || "Failed to login");
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Connection timeout - backend server not responding');
    }
    throw error;
  }
};

export const sendOTP = async (data: SendOTPData): Promise<{ message: string; email: string; expires_in: number }> => {
  const response = await fetch(`${BASE_URL}/api/auth/send-otp`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email: data.email, purpose: data.purpose || "signup" }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to send OTP" }));
    throw new Error(error.detail || "Failed to send OTP");
  }

  return response.json();
};

export const registerWithOTP = async (data: RegisterWithOTPData): Promise<User> => {
  const response = await fetch(`${BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to register" }));

    // Handle validation errors with detailed messages
    if (error.detail && Array.isArray(error.detail)) {
      const errorMessages = error.detail.map((err: any) => err.msg || err.message).join(", ");
      throw new Error(errorMessages);
    }

    throw new Error(error.detail || "Failed to register");
  }

  return response.json();
};

export const register = async (data: RegisterData): Promise<User> => {
  // Deprecated: Use registerWithOTP for OTP flow
  // Use direct registration for development/testing
  // For production OTP flow, use: /api/auth/send-otp then /api/auth/register
  const response = await fetch(`${BASE_URL}/api/auth/register-direct`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to register" }));

    // Handle validation errors with detailed messages
    if (error.detail && Array.isArray(error.detail)) {
      const errorMessages = error.detail.map((err: any) => err.msg || err.message).join(", ");
      throw new Error(errorMessages);
    }

    throw new Error(error.detail || "Failed to register");
  }

  return response.json();
};

export const getCurrentUser = async (token: string): Promise<User> => {
  const response = await fetch(`${BASE_URL}/api/auth/me`, {
    headers: {
      "Authorization": `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch user data");
  }

  return response.json();
};

export const googleLogin = async (token: string): Promise<Token> => {
  // Add timeout to prevent hanging
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

  try {
    const response = await fetch(`${BASE_URL}/api/auth/google`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ token }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Failed to authenticate with Google" }));
      throw new Error(error.detail || "Failed to authenticate with Google");
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Connection timeout - backend server may not be running. Please check if the backend is running on http://localhost:8000');
    }
    throw error;
  }
};

export const requestPasswordReset = async (email: string): Promise<{ message: string; email: string }> => {
  const response = await fetch(`${BASE_URL}/api/auth/password-reset/request`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to request password reset" }));
    throw new Error(error.detail || "Failed to request password reset");
  }

  return response.json();
};

export const completePasswordReset = async (data: {
  email: string;
  otp: string;
  new_password: string;
}): Promise<{ message: string }> => {
  const response = await fetch(`${BASE_URL}/api/auth/password-reset/complete`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to reset password" }));
    throw new Error(error.detail || "Failed to reset password");
  }

  return response.json();
};
