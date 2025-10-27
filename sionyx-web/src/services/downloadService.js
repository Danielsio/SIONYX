/**
 * Download Service for SIONYX
 * ===========================
 * Handles downloading of SIONYX executables from Firebase Storage
 * with automatic version discovery.
 */

// Firebase Storage base URL - use proxy in dev to bypass CORS
const STORAGE_BASE_URL = import.meta.env.DEV 
  ? '/storage-proxy' 
  : 'https://storage.googleapis.com';

/**
 * Get Firebase Storage bucket from environment or default
 */
const getStorageBucket = () => {
  return import.meta.env.VITE_FIREBASE_STORAGE_BUCKET;
};

/**
 * Fetch the latest release metadata from Firebase Storage
 * @returns {Promise<Object>} Release metadata
 */
const fetchLatestMetadata = async () => {
  const bucket = getStorageBucket();
  const metadataUrl = `${STORAGE_BASE_URL}/${bucket}/releases/latest.json`;

  try {
    const response = await fetch(metadataUrl, {
      cache: 'no-cache', // Always get fresh metadata
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch metadata: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.warn('Could not fetch latest.json metadata:', error.message);
    return null;
  }
};

/**
 * Get the latest release information from Firebase Storage metadata
 * @returns {Promise<Object>} Release information including download URL
 */
export const getLatestRelease = async () => {
  const metadata = await fetchLatestMetadata();

  if (metadata && metadata.downloadUrl) {
    return {
      version: metadata.version || 'Latest',
      downloadUrl: metadata.downloadUrl,
      releaseDate: metadata.releaseDate || new Date().toISOString(),
      fileSize: metadata.fileSize || 0,
      fileName: metadata.filename || `sionyx-installer-v${metadata.version}.exe`,
      buildNumber: metadata.buildNumber || null,
      changelog: metadata.changelog || [],
    };
  }

  throw new Error('Could not fetch release metadata. Please try again later.');
};

/**
 * Get all available versions (if version history is enabled)
 * @returns {Promise<Array>} List of available versions
 */
export const getAvailableVersions = async () => {
  // For now, just return latest version
  // Could be extended to list all versions from storage
  const latest = await getLatestRelease();
  return [latest];
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

    if (!url || !url.startsWith('http')) {
      throw new Error('Invalid download URL');
    }

    // Direct download approach (CORS-friendly)
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.target = '_blank';
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    console.log(`Download initiated: ${filename}`);
  } catch (error) {
    console.error('Download failed:', error);
    throw new Error(`Download failed: ${error.message}`);
  }
};

/**
 * Download with progress tracking
 * @param {string} url - Download URL
 * @param {string} filename - Filename
 * @param {Function} onProgress - Progress callback (loaded, total)
 * @returns {Promise<void>}
 */
export const downloadFileWithProgress = async (url, filename, onProgress) => {
  try {
    console.log(`Starting download: ${filename}`);

    if (!url || !url.startsWith('http')) {
      throw new Error('Invalid download URL');
    }

    // Simulate progress for direct download
    if (onProgress) onProgress(0, 100);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.target = '_blank';
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    if (onProgress) setTimeout(() => onProgress(100, 100), 100);

    console.log(`Download initiated: ${filename}`);
  } catch (error) {
    console.error('Download failed:', error);
    throw new Error(`Download failed: ${error.message}`);
  }
};

/**
 * Format file size in human readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Human readable file size
 */
export const formatFileSize = bytes => {
  if (bytes === 0) return 'Unknown size';

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
export const formatReleaseDate = dateString => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('he-IL', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch (error) {
    return 'תאריך לא ידוע';
  }
};

/**
 * Format version string for display
 * @param {Object} release - Release object
 * @returns {string} Formatted version string
 */
export const formatVersion = release => {
  if (!release) return '';

  let version = release.version || 'Latest';
  if (release.buildNumber) {
    version += ` (Build #${release.buildNumber})`;
  }

  return version;
};
