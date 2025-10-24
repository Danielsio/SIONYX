import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme, App as AntApp } from 'antd';
import { useAuthStore } from './store/authStore';
import { onAuthChange, getCurrentAdminData } from './services/authService';

// Components
import ProtectedRoute from './components/ProtectedRoute';
import MainLayout from './components/MainLayout';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import DownloadPage from './pages/DownloadPage';
import OverviewPage from './pages/OverviewPage';
import UsersPage from './pages/UsersPage';
import PackagesPage from './pages/PackagesPage';
import MessagesPage from './pages/MessagesPage';
import ComputersPage from './pages/ComputersPage';

function App() {
  const { setUser, setLoading, isAuthenticated } = useAuthStore();

  useEffect(() => {
    // Listen to auth state changes
    const unsubscribe = onAuthChange(async firebaseUser => {
      setLoading(true);

      if (firebaseUser) {
        // User is signed in, get full admin data
        const result = await getCurrentAdminData();
        if (result.success) {
          setUser(result.admin);
        } else {
          setUser(null);
        }
      } else {
        // User is signed out
        setUser(null);
      }

      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#667eea',
          borderRadius: 6,
        },
      }}
      direction='rtl'
    >
      <AntApp>
        <Router>
          <Routes>
            {/* Landing Page */}
            <Route path='/' element={<LandingPage />} />

            {/* Download Page */}
            <Route path='/download' element={<DownloadPage />} />

            {/* Admin Login */}
            <Route
              path='/admin/login'
              element={isAuthenticated ? <Navigate to='/admin' replace /> : <LoginPage />}
            />

            {/* Protected Admin Routes */}
            <Route
              path='/admin'
              element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<OverviewPage />} />
              <Route path='users' element={<UsersPage />} />
              <Route path='packages' element={<PackagesPage />} />
              <Route path='messages' element={<MessagesPage />} />
              <Route path='computers' element={<ComputersPage />} />
            </Route>

            {/* Catch all - redirect to home */}
            <Route path='*' element={<Navigate to='/' replace />} />
          </Routes>
        </Router>
      </AntApp>
    </ConfigProvider>
  );
}

export default App;
