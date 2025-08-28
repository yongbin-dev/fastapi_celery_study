import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Header } from '@/shared/components';
import HomePage from '@/pages/HomePage';
import AboutPage from '@/pages/AboutPage';
import { ChatBotPage } from '@/features/chatbot';
import { TaskPage } from '@/features/task';

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
              <Route path="/chatbot" element={<ChatBotPage />} />
              <Route path="/tasks" element={<TaskPage />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
