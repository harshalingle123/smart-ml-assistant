import React, { memo } from 'react';

export const ChatPreview = memo(() => {
  return (
    <div className="relative h-full flex items-center justify-center p-8">
      <div className="w-full max-w-lg bg-gradient-to-br from-[#1a1a2e] to-[#16213e] rounded-2xl shadow-[0_0_50px_rgba(65,105,255,0.3)] p-6 animate-[fadeIn_0.8s_ease-out]">
        {/* Chat Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#4169ff] rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h3 className="text-white font-semibold">Chat with AutoML</h3>
              <p className="text-xs text-white/60">AI-powered ML assistant</p>
            </div>
          </div>
          <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs rounded-full border border-green-500/30">
            Active
          </span>
        </div>

        {/* Chat Messages */}
        <div className="space-y-4">
          {/* User Message */}
          <div className="flex justify-end animate-[slideUp_0.5s_ease-out_0.3s_both]">
            <div className="bg-[#4169ff] text-white px-4 py-3 rounded-2xl rounded-tr-sm max-w-[85%]">
              <p className="text-sm">Train a model to predict house prices using my dataset</p>
            </div>
          </div>

          {/* AutoML Response */}
          <div className="flex justify-start animate-[slideUp_0.5s_ease-out_0.5s_both]">
            <div className="bg-white/5 backdrop-blur-sm text-white px-4 py-3 rounded-2xl rounded-tl-sm max-w-[85%] border border-white/10">
              <p className="text-sm mb-3">I'll help you train a regression model. Here's what I'm doing:</p>

              {/* Processing Steps */}
              <div className="space-y-2 mb-3">
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-green-400">✓</span>
                  <span className="text-white/80">Analyzing dataset structure</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-green-400">✓</span>
                  <span className="text-white/80">Preprocessing features</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 border-2 border-[#4169ff] border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-white/80">Training model...</span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="bg-white/10 rounded-full h-2 overflow-hidden">
                <div className="bg-gradient-to-r from-[#4169ff] to-[#5179ff] h-full w-[78%] rounded-full animate-[pulse_2s_ease-in-out_infinite]"></div>
              </div>
              <p className="text-xs text-white/60 mt-1">Training progress: 78%</p>

              {/* Code Snippet */}
              <div className="mt-3 bg-black/30 rounded-lg p-3 border border-white/5">
                <code className="text-xs text-green-400 font-mono">
                  model = AutoML(task='regression')<br/>
                  model.fit(train_data, label='price')
                </code>
              </div>
            </div>
          </div>

          {/* Typing Indicator */}
          <div className="flex justify-start animate-[slideUp_0.5s_ease-out_0.7s_both]">
            <div className="bg-white/5 backdrop-blur-sm px-4 py-3 rounded-2xl rounded-tl-sm border border-white/10">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-white/60 rounded-full animate-[bounce_1s_ease-in-out_0s_infinite]"></span>
                <span className="w-2 h-2 bg-white/60 rounded-full animate-[bounce_1s_ease-in-out_0.2s_infinite]"></span>
                <span className="w-2 h-2 bg-white/60 rounded-full animate-[bounce_1s_ease-in-out_0.4s_infinite]"></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

ChatPreview.displayName = 'ChatPreview';
