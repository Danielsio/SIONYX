import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App as AntApp } from 'antd';
import NotificationBell from './NotificationBell';
import { useNotificationStore } from '../store/notificationStore';

vi.mock('../store/notificationStore');

describe('NotificationBell', () => {
  const mockMarkAsRead = vi.fn();
  const mockMarkAllAsRead = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    useNotificationStore.mockImplementation(() => ({
      notifications: [],
      unreadCount: 0,
      markAsRead: mockMarkAsRead,
      markAllAsRead: mockMarkAllAsRead,
    }));
  });

  const renderNotificationBell = () =>
    render(
      <AntApp>
        <NotificationBell />
      </AntApp>
    );

  it('renders bell icon', () => {
    renderNotificationBell();
    expect(screen.getByLabelText('התראות')).toBeInTheDocument();
    expect(document.body.textContent).toContain('[BellOutlined]');
  });

  it('shows badge count when notifications exist', () => {
    useNotificationStore.mockImplementation(() => ({
      notifications: [
        { id: '1', message: 'Test', read: false, type: 'message', timestamp: new Date().toISOString() },
      ],
      unreadCount: 1,
      markAsRead: mockMarkAsRead,
      markAllAsRead: mockMarkAllAsRead,
    }));

    renderNotificationBell();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('renders notification list when clicked', async () => {
    const user = userEvent.setup();
    useNotificationStore.mockImplementation(() => ({
      notifications: [
        { id: '1', message: 'הודעה חדשה', read: false, type: 'message', timestamp: new Date().toISOString() },
      ],
      unreadCount: 1,
      markAsRead: mockMarkAsRead,
      markAllAsRead: mockMarkAllAsRead,
    }));

    renderNotificationBell();
    await user.click(screen.getByLabelText('התראות'));

    await waitFor(() => {
      expect(screen.getByText('הודעה חדשה')).toBeInTheDocument();
    });
    expect(screen.getByText('התראות')).toBeInTheDocument();
  });

  it('shows empty state when no notifications', async () => {
    const user = userEvent.setup();
    renderNotificationBell();
    await user.click(screen.getByLabelText('התראות'));

    await waitFor(() => {
      expect(screen.getByText('אין התראות')).toBeInTheDocument();
    });
  });

  it('shows mark all as read button when unread notifications exist', async () => {
    const user = userEvent.setup();
    useNotificationStore.mockImplementation(() => ({
      notifications: [
        { id: '1', message: 'Test', read: false, type: 'message', timestamp: new Date().toISOString() },
      ],
      unreadCount: 1,
      markAsRead: mockMarkAsRead,
      markAllAsRead: mockMarkAllAsRead,
    }));

    renderNotificationBell();
    await user.click(screen.getByLabelText('התראות'));

    await waitFor(() => {
      expect(screen.getByText('סמן הכל כנקרא')).toBeInTheDocument();
    });
  });
});
