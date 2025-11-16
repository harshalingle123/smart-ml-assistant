import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useMutation } from "@tanstack/react-query";
import { Link, useLocation } from "wouter";
import { GoogleLogin, CredentialResponse } from "@react-oauth/google";
import { login, googleLogin } from "@/lib/auth";
import { useAuth } from "@/contexts/AuthContext";
import { AlertCircle, Eye, EyeOff, ArrowRight } from "lucide-react";
import { useState, useEffect } from "react";
import { ChatPreview } from "@/components/auth/ChatPreview";

const formSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
});

export default function Login() {
  const [, setLocation] = useLocation();
  const { login: loginUser, isAuthenticated } = useAuth();
  const [googleError, setGoogleError] = useState<string | null>(null);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [loginSuccess, setLoginSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Navigate to dashboard after successful authentication
  useEffect(() => {
    if (loginSuccess && isAuthenticated) {
      setLocation("/");
    }
  }, [loginSuccess, isAuthenticated, setLocation]);

  const mutation = useMutation({
    mutationFn: login,
    onSuccess: async (data) => {
      try {
        await loginUser(data.access_token);
        setLoginSuccess(true);
      } catch (error) {
        console.error("Login failed:", error);
      }
    },
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    mutation.mutate(values);
  }

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) {
      setGoogleError("No credential received from Google");
      return;
    }

    setIsGoogleLoading(true);
    setGoogleError(null);

    try {
      const data = await googleLogin(credentialResponse.credential);
      await loginUser(data.access_token);
      setLoginSuccess(true);
    } catch (error) {
      setGoogleError(error instanceof Error ? error.message : "Failed to authenticate with Google");
    } finally {
      setIsGoogleLoading(false);
    }
  };

  const handleGoogleError = () => {
    setGoogleError("Google Sign-In failed. Please try again.");
  };

  return (
    <div className="flex min-h-screen bg-black">
      {/* Left Section - Chat Preview */}
      <div className="hidden lg:flex lg:flex-1 relative overflow-hidden bg-gradient-to-br from-[#0f0f23] to-[#1a1a2e] items-center justify-center p-16">
        <ChatPreview />
      </div>

      {/* Right Section - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 lg:p-16">
        <div className="w-full max-w-[450px] animate-[fadeIn_0.8s_ease-out]">
          <h1 className="text-5xl font-bold text-white mb-4 leading-tight">
            Welcome back
          </h1>
          <p className="text-lg text-gray-400 mb-10 leading-relaxed">
            Sign in to continue building amazing ML models.
          </p>

          {(mutation.isError || googleError) && (
            <Alert className="mb-6 bg-red-500/10 border-red-500/50 text-red-400">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {googleError || mutation.error?.message || "Failed to sign in. Please check your credentials."}
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block mb-2 text-sm font-medium text-white">
                Email address
              </label>
              <input
                id="email"
                type="email"
                placeholder="your@email.com"
                autoComplete="email"
                {...form.register("email")}
                className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-lg text-white text-[15px] placeholder:text-white/40 transition-all duration-300 focus:outline-none focus:border-[#4169ff] focus:bg-white/10 focus:ring-4 focus:ring-[#4169ff]/10"
              />
              {form.formState.errors.email && (
                <p className="mt-2 text-sm text-red-400">{form.formState.errors.email.message}</p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block mb-2 text-sm font-medium text-white">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter password"
                  autoComplete="current-password"
                  {...form.register("password")}
                  className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-lg text-white text-[15px] placeholder:text-white/40 transition-all duration-300 focus:outline-none focus:border-[#4169ff] focus:bg-white/10 focus:ring-4 focus:ring-[#4169ff]/10 pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white/50 hover:text-[#4169ff] transition-colors duration-300"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {form.formState.errors.password && (
                <p className="mt-2 text-sm text-red-400">{form.formState.errors.password.message}</p>
              )}
              <div className="text-right mt-2">
                <a href="#" className="text-[13px] text-[#4169ff] hover:opacity-80 transition-opacity">
                  Forgot password?
                </a>
              </div>
            </div>

            {/* Sign In Button */}
            <button
              type="submit"
              disabled={mutation.isPending}
              className="w-full mt-8 px-4 py-4 bg-[#4169ff] text-white text-base font-semibold rounded-lg transition-all duration-300 hover:bg-[#3557e0] hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 flex items-center justify-center gap-2"
            >
              {mutation.isPending ? "Signing in..." : "Sign In"}
              {!mutation.isPending && <ArrowRight size={18} />}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10"></div>
            </div>
            <div className="relative flex justify-center">
              <span className="px-4 text-[13px] text-white/50 bg-black uppercase tracking-wide">
                or continue with
              </span>
            </div>
          </div>

          {/* Google Sign In */}
          <div className="space-y-3">
            <div className="flex items-center justify-center">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={handleGoogleError}
                text="continue_with"
                theme="filled_black"
                size="large"
                width="100%"
              />
            </div>

            {isGoogleLoading && (
              <div className="flex items-center justify-center py-2">
                <div className="w-4 h-4 border-2 border-[#4169ff] border-t-transparent rounded-full animate-spin"></div>
                <span className="ml-2 text-sm text-white/60">Signing in with Google...</span>
              </div>
            )}
          </div>

          {/* Sign Up Link */}
          <p className="text-center mt-8 text-sm text-white/60">
            New to AutoML?
            <Link href="/register" className="ml-1 text-[#4169ff] font-semibold hover:underline">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
