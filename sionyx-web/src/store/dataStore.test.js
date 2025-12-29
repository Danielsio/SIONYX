import { describe, it, expect, beforeEach } from 'vitest';
import { useDataStore } from './dataStore';

describe('dataStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useDataStore.setState({
      users: [],
      packages: [],
      stats: null,
    });
  });

  describe('initial state', () => {
    it('has empty users array initially', () => {
      const state = useDataStore.getState();
      expect(state.users).toEqual([]);
    });

    it('has empty packages array initially', () => {
      const state = useDataStore.getState();
      expect(state.packages).toEqual([]);
    });

    it('has null stats initially', () => {
      const state = useDataStore.getState();
      expect(state.stats).toBeNull();
    });
  });

  describe('setUsers', () => {
    it('sets users array', () => {
      const mockUsers = [
        { uid: 'user-1', firstName: 'John', lastName: 'Doe' },
        { uid: 'user-2', firstName: 'Jane', lastName: 'Smith' },
      ];

      useDataStore.getState().setUsers(mockUsers);

      expect(useDataStore.getState().users).toEqual(mockUsers);
    });

    it('replaces existing users', () => {
      useDataStore.getState().setUsers([{ uid: 'old-user' }]);
      useDataStore.getState().setUsers([{ uid: 'new-user' }]);

      expect(useDataStore.getState().users).toEqual([{ uid: 'new-user' }]);
    });

    it('can set empty array', () => {
      useDataStore.getState().setUsers([{ uid: 'user-1' }]);
      useDataStore.getState().setUsers([]);

      expect(useDataStore.getState().users).toEqual([]);
    });
  });

  describe('setPackages', () => {
    it('sets packages array', () => {
      const mockPackages = [
        { id: 'pkg-1', name: 'Basic', price: 10 },
        { id: 'pkg-2', name: 'Premium', price: 50 },
      ];

      useDataStore.getState().setPackages(mockPackages);

      expect(useDataStore.getState().packages).toEqual(mockPackages);
    });

    it('replaces existing packages', () => {
      useDataStore.getState().setPackages([{ id: 'old-pkg' }]);
      useDataStore.getState().setPackages([{ id: 'new-pkg' }]);

      expect(useDataStore.getState().packages).toEqual([{ id: 'new-pkg' }]);
    });
  });

  describe('setStats', () => {
    it('sets stats object', () => {
      const mockStats = {
        usersCount: 100,
        packagesCount: 10,
        totalRevenue: 5000,
      };

      useDataStore.getState().setStats(mockStats);

      expect(useDataStore.getState().stats).toEqual(mockStats);
    });

    it('can clear stats with null', () => {
      useDataStore.getState().setStats({ usersCount: 100 });
      useDataStore.getState().setStats(null);

      expect(useDataStore.getState().stats).toBeNull();
    });
  });

  describe('addPackage', () => {
    it('adds package to beginning of array', () => {
      const existingPackage = { id: 'pkg-1', name: 'Existing' };
      const newPackage = { id: 'pkg-2', name: 'New' };

      useDataStore.getState().setPackages([existingPackage]);
      useDataStore.getState().addPackage(newPackage);

      const packages = useDataStore.getState().packages;
      expect(packages).toHaveLength(2);
      expect(packages[0]).toEqual(newPackage); // New package is first
      expect(packages[1]).toEqual(existingPackage);
    });

    it('adds package to empty array', () => {
      const newPackage = { id: 'pkg-1', name: 'First' };

      useDataStore.getState().addPackage(newPackage);

      expect(useDataStore.getState().packages).toEqual([newPackage]);
    });

    it('preserves existing packages', () => {
      useDataStore.getState().setPackages([
        { id: 'pkg-1' },
        { id: 'pkg-2' },
      ]);

      useDataStore.getState().addPackage({ id: 'pkg-3' });

      const packages = useDataStore.getState().packages;
      expect(packages).toHaveLength(3);
      expect(packages.map(p => p.id)).toEqual(['pkg-3', 'pkg-1', 'pkg-2']);
    });
  });

  describe('updatePackage', () => {
    it('updates package by id', () => {
      useDataStore.getState().setPackages([
        { id: 'pkg-1', name: 'Original', price: 10 },
        { id: 'pkg-2', name: 'Other', price: 20 },
      ]);

      useDataStore.getState().updatePackage('pkg-1', { name: 'Updated', price: 15 });

      const packages = useDataStore.getState().packages;
      expect(packages[0]).toEqual({ id: 'pkg-1', name: 'Updated', price: 15 });
      expect(packages[1]).toEqual({ id: 'pkg-2', name: 'Other', price: 20 });
    });

    it('partially updates package (merges properties)', () => {
      useDataStore.getState().setPackages([
        { id: 'pkg-1', name: 'Original', price: 10, description: 'Test' },
      ]);

      useDataStore.getState().updatePackage('pkg-1', { price: 20 });

      const pkg = useDataStore.getState().packages[0];
      expect(pkg.name).toBe('Original'); // Unchanged
      expect(pkg.price).toBe(20); // Updated
      expect(pkg.description).toBe('Test'); // Unchanged
    });

    it('does nothing if package id not found', () => {
      useDataStore.getState().setPackages([
        { id: 'pkg-1', name: 'Original' },
      ]);

      useDataStore.getState().updatePackage('non-existent', { name: 'Updated' });

      expect(useDataStore.getState().packages[0].name).toBe('Original');
    });

    it('updates correct package when multiple exist', () => {
      useDataStore.getState().setPackages([
        { id: 'pkg-1', name: 'First' },
        { id: 'pkg-2', name: 'Second' },
        { id: 'pkg-3', name: 'Third' },
      ]);

      useDataStore.getState().updatePackage('pkg-2', { name: 'Updated Second' });

      const packages = useDataStore.getState().packages;
      expect(packages[0].name).toBe('First');
      expect(packages[1].name).toBe('Updated Second');
      expect(packages[2].name).toBe('Third');
    });
  });

  describe('removePackage', () => {
    it('removes package by id', () => {
      useDataStore.getState().setPackages([
        { id: 'pkg-1', name: 'First' },
        { id: 'pkg-2', name: 'Second' },
      ]);

      useDataStore.getState().removePackage('pkg-1');

      const packages = useDataStore.getState().packages;
      expect(packages).toHaveLength(1);
      expect(packages[0].id).toBe('pkg-2');
    });

    it('does nothing if package id not found', () => {
      useDataStore.getState().setPackages([
        { id: 'pkg-1', name: 'First' },
      ]);

      useDataStore.getState().removePackage('non-existent');

      expect(useDataStore.getState().packages).toHaveLength(1);
    });

    it('can remove last package', () => {
      useDataStore.getState().setPackages([{ id: 'pkg-1' }]);

      useDataStore.getState().removePackage('pkg-1');

      expect(useDataStore.getState().packages).toEqual([]);
    });

    it('removes correct package when multiple exist', () => {
      useDataStore.getState().setPackages([
        { id: 'pkg-1' },
        { id: 'pkg-2' },
        { id: 'pkg-3' },
      ]);

      useDataStore.getState().removePackage('pkg-2');

      const packages = useDataStore.getState().packages;
      expect(packages.map(p => p.id)).toEqual(['pkg-1', 'pkg-3']);
    });
  });

  describe('updateUser', () => {
    it('updates user by uid', () => {
      useDataStore.getState().setUsers([
        { uid: 'user-1', firstName: 'John', lastName: 'Doe' },
        { uid: 'user-2', firstName: 'Jane', lastName: 'Smith' },
      ]);

      useDataStore.getState().updateUser('user-1', { firstName: 'Johnny' });

      const users = useDataStore.getState().users;
      expect(users[0].firstName).toBe('Johnny');
      expect(users[0].lastName).toBe('Doe'); // Unchanged
      expect(users[1].firstName).toBe('Jane'); // Other user unchanged
    });

    it('partially updates user (merges properties)', () => {
      useDataStore.getState().setUsers([
        { uid: 'user-1', firstName: 'John', remainingTime: 100, printBalance: 50 },
      ]);

      useDataStore.getState().updateUser('user-1', { remainingTime: 200 });

      const user = useDataStore.getState().users[0];
      expect(user.firstName).toBe('John'); // Unchanged
      expect(user.remainingTime).toBe(200); // Updated
      expect(user.printBalance).toBe(50); // Unchanged
    });

    it('does nothing if user uid not found', () => {
      useDataStore.getState().setUsers([
        { uid: 'user-1', firstName: 'John' },
      ]);

      useDataStore.getState().updateUser('non-existent', { firstName: 'Updated' });

      expect(useDataStore.getState().users[0].firstName).toBe('John');
    });

    it('can update multiple properties at once', () => {
      useDataStore.getState().setUsers([
        { uid: 'user-1', firstName: 'John', lastName: 'Doe', isAdmin: false },
      ]);

      useDataStore.getState().updateUser('user-1', {
        firstName: 'Johnny',
        lastName: 'Updated',
        isAdmin: true,
      });

      const user = useDataStore.getState().users[0];
      expect(user.firstName).toBe('Johnny');
      expect(user.lastName).toBe('Updated');
      expect(user.isAdmin).toBe(true);
    });
  });

  describe('combined operations', () => {
    it('handles multiple operations in sequence', () => {
      // Add some packages
      useDataStore.getState().addPackage({ id: 'pkg-1', name: 'First' });
      useDataStore.getState().addPackage({ id: 'pkg-2', name: 'Second' });

      // Update one
      useDataStore.getState().updatePackage('pkg-1', { name: 'Updated First' });

      // Remove one
      useDataStore.getState().removePackage('pkg-2');

      // Add another
      useDataStore.getState().addPackage({ id: 'pkg-3', name: 'Third' });

      const packages = useDataStore.getState().packages;
      expect(packages).toHaveLength(2);
      expect(packages[0].id).toBe('pkg-3');
      expect(packages[1].name).toBe('Updated First');
    });
  });
});


