import { Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from '../store/authStore';
import { isAdminOrAbove } from '../utils/roles';

const ProtectedRoute = ({ children }) => {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  const isLoading = useAuthStore(state => state.isLoading);
  const user = useAuthStore(state => state.user);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <Spin size='large' />
      </div>
    );
  }

  if (!isAuthenticated || !isAdminOrAbove(user)) {
    return <Navigate to='/admin/login' replace />;
  }

  return children;
};

export default ProtectedRoute;
