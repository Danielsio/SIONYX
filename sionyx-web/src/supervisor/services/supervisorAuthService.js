import { signInWithEmailAndPassword, signOut as firebaseSignOut, onAuthStateChanged } from 'firebase/auth';
import { ref, get } from 'firebase/database';
import { auth, database } from '../../config/firebase';

const phoneToEmail = phone => {
  const cleanPhone = phone.replace(/\D/g, '');
  return `${cleanPhone}@sionyx.app`;
};

export const signInSupervisor = async (phone, password) => {
  try {
    if (!phone || !password) {
      return { success: false, error: 'Phone and password are required' };
    }

    const email = phoneToEmail(phone);
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const uid = userCredential.user.uid;

    await userCredential.user.getIdToken(true);

    const supervisorRef = ref(database, `supervisors/${uid}`);
    const snapshot = await get(supervisorRef);

    if (!snapshot.exists()) {
      await firebaseSignOut(auth);
      return { success: false, error: 'You do not have supervisor privileges.' };
    }

    const supervisorData = snapshot.val();

    const orgsRef = ref(database, `supervisors/${uid}/organizations`);
    const orgsSnapshot = await get(orgsRef);
    const orgIds = orgsSnapshot.exists() ? Object.keys(orgsSnapshot.val()) : [];

    localStorage.setItem('supervisorUid', uid);

    return {
      success: true,
      supervisor: {
        uid,
        phone,
        name: supervisorData.name || '',
        email: supervisorData.email || '',
        orgIds,
      },
    };
  } catch (error) {
    let errorMessage = 'An error occurred during sign in';
    if (error.code === 'auth/invalid-credential' || error.code === 'auth/wrong-password') {
      errorMessage = 'Invalid phone number or password';
    } else if (error.code === 'auth/user-not-found') {
      errorMessage = 'No account found with this phone number';
    } else if (error.code === 'auth/too-many-requests') {
      errorMessage = 'Too many failed attempts. Please try again later';
    }
    return { success: false, error: errorMessage };
  }
};

export const signOutSupervisor = async () => {
  try {
    await firebaseSignOut(auth);
    localStorage.removeItem('supervisorUid');
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const getCurrentSupervisorData = async () => {
  try {
    const user = auth.currentUser;
    if (!user) return { success: false, error: 'Not authenticated' };

    const supervisorRef = ref(database, `supervisors/${user.uid}`);
    const snapshot = await get(supervisorRef);

    if (!snapshot.exists()) {
      return { success: false, error: 'Supervisor data not found' };
    }

    const supervisorData = snapshot.val();
    const orgsRef = ref(database, `supervisors/${user.uid}/organizations`);
    const orgsSnapshot = await get(orgsRef);
    const orgIds = orgsSnapshot.exists() ? Object.keys(orgsSnapshot.val()) : [];

    return {
      success: true,
      supervisor: {
        uid: user.uid,
        name: supervisorData.name || '',
        email: supervisorData.email || '',
        phone: supervisorData.phone || '',
        orgIds,
      },
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const onSupervisorAuthChange = callback => {
  return onAuthStateChanged(auth, callback);
};
