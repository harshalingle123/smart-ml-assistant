import React, { memo, ReactNode } from 'react';

interface AuthLayoutProps {
  children: ReactNode;
  reverse?: boolean;
  chatPreview: ReactNode;
}

export const AuthLayout = memo<AuthLayoutProps>(({ children, reverse = false, chatPreview }) => {
  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-7xl">
        <div className={`grid lg:grid-cols-2 gap-8 items-center ${reverse ? 'lg:grid-flow-dense' : ''}`}>
          {/* Form Section */}
          <div className={`w-full max-w-md mx-auto ${reverse ? 'lg:col-start-1' : 'lg:col-start-2'} animate-[fadeIn_0.6s_ease-out]`}>
            {children}
          </div>

          {/* Chat Preview Section */}
          <div className={`hidden lg:block ${reverse ? 'lg:col-start-2' : 'lg:col-start-1'}`}>
            {chatPreview}
          </div>
        </div>
      </div>
    </div>
  );
});

AuthLayout.displayName = 'AuthLayout';
