import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App as AntApp } from 'antd';
import OperatingHoursSettings from './OperatingHoursSettings';
import { getOperatingHours, updateOperatingHours, DEFAULT_OPERATING_HOURS } from '../../services/settingsService';

vi.mock('../../services/settingsService');
const mockUseOrgId = vi.fn(() => 'my-org');
vi.mock('../../hooks/useOrgId', () => ({
  useOrgId: (...args) => mockUseOrgId(...args),
}));

// Mock dayjs with all methods required by Ant Design TimePicker
vi.mock('dayjs', () => {
  const createDayjsInstance = (date) => {
    const instance = {
      format: (fmt) => (typeof date === 'string' ? date : '06:00'),
      isValid: () => true,
      hour: () => 6,
      minute: () => 0,
      second: () => 0,
      millisecond: () => 0,
      valueOf: () => Date.now(),
      toDate: () => new Date(),
      clone: () => createDayjsInstance(date),
      add: () => createDayjsInstance(date),
      subtract: () => createDayjsInstance(date),
      isSame: () => true,
      isBefore: () => false,
      isAfter: () => false,
      startOf: () => createDayjsInstance(date),
      endOf: () => createDayjsInstance(date),
      set: () => createDayjsInstance(date),
      get: () => 0,
      locale: () => createDayjsInstance(date),
      $L: 'en',
      $d: new Date(),
      $isDayjsObject: true,
    };
    return instance;
  };
  
  const dayjs = (date) => createDayjsInstance(date);
  dayjs.isDayjs = (obj) => obj && obj.$isDayjsObject === true;
  dayjs.extend = () => {};
  dayjs.locale = () => {};
  return { default: dayjs };
});

describe('OperatingHoursSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');

    getOperatingHours.mockResolvedValue({
      success: true,
      operatingHours: { ...DEFAULT_OPERATING_HOURS },
    });

    updateOperatingHours.mockResolvedValue({ success: true });
  });

  it('renders settings form', async () => {
    render(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getOperatingHours).toHaveBeenCalled();
    });

    expect(screen.getByText('הפעל הגבלת שעות פעילות')).toBeInTheDocument();
  });

  it('loads operating hours on mount', async () => {
    render(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getOperatingHours).toHaveBeenCalledWith('my-org');
    });
  });

  it('shows supervisor warning', async () => {
    render(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    expect(screen.getByText('הגדרות מפקח בלבד')).toBeInTheDocument();
  });

  it('shows current status section', async () => {
    render(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getOperatingHours).toHaveBeenCalled();
    });

    expect(screen.getByText('מצב נוכחי')).toBeInTheDocument();
    // There are multiple "מושבת" elements (tag and switch), check at least one exists
    expect(screen.getAllByText('מושבת').length).toBeGreaterThan(0);
  });

  it('shows enabled status when enabled', async () => {
    getOperatingHours.mockResolvedValue({
      success: true,
      operatingHours: {
        ...DEFAULT_OPERATING_HOURS,
        enabled: true,
      },
    });

    render(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(screen.getByText('מופעל')).toBeInTheDocument();
    });
  });

  it('has refresh button', async () => {
    render(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getOperatingHours).toHaveBeenCalled();
    });

    expect(screen.getByText('רענן')).toBeInTheDocument();
  });

  it('refreshes when refresh clicked', async () => {
    const user = userEvent.setup();

    render(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getOperatingHours).toHaveBeenCalledTimes(1);
    });

    await user.click(screen.getByText('רענן'));

    await waitFor(() => {
      expect(getOperatingHours).toHaveBeenCalledTimes(2);
    });
  });

  it('has save and reset buttons', async () => {
    render(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getOperatingHours).toHaveBeenCalled();
    });

    expect(screen.getByText('שמור שינויים')).toBeInTheDocument();
    expect(screen.getByText('איפוס')).toBeInTheDocument();
  });

  it('shows grace behavior options', async () => {
    render(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getOperatingHours).toHaveBeenCalled();
    });

    expect(screen.getByText('סיום רגיל')).toBeInTheDocument();
    expect(screen.getByText('סגירה מיידית')).toBeInTheDocument();
  });

  it('shows explanation section', async () => {
    render(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    expect(screen.getByText('הסבר')).toBeInTheDocument();
  });

  it('handles load error', async () => {
    getOperatingHours.mockResolvedValue({
      success: false,
      error: 'Failed to load',
    });

    render(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getOperatingHours).toHaveBeenCalled();
    });

    // Should not crash
    expect(screen.getByText('עדכן הגדרות')).toBeInTheDocument();
  });

  it('reloads data when orgId changes from null to a value', async () => {
    mockUseOrgId.mockReturnValue(null);

    getOperatingHours.mockResolvedValue({
      success: true,
      operatingHours: DEFAULT_OPERATING_HOURS,
    });

    const { rerender } = render(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    await new Promise(r => setTimeout(r, 50));
    expect(getOperatingHours).not.toHaveBeenCalled();

    mockUseOrgId.mockReturnValue('my-org');

    rerender(
      <AntApp>
        <OperatingHoursSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getOperatingHours).toHaveBeenCalledWith('my-org');
    });
  });
});
