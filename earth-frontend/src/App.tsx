import { Toaster } from '@/components/ui/toaster';
import { Toaster as Sonner } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Schemas from './pages/Schemas';
import Endpoints from './pages/Endpoints';
import Search from './pages/EndpointSearch';
import Documents from './pages/Documents';
import DocumentSearch from './pages/DocumentSearch';
import NotFound from './pages/NotFound';

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter basename="/ui">
        <Routes>
          {/* Redirect root to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Public Routes */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/schemas" element={<Schemas />} />
          <Route path="/endpoints" element={<Endpoints />} />
          <Route path="/search" element={<Search />} />
          <Route path="/documents" element={<Documents />} />

          <Route path="/document-search" element={<DocumentSearch />} />

          {/* Catch-all route */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
