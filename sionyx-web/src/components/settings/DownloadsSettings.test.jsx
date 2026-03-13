import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App as AntApp } from 'antd';
import DownloadsSettings from './DownloadsSettings';
import { getLatestRelease, downloadFile } from '../../services/downloadService';

vi.mock('../../services/downloadService');
vi.mock('@ant-design/icons', async importOriginal => {
  const actual = await importOriginal();
  return {
    ...actual,
    CloudDownloadOutlined: (props) => <span {...props} data-testid="cloud-download-icon" />,
  };
});
vi.mock('../../hooks/useOrgId', () => ({
  useOrgId: () => 'my-org',
}));

const mockReleaseInfo = {
  version: '2.0.0',
  downloadUrl: 'https://example.com/sionyx-installer.exe',
  fileName: 'sionyx-installer-v2.0.0.exe',
  releaseDate: '2025-01-01T10:00:00Z',
  fileSize: 123456789,
  buildNumber: 42,
  changelog: ['שיפור ביצועים', 'תיקוני באגים'],
};

const renderDownloadsSettings = () => {
  getLatestRelease.mockResolvedValue(mockReleaseInfo);
  downloadFile.mockResolvedValue(undefined);

  return render(
    <AntApp>
      <DownloadsSettings />
    </AntApp>
  );
};

describe('DownloadsSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads latest release info on mount', async () => {
    renderDownloadsSettings();

    await waitFor(() => {
      expect(getLatestRelease).toHaveBeenCalled();
    });
  });

  it('displays release metadata and download button', async () => {
    renderDownloadsSettings();

    await waitFor(() => {
      expect(screen.getAllByText(/גרסה/).length).toBeGreaterThan(0);
    });

    expect(screen.getByText(mockReleaseInfo.fileName)).toBeInTheDocument();
    expect(screen.getByText(/הורד תוכנה/)).toBeInTheDocument();
  });

  it('invokes downloadFile when clicking download', async () => {
    const user = userEvent.setup();
    renderDownloadsSettings();

    await waitFor(() => {
      expect(screen.getByText(/הורד תוכנה/)).toBeInTheDocument();
    });

    const button = screen.getByRole('button', { name: /הורד תוכנה/ });
    await user.click(button);

    await waitFor(() => {
      expect(downloadFile).toHaveBeenCalledWith(
        mockReleaseInfo.downloadUrl,
        mockReleaseInfo.fileName
      );
    });
  });
});

