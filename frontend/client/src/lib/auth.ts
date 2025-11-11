import { User, Token } from "@/types/api";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface LoginCredentials {
  email: string;
  password: string;
}

interface RegisterData {
  email: string;
  name: string;
  password: string;
}

export const login = async (credentials: LoginCredentials): Promise<Token> => {
  const response = await fetch(`${BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to login" }));
    throw new Error(error.detail || "Failed to login");
  }

  return response.json();
};

export const register = async (data: RegisterData): Promise<User> => {
  const response = await fetch(`${BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to register" }));
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
  const response = await fetch(`${BASE_URL}/api/auth/google`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ token }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to authenticate with Google" }));
    throw new Error(error.detail || "Failed to authenticate with Google");
  }

  return response.json();
};
