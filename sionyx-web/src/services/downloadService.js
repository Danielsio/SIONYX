import { storage } from '../config/firebase';
import { ref, getDownloadURL } from 'firebase/storage';

// Software file path in Firebase Storage
const SOFTWARE_FILE_PATH = 'software/sionyx-installer.exe';

export const getSoftwareDownloadUrl = async () => {
  try {
    const softwareRef = ref(storage, SOFTWARE_FILE_PATH);
    const downloadUrl = await getDownloadURL(softwareRef);
    
    return {
      success: true,
      downloadUrl
    };
  } catch (error) {
    console.error('Error getting download URL:', error);
    return {
      success: false,
      error: 'Failed to get download URL'
    };
  }
};

export const downloadSoftware = async () => {
  try {
    const result = await getSoftwareDownloadUrl();
    
    if (result.success) {
      // Create a temporary link element and trigger download
      const link = document.createElement('a');
      link.href = result.downloadUrl;
      link.download = 'sionyx-installer.exe';
      link.target = '_blank';
      
      // Append to body, click, and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      return {
        success: true,
        message: 'Download started successfully'
      };
    } else {
      return result;
    }
  } catch (error) {
    console.error('Error downloading software:', error);
    return {
      success: false,
      error: 'Failed to download software'
    };
  }
};
