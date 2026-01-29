import { BrowserRouter as Router } from 'react-router-dom'
import { ErrorBoundary } from 'react-error-boundary'
import { Toaster } from "./components/ui/sonner"
import { Suspense } from 'react';
import InlineLoader from './components/layout/InlineLoader';
import { ErrorFallback } from './components/layout/ErrorFallBack';
import { AppRoutes } from './routes/AppRoutes';


function App() {
 
  return (
    <Router>
        <Suspense fallback={<InlineLoader />}>
          <ErrorBoundary FallbackComponent={ErrorFallback}>
            <AppRoutes />
          </ErrorBoundary>
          <Toaster richColors position="top-right" />
        </Suspense>
      </Router>
  );
}

export default App;
