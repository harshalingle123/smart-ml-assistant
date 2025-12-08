import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useMutation } from "@tanstack/react-query";
import { Link, useLocation } from "wouter";
import { GoogleLogin, CredentialResponse } from "@react-oauth/google";
import { sendOTP, registerWithOTP, googleLogin } from "@/lib/auth";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { AlertCircle, Eye, EyeOff, ArrowRight, Mail, CheckCircle } from "lucide-react";
import { useState } from "react";
import { ChatPreview } from "@/components/auth/ChatPreview";

const formSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  confirmPassword: z.string().min(6, "Password must be at least 6 characters"),
  otp: z.string().optional(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

export default function Register() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const { login: loginUser } = useAuth();
  const [googleError, setGoogleError] = useState<string | null>(null);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [step, setStep] = useState<1 | 2>(1);
  const [otpSent, setOtpSent] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);

  const sendOTPMutation = useMutation({
    mutationFn: sendOTP,
    onSuccess: () => {
      setOtpSent(true);
      setStep(2);
      setResendTimer(60);
      const interval = setInterval(() => {
        setResendTimer((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      toast({
        title: "OTP sent successfully!",
        description: "Please check your email for the verification code.",
      });
    },
  });

  const mutation = useMutation({
    mutationFn: registerWithOTP,
    onSuccess: () => {
      toast({
        title: "Account created successfully!",
        description: "You can now sign in with your credentials.",
      });
      setLocation("/login");
    },
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
      otp: "",
    },
  });

  function onSendOTP() {
    const email = form.getValues("email");
    const name = form.getValues("name");
    const password = form.getValues("password");
    const confirmPassword = form.getValues("confirmPassword");

    // Validate required fields
    if (!email || !name || !password || !confirmPassword) {
      toast({
        title: "Missing information",
        description: "Please fill in all fields before sending OTP.",
        variant: "destructive",
      });
      return;
    }

    if (password !== confirmPassword) {
      toast({
        title: "Passwords don't match",
        description: "Please make sure your passwords match.",
        variant: "destructive",
      });
      return;
    }

    if (password.length < 6) {
      toast({
        title: "Password too short",
        description: "Password must be at least 6 characters.",
        variant: "destructive",
      });
      return;
    }

    sendOTPMutation.mutate({ email, purpose: "signup" });
  }

  function onSubmit(values: z.infer<typeof formSchema>) {
    if (step === 1) {
      onSendOTP();
      return;
    }

    const { confirmPassword, ...registerData } = values;
    if (!registerData.otp) {
      toast({
        title: "OTP required",
        description: "Please enter the OTP sent to your email.",
        variant: "destructive",
      });
      return;
    }
    mutation.mutate(registerData as any);
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
      setLocation("/");
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
      {/* Left Section - Registration Form */}
      <div className="flex-1 flex items-center justify-center p-8 lg:p-16">
        <div className="w-full max-w-[450px] animate-[fadeIn_0.8s_ease-out]">
          <h1 className="text-5xl font-bold text-white mb-4 leading-tight">
            Start building in minutes
          </h1>
          <p className="text-lg text-gray-400 mb-10 leading-relaxed">
            Create your account and deploy your first ML model today.
          </p>

          {/* Step Indicator */}
          {otpSent && (
            <div className="mb-6 p-4 bg-green-500/10 border border-green-500/50 rounded-lg">
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle className="h-5 w-5" />
                <span className="text-sm font-medium">OTP sent to your email!</span>
              </div>
              <p className="text-xs text-green-400/80 mt-1">Please enter the 6-digit code below.</p>
            </div>
          )}

          {(mutation.isError || sendOTPMutation.isError || googleError) && (
            <Alert className="mb-6 bg-red-500/10 border-red-500/50 text-red-400">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {googleError || mutation.error?.message || sendOTPMutation.error?.message || "Failed to create account. Please try again."}
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Full Name Field */}
            <div>
              <label htmlFor="name" className="block mb-2 text-sm font-medium text-white">
                Full Name
              </label>
              <input
                id="name"
                type="text"
                placeholder="John Doe"
                autoComplete="name"
                disabled={step === 2}
                {...form.register("name")}
                className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-lg text-white text-[15px] placeholder:text-white/40 transition-all duration-300 focus:outline-none focus:border-[#4169ff] focus:bg-white/10 focus:ring-4 focus:ring-[#4169ff]/10 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              {form.formState.errors.name && (
                <p className="mt-2 text-sm text-red-400">{form.formState.errors.name.message}</p>
              )}
            </div>

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
                disabled={step === 2}
                {...form.register("email")}
                className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-lg text-white text-[15px] placeholder:text-white/40 transition-all duration-300 focus:outline-none focus:border-[#4169ff] focus:bg-white/10 focus:ring-4 focus:ring-[#4169ff]/10 disabled:opacity-50 disabled:cursor-not-allowed"
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
                  placeholder="Create a password"
                  autoComplete="new-password"
                  disabled={step === 2}
                  {...form.register("password")}
                  className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-lg text-white text-[15px] placeholder:text-white/40 transition-all duration-300 focus:outline-none focus:border-[#4169ff] focus:bg-white/10 focus:ring-4 focus:ring-[#4169ff]/10 pr-12 disabled:opacity-50 disabled:cursor-not-allowed"
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
                <span className="text-[13px] text-white/50">
                  Minimum 6 characters
                </span>
              </div>
            </div>

            {/* Confirm Password Field */}
            <div>
              <label htmlFor="confirmPassword" className="block mb-2 text-sm font-medium text-white">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="Confirm your password"
                  autoComplete="new-password"
                  disabled={step === 2}
                  {...form.register("confirmPassword")}
                  className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-lg text-white text-[15px] placeholder:text-white/40 transition-all duration-300 focus:outline-none focus:border-[#4169ff] focus:bg-white/10 focus:ring-4 focus:ring-[#4169ff]/10 pr-12 disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white/50 hover:text-[#4169ff] transition-colors duration-300"
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {form.formState.errors.confirmPassword && (
                <p className="mt-2 text-sm text-red-400">{form.formState.errors.confirmPassword.message}</p>
              )}
            </div>

            {/* OTP Field - Only shown in step 2 */}
            {step === 2 && (
              <div>
                <label htmlFor="otp" className="block mb-2 text-sm font-medium text-white">
                  Verification Code
                </label>
                <input
                  id="otp"
                  type="text"
                  placeholder="Enter 6-digit code"
                  maxLength={6}
                  {...form.register("otp")}
                  className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-lg text-white text-[15px] placeholder:text-white/40 transition-all duration-300 focus:outline-none focus:border-[#4169ff] focus:bg-white/10 focus:ring-4 focus:ring-[#4169ff]/10 text-center tracking-widest font-mono text-lg"
                />
                {form.formState.errors.otp && (
                  <p className="mt-2 text-sm text-red-400">{form.formState.errors.otp.message}</p>
                )}
                <div className="flex justify-between items-center mt-2">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="text-[13px] text-white/50 hover:text-[#4169ff] transition-colors"
                  >
                    Change email
                  </button>
                  {resendTimer > 0 ? (
                    <span className="text-[13px] text-white/50">
                      Resend in {resendTimer}s
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={onSendOTP}
                      disabled={sendOTPMutation.isPending}
                      className="text-[13px] text-[#4169ff] hover:underline disabled:opacity-50"
                    >
                      Resend OTP
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={mutation.isPending || sendOTPMutation.isPending}
              className="w-full mt-8 px-4 py-4 bg-[#4169ff] text-white text-base font-semibold rounded-lg transition-all duration-300 hover:bg-[#3557e0] hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 flex items-center justify-center gap-2"
            >
              {step === 1 ? (
                <>
                  {sendOTPMutation.isPending ? "Sending OTP..." : "Send Verification Code"}
                  {!sendOTPMutation.isPending && <Mail size={18} />}
                </>
              ) : (
                <>
                  {mutation.isPending ? "Creating account..." : "Complete Registration"}
                  {!mutation.isPending && <ArrowRight size={18} />}
                </>
              )}
            </button>
          </form>

          {/* Divider - Only show in step 1 */}
          {step === 1 && (
            <>
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
                    width="400"
                  />
                </div>

                {isGoogleLoading && (
                  <div className="flex items-center justify-center py-2">
                    <div className="w-4 h-4 border-2 border-[#4169ff] border-t-transparent rounded-full animate-spin"></div>
                    <span className="ml-2 text-sm text-white/60">Signing in with Google...</span>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Sign In Link */}
          <p className="text-center mt-8 text-sm text-white/60">
            Already have an AutoML account?
            <Link href="/login" className="ml-1 text-[#4169ff] font-semibold hover:underline">
              Sign In
            </Link>
          </p>
        </div>
      </div>

      {/* Right Section - Chat Preview */}
      <div className="hidden lg:flex lg:flex-1 relative overflow-hidden bg-gradient-to-br from-[#1a1a2e] to-[#16213e] items-center justify-center p-16">
        <ChatPreview />
      </div>
    </div>
  );
}
