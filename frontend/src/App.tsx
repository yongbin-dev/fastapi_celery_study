import { TaskPage } from '@/features/task';
import AboutPage from '@/pages/AboutPage';
import HomePage from '@/pages/HomePage';
import { Header } from '@/shared/components';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { OcrPage } from './features/ocr/pages';
import ContactPage from './pages/ContactPage';
import { OcrComparisonPage } from './features/ocr';
import { analyzeSimilarity } from '@/features/ocr/utils/similarity';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="h-screen bg-gray-50 overflow-hidden flex flex-col">
          <Header />
          <main className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/pipelines" element={<TaskPage />} />
              <Route path="/ocr" element={<OcrPage />} />
              <Route path="/ocr-comparison" element={<OcrComparisonPage analyzeSimilarity={analyzeSimilarity} />} />
              <Route path="/contact" element={<ContactPage />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
