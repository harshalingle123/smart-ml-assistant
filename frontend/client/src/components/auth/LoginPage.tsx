import React, { useState, useCallback, memo, FormEvent } from 'react';
import { AuthLayout } from './AuthLayout';
import { ChatPreview } from './ChatPreview';
import { SocialButton } from './SocialButton';

interface LoginFormData {
  email: string;
  password: string;
}

export const LoginPage = memo(() => {
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  }, []);

  const togglePasswordVisibility = useCallback(() => {
    setShowPassword(prev => !prev);
  }, []);

  const handleSubmit = useCallback((e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    // Placeholder for actual authentication logic
    console.log('Login attempt:', formData);

    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      console.log('Login submitted:', formData);
    }, 1500);
  }, [formData]);

  const handleGoogleLogin = useCallback(() => {
    console.log('Google OAuth login initiated');
    // Implement Google OAuth flow
  }, []);

  return (
    <AuthLayout reverse={false} chatPreview={<ChatPreview />}>
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-white">Welcome back</h1>
          <p className="text-white/60">Sign in to continue building amazing ML models.</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Email Input */}
          <div className="space-y-2">
            <label htmlFor="email" className="block text-sm font-medium text-white/80">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={formData.email}
              onChange={handleInputChange}
              className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-[#4169ff] focus:ring-2 focus:ring-[#4169ff]/50 transition-all duration-200"
              placeholder="you@example.com"
            />
          </div>

          {/* Password Input */}
          <div className="space-y-2">
            <label htmlFor="password" className="block text-sm font-medium text-white/80">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                value={formData.password}
                onChange={handleInputChange}
                className="w-full px-4 py-3.5 pr-12 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-[#4169ff] focus:ring-2 focus:ring-[#4169ff]/50 transition-all duration-200"
                placeholder="Enter your password"
              />
              <button
                type="button"
                onClick={togglePasswordVisibility}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60 focus:outline-none"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
            <div className="flex justify-end">
              <a href="#forgot-password" className="text-sm text-[#4169ff] hover:text-[#5179ff] transition-colors">
                Forgot password?
              </a>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full px-4 py-4 bg-[#4169ff] text-white font-semibold rounded-lg transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#5179ff] hover:shadow-lg hover:shadow-[#4169ff]/50 focus:outline-none focus:ring-2 focus:ring-[#4169ff] focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <span>Sign In</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </>
            )}
          </button>
        </form>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-white/10"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-4 bg-black text-white/40">or continue with</span>
          </div>
        </div>

        {/* Social Login */}
        <SocialButton provider="google" onClick={handleGoogleLogin} disabled={isLoading} />

        {/* Sign Up Link */}
        <div className="text-center">
          <p className="text-white/60">
            New to AutoML?{' '}
            <a href="/signup" className="text-[#4169ff] hover:text-[#5179ff] font-medium transition-colors">
              Create an account
            </a>
          </p>
        </div>
      </div>
    </AuthLayout>
  );
});

LoginPage.displayName = 'LoginPage';
