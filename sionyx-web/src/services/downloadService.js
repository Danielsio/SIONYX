/**
 * Download Service for SIONYX
 * ===========================
 * Handles downloading of SIONYX executables from Firebase Storage
 */

// Firebase Storage imports removed - using direct URL from environment variable

/**
 * Get the latest release information
 * @returns {Promise<Object>} Release information including download URL
 */
export const getLatestRelease = async () => {
  // Use environment variable for download URL - no fallbacks
  const downloadUrl = import.meta.env.VITE_INSTALLER_DOWNLOAD_URL;
  
  if (!downloadUrl) {
    throw new Error('VITE_INSTALLER_DOWNLOAD_URL environment variable is not set. Please configure the download URL in your .env file.');
  }
  
  return {
    downloadUrl: downloadUrl,
    version: 'Latest',
    releaseDate: new Date().toISOString(),
    fileSize: 0,
    fileName: 'sionyx-installer.exe'
  };
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

// Removed unused functions - using direct URL approach

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