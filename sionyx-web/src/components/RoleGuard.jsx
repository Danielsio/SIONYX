import PropTypes from 'prop-types';
import { useAuthStore } from '../store/authStore';
import { hasRole, ROLES } from '../utils/roles';

/**
 * RoleGuard - Conditionally renders children based on user role
 *
 * Usage:
 *   <RoleGuard requiredRole="supervisor">
 *     <SupervisorOnlyContent />
 *   </RoleGuard>
 *
 *   <RoleGuard requiredRole="admin" fallback={<AccessDenied />}>
 *     <AdminContent />
 *   </RoleGuard>
 */
const RoleGuard = ({ requiredRole, children, fallback = null }) => {
  const user = useAuthStore(state => state.user);

  if (hasRole(user, requiredRole)) {
    return children;
  }

  return fallback;
};

RoleGuard.propTypes = {
  requiredRole: PropTypes.oneOf(Object.values(ROLES)).isRequired,
  children: PropTypes.node.isRequired,
  fallback: PropTypes.node,
};

export default RoleGuard;
