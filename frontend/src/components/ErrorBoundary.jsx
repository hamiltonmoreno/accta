import React from 'react';
import { AlertTriangle, RotateCw, Home } from 'lucide-react';

/**
 * ErrorBoundary — catches uncaught render errors anywhere below it and
 * shows a graceful fallback instead of a white screen of death.
 *
 * Wrap the entire <App /> with it so a bug in any page produces a
 * "Recover" UI rather than crashing the SPA. Errors are also logged to
 * console.error so Sentry/LogRocket-style integrations pick them up.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('Uncaught render error:', error, info);
  }

  handleReset = () => {
    this.setState({ error: null });
  };

  render() {
    if (!this.state.error) {
      return this.props.children;
    }

    return (
      <div
        className="min-h-screen flex items-center justify-center bg-gray-50 px-6"
        role="alert"
        aria-live="assertive"
      >
        <div className="max-w-lg w-full bg-white rounded-2xl border border-gray-200 shadow-sm p-8 text-center">
          <div className="w-14 h-14 bg-carmesim/10 rounded-full flex items-center justify-center mx-auto mb-5">
            <AlertTriangle className="w-7 h-7 text-carmesim" aria-hidden="true" />
          </div>
          <h1 className="font-sans font-bold text-2xl text-grafite mb-2">
            Algo correu mal
          </h1>
          <p className="text-gray-600 mb-6">
            Ocorreu um erro inesperado nesta página. Pode tentar de novo ou
            voltar à página inicial.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              type="button"
              onClick={this.handleReset}
              className="inline-flex items-center justify-center gap-2 bg-floresta text-white px-5 py-2.5 rounded-lg font-semibold hover:bg-floresta-dark transition-colors"
            >
              <RotateCw className="w-4 h-4" aria-hidden="true" />
              Tentar novamente
            </button>
            <a
              href="/"
              className="inline-flex items-center justify-center gap-2 bg-white border border-[#D1D5DB] text-[#3A3A3A] px-5 py-2.5 rounded-lg font-semibold hover:bg-[#F5F5F5] transition-colors"
            >
              <Home className="w-4 h-4" aria-hidden="true" />
              Voltar ao início
            </a>
          </div>
          {process.env.NODE_ENV === 'development' && this.state.error?.message && (
            <pre className="mt-6 text-left text-xs bg-gray-100 rounded-lg p-3 overflow-auto text-grafite/70">
              {this.state.error.message}
            </pre>
          )}
        </div>
      </div>
    );
  }
}
