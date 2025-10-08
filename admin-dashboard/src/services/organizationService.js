import { ref, get } from 'firebase/database';
import { database } from '../config/firebase';

/**
 * Get organization statistics
 */
export const getOrganizationStats = async (orgId) => {
  try {
    // Get users count
    const usersRef = ref(database, `organizations/${orgId}/users`);
    const usersSnapshot = await get(usersRef);
    const usersCount = usersSnapshot.exists() 
      ? Object.keys(usersSnapshot.val()).length 
      : 0;
    
    // Get packages count
    const packagesRef = ref(database, `organizations/${orgId}/packages`);
    const packagesSnapshot = await get(packagesRef);
    const packagesCount = packagesSnapshot.exists() 
      ? Object.keys(packagesSnapshot.val()).length 
      : 0;
    
    // Get purchases count
    const purchasesRef = ref(database, `organizations/${orgId}/purchases`);
    const purchasesSnapshot = await get(purchasesRef);
    const purchasesCount = purchasesSnapshot.exists() 
      ? Object.keys(purchasesSnapshot.val()).length 
      : 0;
    
    // Calculate total time purchased
    let totalTimeMinutes = 0;
    let totalRevenue = 0;
    
    if (purchasesSnapshot.exists()) {
      const purchases = purchasesSnapshot.val();
      Object.values(purchases).forEach(purchase => {
        if (purchase.status === 'completed') {
          totalTimeMinutes += purchase.timeMinutes || 0;
          totalRevenue += purchase.finalPrice || 0;
        }
      });
    }
    
    return {
      success: true,
      stats: {
        usersCount,
        packagesCount,
        purchasesCount,
        totalTimeMinutes,
        totalRevenue
      }
    };
  } catch (error) {
    console.error('Error getting organization stats:', error);
    return {
      success: false,
      error: error.message,
      stats: {
        usersCount: 0,
        packagesCount: 0,
        purchasesCount: 0,
        totalTimeMinutes: 0,
        totalRevenue: 0
      }
    };
  }
};

