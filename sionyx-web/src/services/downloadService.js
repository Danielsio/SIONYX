/**
 * Download Service for SIONYX
 * ===========================
 * Handles downloading of SIONYX executables from Firebase Storage
 */

import { ref, getDownloadURL } from 'firebase/storage';
import { storage } from '../config/firebase';

/**
 * Get the latest release information
 * @returns {Promise<Object>} Release information including download URL
 */
export const getLatestRelease = async () => {
  try {
    // Try to get release info from a database or API endpoint
    // For now, we'll use a hardcoded path - you can make this dynamic
    const releasePath = 'releases/latest.json';
    
    try {
      // Try to get from your API/database first
      const response = await fetch('/api/latest-release');
      if (response.ok) {
        const releaseInfo = await response.json();
        return {
          downloadUrl: releaseInfo.download_url,
          version: releaseInfo.version || '1.0.0',
          releaseDate: releaseInfo.upload_time,
          fileSize: releaseInfo.file_size,
          fileName: releaseInfo.file_name
        };
      }
    } catch (apiError) {
      console.warn('API not available, using fallback method');
    }
    
    // Fallback: Try to get from Firebase Storage directly
    // This requires the latest.json file to be uploaded with release info
    try {
      const latestRef = ref(storage, releasePath);
      const downloadUrl = await getDownloadURL(latestRef);
      
      const response = await fetch(downloadUrl);
      const releaseInfo = await response.json();
      
      return {
        downloadUrl: releaseInfo.download_url,
        version: releaseInfo.version || '1.0.0',
        releaseDate: releaseInfo.upload_time,
        fileSize: releaseInfo.file_size,
        fileName: releaseInfo.file_name
      };
    } catch (storageError) {
      console.warn('Could not get latest release info from storage');
    }
    
    // Use environment variable for download URL
    const downloadUrl = import.meta.env.VITE_INSTALLER_DOWNLOAD_URL;
    if (downloadUrl) {
      return {
        downloadUrl: downloadUrl,
        version: 'Latest',
        releaseDate: new Date().toISOString(),
        fileSize: 0,
        fileName: 'sionyx-installer.exe'
      };
    }
    
    // Fallback to Firebase Storage direct path
    try {
      const fileRef = ref(storage, 'sionyx-installer.exe');
      const downloadUrl = await getDownloadURL(fileRef);
      
      return {
        downloadUrl: downloadUrl,
        version: 'Latest',
        releaseDate: new Date().toISOString(),
        fileSize: 0,
        fileName: 'sionyx-installer.exe'
      };
    } catch (fallbackError) {
      console.error('Fallback download failed:', fallbackError);
      throw new Error('No download available');
    }
    
  } catch (error) {
    console.error('Failed to get latest release:', error);
    throw new Error('Unable to get latest release information');
  }
};

/**
 * Download a file from a URL
 * @param {string} url - The download URL
 * @param {string} filename - The filename to save as
 * @returns {Promise<void>}
 */
export const downloadFile = async (url, filename) => {
  try {
    console.log(`Starting download: ${filename} from ${url}`);
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const blob = await response.blob();
    
    // Create download link
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    link.style.display = 'none';
    
    // Add to DOM, click, and remove
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up the object URL
    setTimeout(() => {
      window.URL.revokeObjectURL(downloadUrl);
    }, 1000);
    
    console.log(`Download completed: ${filename}`);
    
  } catch (error) {
    console.error('Download failed:', error);
    throw new Error(`Download failed: ${error.message}`);
  }
};

/**
 * Get file size in human readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Human readable file size
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Format release date
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
export const formatReleaseDate = (dateString) => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return 'Unknown date';
  }
};

/**
 * Check if a file exists in Firebase Storage
 * @param {string} path - Storage path
 * @returns {Promise<boolean>} True if file exists
 */
export const checkFileExists = async (path) => {
  try {
    const fileRef = ref(storage, path);
    await getDownloadURL(fileRef);
    return true;
  } catch (error) {
    return false;
  }
};

/**
 * Get all available releases
 * @returns {Promise<Array>} Array of release information
 */
export const getAllReleases = async () => {
  try {
    // This would require listing files in the releases folder
    // For now, return the latest release
    const latest = await getLatestRelease();
    return [latest];
  } catch (error) {
    console.error('Failed to get releases:', error);
    return [];
  }
};

/**
 * Download with progress tracking
 * @param {string} url - Download URL
 * @param {string} filename - Filename
 * @param {Function} onProgress - Progress callback (bytes, total)
 * @returns {Promise<void>}
 */
export const downloadFileWithProgress = async (url, filename, onProgress) => {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const contentLength = response.headers.get('content-length');
    const total = parseInt(contentLength, 10);
    let loaded = 0;
    
    const reader = response.body.getReader();
    const chunks = [];
    
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;
      
      chunks.push(value);
      loaded += value.length;
      
      if (onProgress) {
        onProgress(loaded, total);
      }
    }
    
    // Combine chunks into blob
    const blob = new Blob(chunks);
    
    // Create download link
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setTimeout(() => {
      window.URL.revokeObjectURL(downloadUrl);
    }, 1000);
    
  } catch (error) {
    console.error('Download with progress failed:', error);
    throw new Error(`Download failed: ${error.message}`);
  }
};