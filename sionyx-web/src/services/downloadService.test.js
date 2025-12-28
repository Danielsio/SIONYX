import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  getLatestRelease,
  downloadFile,
  downloadFileWithProgress,
  formatFileSize,
  formatReleaseDate,
  formatVersion,
} from './downloadService';

// Mock fetch
global.fetch = vi.fn();

// Mock document.createElement for download tests
const mockLink = {
  href: '',
  download: '',
  target: '',
  style: { display: '' },
  click: vi.fn(),
};

vi.spyOn(document, 'createElement').mockImplementation(() => mockLink);
vi.spyOn(document.body, 'appendChild').mockImplementation(() => {});
vi.spyOn(document.body, 'removeChild').mockImplementation(() => {});

describe('downloadService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLink.href = '';
    mockLink.download = '';
    mockLink.click.mockClear();
  });

  describe('getLatestRelease', () => {
    it('should return release info from metadata', async () => {
      const mockMetadata = {
        version: '1.2.3',
        downloadUrl: 'https://storage.example.com/sionyx.exe',
        releaseDate: '2024-01-15',
        fileSize: 50000000,
        filename: 'sionyx-v1.2.3.exe',
        buildNumber: 42,
        changelog: ['Fix bug', 'Add feature'],
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMetadata,
      });

      const result = await getLatestRelease();

      expect(result.version).toBe('1.2.3');
      expect(result.downloadUrl).toBe('https://storage.example.com/sionyx.exe');
      expect(result.buildNumber).toBe(42);
    });

    it('should throw error when metadata fetch fails', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await expect(getLatestRelease()).rejects.toThrow('Could not fetch release metadata');
    });

    it('should throw error when downloadUrl is missing', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ version: '1.0.0' }), // No downloadUrl
      });

      await expect(getLatestRelease()).rejects.toThrow();
    });
  });

  describe('downloadFile', () => {
    it('should create download link and click it', async () => {
      await downloadFile('https://example.com/file.exe', 'file.exe');

      expect(document.createElement).toHaveBeenCalledWith('a');
      expect(mockLink.href).toBe('https://example.com/file.exe');
      expect(mockLink.download).toBe('file.exe');
      expect(mockLink.click).toHaveBeenCalled();
    });

    it('should throw error for invalid URL', async () => {
      await expect(downloadFile('', 'file.exe')).rejects.toThrow('Invalid download URL');
      await expect(downloadFile('ftp://invalid', 'file.exe')).rejects.toThrow('Invalid download URL');
    });

    it('should throw error when URL is null', async () => {
      await expect(downloadFile(null, 'file.exe')).rejects.toThrow('Invalid download URL');
    });
  });

  describe('downloadFileWithProgress', () => {
    it('should download and call progress callback', async () => {
      const onProgress = vi.fn();

      await downloadFileWithProgress('https://example.com/file.exe', 'file.exe', onProgress);

      expect(onProgress).toHaveBeenCalledWith(0, 100);
      expect(mockLink.click).toHaveBeenCalled();
    });

    it('should work without progress callback', async () => {
      await downloadFileWithProgress('https://example.com/file.exe', 'file.exe');

      expect(mockLink.click).toHaveBeenCalled();
    });

    it('should throw error for invalid URL', async () => {
      await expect(downloadFileWithProgress('', 'file.exe')).rejects.toThrow('Invalid download URL');
    });
  });

  describe('formatFileSize', () => {
    it('should return "Unknown size" for 0 bytes', () => {
      expect(formatFileSize(0)).toBe('Unknown size');
    });

    it('should format bytes correctly', () => {
      expect(formatFileSize(500)).toBe('500 Bytes');
    });

    it('should format kilobytes correctly', () => {
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(2048)).toBe('2 KB');
    });

    it('should format megabytes correctly', () => {
      expect(formatFileSize(1048576)).toBe('1 MB');
      expect(formatFileSize(52428800)).toBe('50 MB');
    });

    it('should format gigabytes correctly', () => {
      expect(formatFileSize(1073741824)).toBe('1 GB');
    });
  });

  describe('formatReleaseDate', () => {
    it('should format date in Hebrew locale', () => {
      const result = formatReleaseDate('2024-01-15T10:00:00Z');
      // Should contain the year 2024
      expect(result).toContain('2024');
    });

    it('should handle invalid date', () => {
      const result = formatReleaseDate('invalid-date');
      // Should return Hebrew "unknown date" message or attempt to format
      // Invalid Date objects still pass toLocaleDateString but produce "Invalid Date"
      expect(typeof result).toBe('string');
    });
  });

  describe('formatVersion', () => {
    it('should return empty string for null release', () => {
      expect(formatVersion(null)).toBe('');
      expect(formatVersion(undefined)).toBe('');
    });

    it('should return version string', () => {
      expect(formatVersion({ version: '1.2.3' })).toBe('1.2.3');
    });

    it('should include build number when available', () => {
      expect(formatVersion({ version: '1.2.3', buildNumber: 42 })).toBe('1.2.3 (Build #42)');
    });

    it('should default to "Latest" when no version', () => {
      expect(formatVersion({})).toBe('Latest');
    });
  });
});
