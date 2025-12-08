import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useMutation } from "@tanstack/react-query";
import { Link, useLocation } from "wouter";
import { requestPasswordReset, completePasswordReset } from "@/lib/auth";
import { useToast } from "@/hooks/use-toast";
import { AlertCircle, ArrowRight, Mail, CheckCircle, Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { ChatPreview } from "@/components/auth/ChatPreview";

const emailSchema = z.object({
  email: z.string().email("Invalid email address"),
});

const resetSchema = z.object({
  email: z.string().email("Invalid email address"),
  otp: z.string().min(6, "OTP must be 6 digits").max(6, "OTP must be 6 digits"),
  new_password: z.string().min(6, "Password must be at least 6 characters"),
  confirm_password: z.string().min(6, "Password must be at least 6 characters"),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

export default function ForgotPassword() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [step, setStep] = useState<1 | 2>(1);
  const [otpSent, setOtpSent] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);
  const [email, setEmail] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const requestMutation = useMutation({
    mutationFn: requestPasswordReset,
    onSuccess: (data) => {
      setEmail(data.email);
      resetForm.setValue("email", data.email);
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
        title: "Reset code sent!",
        description: "Please check your email for the password reset code.",
      });
    },
  });

  const resetMutation = useMutation({
    mutationFn: completePasswordReset,
    onSuccess: () => {
      toast({
        title: "Password reset successfully!",
        description: "You can now sign in with your new password.",
      });
      setLocation("/login");
    },
  });

  const emailForm = useForm<z.infer<typeof emailSchema>>({
    resolver: zodResolver(emailSchema),
    defaultValues: {
      email: "",
    },
  });

  const resetForm = useForm<z.infer<typeof resetSchema>>({
    resolver: zodResolver(resetSchema),
    defaultValues: {
      email: "",
      otp: "",
      new_password: "",
      confirm_password: "",
    },
  });

  function onRequestReset(values: z.infer<typeof emailSchema>) {
    requestMutation.mutate(values.email);
  }

  function onCompleteReset(values: z.infer<typeof resetSchema>) {
    resetMutation.mutate({
      email: values.email,
      otp: values.otp,
      new_password: values.new_password,
    });
  }

  function onResendOTP() {
    if (email) {
      requestMutation.mutate(email);
    }
  }

  return (
    <div className="flex min-h-screen bg-black">
      {/* Left Section - Reset Form */}
      <div className="flex-1 flex items-center justify-center p-8 lg:p-16">
        <div className="w-full max-w-[450px] animate-[fadeIn_0.8s_ease-out]">
          <h1 className="text-5xl font-bold text-white mb-4 leading-tight">
            Reset your password
          </h1>
          <p className="text-lg text-gray-400 mb-10 leading-relaxed">
            {step === 1
              ? "Enter your email address and we'll send you a reset code."
              : "Enter the code from your email and your new password."}
          </p>

          {/* Success Alert */}
          {otpSent && (
            <div className="mb-6 p-4 bg-green-500/10 border border-green-500/50 rounded-lg">
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle className="h-5 w-5" />
                <span className="text-sm font-medium">Reset code sent to your email!</span>
              </div>
              <p className="text-xs text-green-400/80 mt-1">Please enter the 6-digit code below.</p>
            </div>
          )}

          {/* Error Alert */}
          {(requestMutation.isError || resetMutation.isError) && (
            <Alert className="mb-6 bg-red-500/10 border-red-500/50 text-red-400">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {requestMutation.error?.message || resetMutation.error?.message || "An error occurred. Please try again."}
              </AlertDescription>
            </Alert>
          )}

          {/* Step 1: Request Reset */}
          {step === 1 && (
            <form onSubmit={emailForm.handleSubmit(onRequestReset)} className="space-y-6">
              <div>
                <label htmlFor="email" className="block mb-2 text-sm font-medium text-white">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  autoComplete="email"
                  {...emailForm.register("email")}
                  className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-lg text-white text-[15px] placeholder:text-white/40 transition-all duration-300 focus:outline-none focus:border-[#4169ff] focus:bg-white/10 focus:ring-4 focus:ring-[#4169ff]/10"
                />
                {emailForm.formState.errors.email && (
                  <p className="mt-2 text-sm text-red-400">{emailForm.formState.errors.email.message}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={requestMutation.isPending}
                className="w-full mt-8 px-4 py-4 bg-[#4169ff] text-white text-base font-semibold rounded-lg transition-all duration-300 hover:bg-[#3557e0] hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 flex items-center justify-center gap-2"
              >
                {requestMutation.isPending ? "Sending code..." : "Send Reset Code"}
                {!requestMutation.isPending && <Mail size={18} />}
              </button>
            </form>
          )}

          {/* Step 2: Complete Reset */}
          {step === 2 && (
            <form onSubmit={resetForm.handleSubmit(onCompleteReset)} className="space-y-6">
              {/* Email Field (readonly) */}
              <div>
                <label htmlFor="reset-email" className="block mb-2 text-sm font-medium text-white">
                  Email address
                </label>
                <input
                  id="reset-email"
                  type="email"
                  value={email}
                  {...resetForm.register("email")}
                  readOnly
                  className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-lg text-white text-[15px] opacity-50 cursor-not-allowed"
                />
              </div>

              {/* OTP Field */}
              <div>
                <label htmlFor="otp" className="block mb-2 text-sm font-medium text-white">
                  Reset Code
                </label>
                <input
                  id="otp"
                  type="text"
                  placeholder="Enter 6-digit code"
                  maxLength={6}
                  {...resetForm.register("otp")}
                  className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-lg text-white text-[15px] placeholder:text-white/40 transition-all duration-300 focus:outline-none focus:border-[#4169ff] focus:bg-white/10 focus:ring-4 focus:ring-[#4169ff]/10 text-center tracking-widest font-mono text-lg"
                />
                {resetForm.formState.errors.otp && (
                  <p className="mt-2 text-sm text-red-400">{resetForm.formState.errors.otp.message}</p>
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
                      onClick={onResendOTP}
                      disabled={requestMutation.isPending}
                      className="text-[13px] text-[#4169ff] hover:underline disabled:opacity-50"
                    >
                      Resend code
                    </button>
                  )}
                </div>
              </div>

              {/* New Password Field */}
              <div>
                <label htmlFor="new_password" className="block mb-2 text-sm font-medium text-white">
                  New Password
                </label>
                <div className="relative">
                  <input
                    id="new_password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Create new password"
                    autoComplete="new-password"
                    {...resetForm.register("new_password")}
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
                {resetForm.formState.errors.new_password && (
                  <p className="mt-2 text-sm text-red-400">{resetForm.formState.errors.new_password.message}</p>
                )}
                <div className="text-right mt-2">
                  <span className="text-[13px] text-white/50">
                    Minimum 6 characters
                  </span>
                </div>
              </div>

              {/* Confirm Password Field */}
              <div>
                <label htmlFor="confirm_password" className="block mb-2 text-sm font-medium text-white">
                  Confirm New Password
                </label>
                <div className="relative">
                  <input
                    id="confirm_password"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Confirm new password"
                    autoComplete="new-password"
                    {...resetForm.register("confirm_password")}
                    className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-lg text-white text-[15px] placeholder:text-white/40 transition-all duration-300 focus:outline-none focus:border-[#4169ff] focus:bg-white/10 focus:ring-4 focus:ring-[#4169ff]/10 pr-12"
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
                {resetForm.formState.errors.confirm_password && (
                  <p className="mt-2 text-sm text-red-400">{resetForm.formState.errors.confirm_password.message}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={resetMutation.isPending}
                className="w-full mt-8 px-4 py-4 bg-[#4169ff] text-white text-base font-semibold rounded-lg transition-all duration-300 hover:bg-[#3557e0] hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 flex items-center justify-center gap-2"
              >
                {resetMutation.isPending ? "Resetting password..." : "Reset Password"}
                {!resetMutation.isPending && <ArrowRight size={18} />}
              </button>
            </form>
          )}

          {/* Back to Login Link */}
          <p className="text-center mt-8 text-sm text-white/60">
            Remember your password?
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
