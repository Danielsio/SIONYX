/**
 * Download Service for SIONYX
 * ===========================
 * Handles downloading of SIONYX executables from Firebase Storage
 * with automatic version discovery.
 */

import { logger } from '../utils/logger';

/**
 * Get Firebase Storage bucket from environment or default
 */
const getStorageBucket = () => {
  return import.meta.env.VITE_FIREBASE_STORAGE_BUCKET;
};

/**
 * Build a Firebase Storage REST API URL for a given path.
 * Uses the firebasestorage.googleapis.com endpoint which respects
 * Firebase Security Rules (unlike storage.googleapis.com which needs IAM/ACL).
 */
const getFirebaseStorageUrl = path => {
  const bucket = getStorageBucket();
  const encodedPath = encodeURIComponent(path);
  return `https://firebasestorage.googleapis.com/v0/b/${bucket}/o/${encodedPath}`;
};

/**
 * Get Firebase RTDB URL for public data
 */
const getRtdbUrl = path => {
  const databaseUrl = import.meta.env.VITE_FIREBASE_DATABASE_URL;
  return `${databaseUrl}/${path}.json`;
};

/**
 * Fetch the latest release metadata.
 *
 * Primary: Firebase Realtime Database (public/latestRelease)
 *   - No auth needed, no Storage 403 issues
 *   - Written by build.py during each release
 *
 * Fallback: Firebase Storage (latest.json)
 *   - May fail with 403 if uniform bucket-level access is enabled
 *
 * @returns {Promise<Object>} Release metadata
 */
const fetchLatestMetadata = async () => {
  // PRIMARY: Fetch from RTDB (reliable, no auth needed)
  try {
    const rtdbUrl = `${getRtdbUrl('public/latestRelease')}&t=${Date.now()}`;
    const response = await fetch(rtdbUrl, { cache: 'no-store' });

    if (response.ok) {
      const data = await response.json();
      if (data && data.downloadUrl) {
        logger.info('Release metadata loaded from RTDB');
        return data;
      }
    }
  } catch (error) {
    logger.warn('RTDB fetch failed, trying Storage fallback:', error.message);
  }

  // FALLBACK: Fetch from Firebase Storage
  try {
    const cacheBuster = `t=${Date.now()}`;
    const metadataUrl = `${getFirebaseStorageUrl('latest.json')}?alt=media&${cacheBuster}`;

    const response = await fetch(metadataUrl, { cache: 'no-store' });

    if (!response.ok) {
      throw new Error(`Failed to fetch metadata: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    logger.warn('Could not fetch latest.json metadata:', error.message);
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
    logger.info(`Starting download: ${filename} from ${url}`);

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

    logger.info(`Download initiated: ${filename}`);
  } catch (error) {
    logger.error('Download failed:', error);
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
    logger.info(`Starting download: ${filename}`);

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

    logger.info(`Download initiated: ${filename}`);
  } catch (error) {
    logger.error('Download failed:', error);
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
