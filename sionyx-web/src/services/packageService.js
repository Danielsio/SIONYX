import { ref, get, set, update, remove, push } from 'firebase/database';
import { database } from '../config/firebase';
import { useAuthStore } from '../store/authStore';
import { isSupervisorPendingActivation } from '../utils/roles';

const normalizePackageData = packageData => ({
  ...packageData,
  discountPercent: packageData.discountPercent ?? 0,
  minutes: packageData.minutes ?? 0,
  prints: packageData.prints ?? 0,
  validityDays: packageData.validityDays ?? 0,
});

/**
 * Get all packages in an organization
 */
export const getAllPackages = async orgId => {
  // Supervisor activation gate: return empty data if not yet activated
  if (isSupervisorPendingActivation(useAuthStore.getState().user)) {
    return { success: true, packages: [] };
  }

  try {
    const packagesRef = ref(database, `organizations/${orgId}/packages`);
    const snapshot = await get(packagesRef);

    if (!snapshot.exists()) {
      return {
        success: true,
        packages: [],
      };
    }

    const packagesData = snapshot.val();
    const packages = Object.keys(packagesData).map(id => ({
      id,
      ...packagesData[id],
    }));

    // Sort by creation date (newest first)
    packages.sort((a, b) => {
      const dateA = new Date(a.createdAt || 0);
      const dateB = new Date(b.createdAt || 0);
      return dateB - dateA;
    });

    return {
      success: true,
      packages,
    };
  } catch (error) {
    console.error('Error getting packages:', error);
    return {
      success: false,
      error: error.message,
      packages: [],
    };
  }
};

/**
 * Create a new package
 */
export const createPackage = async (orgId, packageData) => {
  try {
    const packagesRef = ref(database, `organizations/${orgId}/packages`);
    const newPackageRef = push(packagesRef);

    const newPackage = {
      ...normalizePackageData(packageData),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    await set(newPackageRef, newPackage);

    return {
      success: true,
      packageId: newPackageRef.key,
      message: 'Package created successfully',
    };
  } catch (error) {
    console.error('Error creating package:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Update an existing package
 */
export const updatePackage = async (orgId, packageId, updates) => {
  try {
    const packageRef = ref(database, `organizations/${orgId}/packages/${packageId}`);

    const updateData = {
      ...normalizePackageData(updates),
      updatedAt: new Date().toISOString(),
    };

    await update(packageRef, updateData);

    return {
      success: true,
      message: 'Package updated successfully',
    };
  } catch (error) {
    console.error('Error updating package:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Delete a package
 */
export const deletePackage = async (orgId, packageId) => {
  try {
    const packageRef = ref(database, `organizations/${orgId}/packages/${packageId}`);
    await remove(packageRef);

    return {
      success: true,
      message: 'Package deleted successfully',
    };
  } catch (error) {
    console.error('Error deleting package:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Calculate final price after discount
 */
export const calculateFinalPrice = (price, discountPercent) => {
  const discount = discountPercent || 0;
  const finalPrice = price * (1 - discount / 100);
  return {
    originalPrice: price,
    discountPercent: discount,
    finalPrice: Math.round(finalPrice * 100) / 100,
    savings: Math.round((price - finalPrice) * 100) / 100,
  };
};
