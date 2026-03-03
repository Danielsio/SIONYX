import { useEffect, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme, App as AntApp, Spin } from 'antd';
import { useAuthStore } from './store/authStore';
import { onAuthChange, getCurrentAdminData } from './services/authService';

// Components
import ProtectedRoute from './components/ProtectedRoute';
import MainLayout from './components/MainLayout';

// Lazy load pages for better performance
const LandingPage = lazy(() => import('./pages/LandingPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const OverviewPage = lazy(() => import('./pages/OverviewPage'));
const UsersPage = lazy(() => import('./pages/UsersPage'));
const PackagesPage = lazy(() => import('./pages/PackagesPage'));
const MessagesPage = lazy(() => import('./pages/MessagesPage'));
const ComputersPage = lazy(() => import('./pages/ComputersPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const AnnouncementsPage = lazy(() => import('./pages/AnnouncementsPage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));

function App() {
  const { setUser, setLoading, isAuthenticated, darkMode } = useAuthStore();

  useEffect(() => {
    setLoading(true);

    const unsubscribe = onAuthChange(async firebaseUser => {
      if (firebaseUser) {
        const result = await getCurrentAdminData();
        if (result.success) {
          setUser(result.admin);
        } else {
          setUser(null);
        }
      } else {
        setUser(null);
      }

      setLoading(false);
    });

    return () => unsubscribe();
  }, [setUser, setLoading]);

  const LoadingFallback = () => (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        direction: 'rtl',
      }}
    >
      <Spin size='large' />
    </div>
  );

  return (
    <ConfigProvider
      theme={{
        algorithm: darkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#667eea',
          borderRadius: 6,
        },
      }}
      direction='rtl'
    >
      <AntApp>
        <Router>
          <Suspense fallback={<LoadingFallback />}>
            <Routes>
              {/* Landing Page */}
              <Route path='/' element={<LandingPage />} />

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
                <Route path='announcements' element={<AnnouncementsPage />} />
                <Route path='reports' element={<ReportsPage />} />
                <Route path='settings' element={<SettingsPage />} />
              </Route>

              {/* Catch all - redirect to home */}
              <Route path='*' element={<Navigate to='/' replace />} />
            </Routes>
          </Suspense>
        </Router>
      </AntApp>
    </ConfigProvider>
  );
}

export default App;
