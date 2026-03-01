import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App as AntApp } from 'antd';
import AnnouncementsPage from './AnnouncementsPage';
import { getAllAnnouncements } from '../services/announcementService';

vi.mock('../services/announcementService');
const mockUseOrgId = vi.fn(() => 'my-org');
vi.mock('../hooks/useOrgId', () => ({
  useOrgId: (...args) => mockUseOrgId(...args),
}));

// Mock dayjs with controllable "now" for schedule status tests
const MOCK_NOW = new Date('2024-06-15T12:00:00Z');
vi.mock('dayjs', () => {
  const dayjs = date => {
    const d = date ? new Date(date) : MOCK_NOW;
    const dayjsObj = {
      format: fmt => (fmt === 'DD/MM/YYYY HH:mm' ? '15/06/2024 12:00' : '15/06/2024'),
      fromNow: () => 'לפני שעה',
      isValid: () => true,
      isBefore: other => {
        const otherDate = other?.toDate ? other.toDate() : other ? new Date(other) : null;
        return otherDate && d.getTime() < otherDate.getTime();
      },
      isAfter: other => {
        const otherDate = other?.toDate ? other.toDate() : other ? new Date(other) : null;
        return otherDate && d.getTime() > otherDate.getTime();
      },
      toISOString: () => d.toISOString(),
      toDate: () => d,
    };
    return dayjsObj;
  };
  dayjs.extend = () => {};
  dayjs.locale = () => {};
  return { default: dayjs };
});

const renderAnnouncementsPage = () =>
  render(
    <AntApp>
      <AnnouncementsPage />
    </AntApp>
  );

describe('AnnouncementsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getAllAnnouncements.mockResolvedValue({ success: true, announcements: [] });
  });

  it('renders without crashing', async () => {
    renderAnnouncementsPage();
    await waitFor(() => {
      expect(getAllAnnouncements).toHaveBeenCalledWith('my-org');
    });
    expect(document.body).toBeInTheDocument();
  });

  it('displays page title', async () => {
    renderAnnouncementsPage();
    await waitFor(() => {
      expect(getAllAnnouncements).toHaveBeenCalled();
    });
    expect(screen.getByRole('heading', { name: /הודעות מערכת/ })).toBeInTheDocument();
  });

  it('shows schedule status tag מתוזמן for scheduled announcement (startDate in future)', async () => {
    getAllAnnouncements.mockResolvedValue({
      success: true,
      announcements: [
        {
          id: '1',
          title: 'Scheduled',
          body: 'Body',
          type: 'info',
          active: true,
          startDate: '2024-08-01T00:00:00Z',
          endDate: null,
          createdAt: '2024-01-01T00:00:00Z',
        },
      ],
    });

    renderAnnouncementsPage();
    await waitFor(() => {
      expect(getAllAnnouncements).toHaveBeenCalled();
    });

    expect(screen.getByText('מתוזמן')).toBeInTheDocument();
  });

  it('shows schedule status tag פעיל for active announcement', async () => {
    getAllAnnouncements.mockResolvedValue({
      success: true,
      announcements: [
        {
          id: '1',
          title: 'Active',
          body: 'Body',
          type: 'info',
          active: true,
          startDate: '2024-01-01T00:00:00Z',
          endDate: '2024-12-31T00:00:00Z',
          createdAt: '2024-01-01T00:00:00Z',
        },
      ],
    });

    renderAnnouncementsPage();
    await waitFor(() => {
      expect(getAllAnnouncements).toHaveBeenCalled();
    });

    expect(screen.getByText('פעיל')).toBeInTheDocument();
  });

  it('shows schedule status tag פג תוקף for expired announcement', async () => {
    getAllAnnouncements.mockResolvedValue({
      success: true,
      announcements: [
        {
          id: '1',
          title: 'Expired',
          body: 'Body',
          type: 'info',
          active: true,
          startDate: '2024-01-01T00:00:00Z',
          endDate: '2024-03-01T00:00:00Z',
          createdAt: '2024-01-01T00:00:00Z',
        },
      ],
    });

    renderAnnouncementsPage();
    await waitFor(() => {
      expect(getAllAnnouncements).toHaveBeenCalled();
    });

    expect(screen.getByText('פג תוקף')).toBeInTheDocument();
  });

  it('shows schedule status tag מושהה for paused announcement', async () => {
    getAllAnnouncements.mockResolvedValue({
      success: true,
      announcements: [
        {
          id: '1',
          title: 'Paused',
          body: 'Body',
          type: 'info',
          active: false,
          startDate: null,
          endDate: null,
          createdAt: '2024-01-01T00:00:00Z',
        },
      ],
    });

    renderAnnouncementsPage();
    await waitFor(() => {
      expect(getAllAnnouncements).toHaveBeenCalled();
    });

    expect(screen.getByText('מושהה')).toBeInTheDocument();
  });

  it('shows date pickers when creating new announcement', async () => {
    const user = userEvent.setup();
    renderAnnouncementsPage();

    await waitFor(() => {
      expect(getAllAnnouncements).toHaveBeenCalled();
    });

    await user.click(screen.getByText('הודעה חדשה'));

    await waitFor(() => {
      expect(screen.getByText('תאריך התחלה')).toBeInTheDocument();
      expect(screen.getByText('תאריך סיום')).toBeInTheDocument();
    });
  });

  it('displays scheduled date range on card when startDate and endDate exist', async () => {
    getAllAnnouncements.mockResolvedValue({
      success: true,
      announcements: [
        {
          id: '1',
          title: 'Scheduled Range',
          body: 'Body',
          type: 'info',
          active: true,
          startDate: '2024-07-01T00:00:00Z',
          endDate: '2024-08-01T00:00:00Z',
          createdAt: '2024-01-01T00:00:00Z',
        },
      ],
    });

    renderAnnouncementsPage();
    await waitFor(() => {
      expect(getAllAnnouncements).toHaveBeenCalled();
    });

    expect(document.body.textContent).toMatch(/מ־|עד/);
  });
});
