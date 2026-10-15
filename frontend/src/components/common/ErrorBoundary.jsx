import React from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an uncaught error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  handleGoDashboard = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/dashboard';
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[50vh] flex items-center justify-center p-4">
          <div className="bg-[#050505] border border-red-500/30 p-6 sm:p-8 max-w-xl w-full specular-top-edge shadow-2xl space-y-5">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 border border-red-500/40 bg-red-950/30 flex items-center justify-center flex-shrink-0">
                <AlertCircle className="w-5 h-5 text-red-400" />
              </div>
              <div className="space-y-1">
                <span className="font-mono text-[10px] text-red-400 uppercase tracking-widest font-bold">
                  System Render Notice
                </span>
                <h3 className="text-base font-mono font-bold text-white uppercase tracking-wider">
                  Component Error Encountered
                </h3>
                <p className="text-xs text-zinc-400 font-sans leading-relaxed">
                  The portal encountered an unexpected display issue while rendering this section. Your saved RPL data and candidate profile remain safe in the database.
                </p>
              </div>
            </div>

            {this.state.error && (
              <div className="p-3 bg-[#080808] border border-white/10 font-mono text-xs text-zinc-300 break-words overflow-auto max-h-36">
                <span className="text-red-400 font-semibold">Error:</span> {this.state.error?.message || String(this.state.error)}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-white/10">
              <button
                type="button"
                onClick={this.handleReset}
                className="inline-flex items-center gap-2 px-4 py-2 bg-white text-black font-mono text-xs font-bold uppercase tracking-wider hover:bg-zinc-200 transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Reload Page</span>
              </button>
              <button
                type="button"
                onClick={this.handleGoDashboard}
                className="inline-flex items-center gap-2 px-4 py-2 border border-white/20 text-white font-mono text-xs uppercase tracking-wider hover:bg-white/5 transition-colors cursor-pointer"
              >
                <Home className="w-3.5 h-3.5" />
                <span>Return to Dashboard</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
