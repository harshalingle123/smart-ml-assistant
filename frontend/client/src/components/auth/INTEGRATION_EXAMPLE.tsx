/**
 * Integration Example - Authentication Components
 *
 * This file demonstrates how to integrate the auth components into your application.
 * DO NOT import this file - it's for reference only.
 */

// Example 1: Basic React Router Integration
// =========================================

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage, RegisterPage } from '@/components/auth';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/signin" element={<LoginPage />} />
        <Route path="/signup" element={<RegisterPage />} />
        <Route path="/" element={<Navigate to="/signin" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

// Example 2: With Authentication Context
// ======================================

import { createContext, useContext, useState, ReactNode } from 'react';
import { LoginPage, RegisterPage } from '@/components/auth';

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = async (email: string, password: string) => {
    // Replace with actual API call
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) throw new Error('Login failed');

    const data = await response.json();
    setUser(data.user);
    setIsAuthenticated(true);
    localStorage.setItem('token', data.token);
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('token');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Example 3: Modified LoginPage with Real Auth
// ============================================

import { useState, useCallback, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthLayout, ChatPreview, SocialButton } from '@/components/auth';

function CustomLoginPage() {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = useCallback(async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Login failed');
      }

      const data = await response.json();
      localStorage.setItem('token', data.token);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [formData, navigate]);

  const handleGoogleLogin = useCallback(() => {
    window.location.href = `${import.meta.env.VITE_API_URL}/auth/google`;
  }, []);

  return (
    <AuthLayout reverse={false} chatPreview={<ChatPreview />}>
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Rest of the form... */}
      </form>
    </AuthLayout>
  );
}

// Example 4: Protected Route Component
// ====================================

import { Navigate, Outlet } from 'react-router-dom';

function ProtectedRoute() {
  const token = localStorage.getItem('token');
  const isAuthenticated = !!token; // In production, verify token validity

  if (!isAuthenticated) {
    return <Navigate to="/signin" replace />;
  }

  return <Outlet />;
}

// Example 5: Full App Structure
// =============================

function FullApp() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/signin" element={<LoginPage />} />
          <Route path="/signup" element={<RegisterPage />} />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/models" element={<Models />} />
            <Route path="/datasets" element={<Datasets />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/signin" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

// Example 6: Environment Variables Setup
// ======================================

// Create a .env file in your frontend root:
/*
VITE_API_URL=http://localhost:3000
VITE_GOOGLE_CLIENT_ID=your-google-client-id
*/

// Access in your code:
const API_URL = import.meta.env.VITE_API_URL;
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

// Example 7: Toast Notifications for Errors
// =========================================

import { toast } from 'sonner'; // or your preferred toast library

const handleSubmitWithToast = useCallback(async (e: FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  setIsLoading(true);

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });

    if (!response.ok) throw new Error('Login failed');

    const data = await response.json();
    localStorage.setItem('token', data.token);
    toast.success('Welcome back!');
    navigate('/dashboard');
  } catch (err) {
    toast.error('Invalid email or password');
  } finally {
    setIsLoading(false);
  }
}, [formData, navigate]);
