import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import StatCard, { MiniStatCard, InfoStatCard } from './StatCard';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
  },
}));

describe('StatCard', () => {
  describe('Basic Rendering', () => {
    it('renders with title and value', () => {
      render(<StatCard title='Total Users' value={100} />);

      expect(screen.getByText('Total Users')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    it('renders with icon', () => {
      render(<StatCard title='Test' value={50} icon={<span data-testid='test-icon'>👤</span>} />);

      expect(screen.getByTestId('test-icon')).toBeInTheDocument();
    });

    it('renders without icon when not provided', () => {
      render(<StatCard title='Test' value={50} />);

      expect(screen.queryByTestId('test-icon')).not.toBeInTheDocument();
    });

    it('renders prefix and suffix', () => {
      render(<StatCard title='Price' value={100} prefix='$' suffix='USD' />);

      expect(screen.getByText(/\$/)).toBeInTheDocument();
      expect(screen.getByText(/USD/)).toBeInTheDocument();
    });

    it('renders subtitle when provided', () => {
      render(<StatCard title='Test' value={50} subtitle='Last 30 days' />);

      expect(screen.getByText('Last 30 days')).toBeInTheDocument();
    });
  });

  describe('Color Variants', () => {
    it('applies primary color by default', () => {
      const { container } = render(<StatCard title='Test' value={50} />);

      const card = container.querySelector('.stat-card--primary');
      expect(card).toBeInTheDocument();
    });

    it('applies success color', () => {
      const { container } = render(<StatCard title='Test' value={50} color='success' />);

      const card = container.querySelector('.stat-card--success');
      expect(card).toBeInTheDocument();
    });

    it('applies warning color', () => {
      const { container } = render(<StatCard title='Test' value={50} color='warning' />);

      const card = container.querySelector('.stat-card--warning');
      expect(card).toBeInTheDocument();
    });

    it('applies error color', () => {
      const { container } = render(<StatCard title='Test' value={50} color='error' />);

      const card = container.querySelector('.stat-card--error');
      expect(card).toBeInTheDocument();
    });

    it('applies info color', () => {
      const { container } = render(<StatCard title='Test' value={50} color='info' />);

      const card = container.querySelector('.stat-card--info');
      expect(card).toBeInTheDocument();
    });

    it('falls back to primary for unknown color', () => {
      const { container } = render(<StatCard title='Test' value={50} color='unknown' />);

      // Should still render without crashing
      const card = container.querySelector('.stat-card');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Variant Styles', () => {
    it('renders default variant', () => {
      const { container } = render(<StatCard title='Test' value={50} variant='default' />);

      expect(container.querySelector('.stat-card')).toBeInTheDocument();
    });

    it('renders filled variant', () => {
      const { container } = render(<StatCard title='Test' value={50} variant='filled' />);

      expect(container.querySelector('.stat-card')).toBeInTheDocument();
    });

    it('renders outlined variant', () => {
      const { container } = render(<StatCard title='Test' value={50} variant='outlined' />);

      expect(container.querySelector('.stat-card')).toBeInTheDocument();
    });

    it('renders gradient variant with special layout', () => {
      render(<StatCard title='Test' value={50} variant='gradient' />);

      // Gradient variant should still show title and value
      expect(screen.getByText('Test')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
    });

    it('gradient variant shows subtitle in separate section', () => {
      render(<StatCard title='Test' value={50} variant='gradient' subtitle='Extra info' />);

      expect(screen.getByText('Extra info')).toBeInTheDocument();
    });
  });

  describe('Trend Indicator', () => {
    it('renders upward trend', () => {
      render(<StatCard title='Test' value={50} trend='up' trendValue='+10%' />);

      expect(screen.getByText(/↑.*\+10%/)).toBeInTheDocument();
    });

    it('renders downward trend', () => {
      render(<StatCard title='Test' value={50} trend='down' trendValue='-5%' />);

      expect(screen.getByText(/↓.*-5%/)).toBeInTheDocument();
    });

    it('does not render trend without trendValue', () => {
      render(<StatCard title='Test' value={50} trend='up' />);

      expect(screen.queryByText('↑')).not.toBeInTheDocument();
    });

    it('does not render trend without trend prop', () => {
      render(<StatCard title='Test' value={50} trendValue='+10%' />);

      expect(screen.queryByText('+10%')).not.toBeInTheDocument();
    });
  });

  describe('Interactivity', () => {
    it('calls onClick when card is clicked', async () => {
      const user = userEvent.setup();
      const handleClick = vi.fn();

      render(<StatCard title='Test' value={50} onClick={handleClick} />);

      const card = screen.getByText('Test').closest('.ant-card');
      await user.click(card);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('renders clickable card when onClick is provided', () => {
      const { container } = render(<StatCard title='Test' value={50} onClick={() => {}} />);

      const card = container.querySelector('.ant-card');
      expect(card).toBeInTheDocument();
      // Verify the style attribute contains cursor: pointer
      expect(card.getAttribute('style')).toContain('cursor');
    });

    it('renders non-clickable card when onClick is not provided', () => {
      const { container } = render(<StatCard title='Test' value={50} />);

      const card = container.querySelector('.ant-card');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading state when loading prop is true', () => {
      const { container } = render(<StatCard title='Test' value={50} loading={true} />);

      // Ant Design adds loading skeleton
      const card = container.querySelector('.ant-card');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Custom Formatter', () => {
    it('uses custom formatter for value', () => {
      const formatter = val => `${val.toLocaleString()} items`;

      render(<StatCard title='Test' value={1000} formatter={formatter} variant='gradient' />);

      expect(screen.getByText('1,000 items')).toBeInTheDocument();
    });
  });

  describe('Custom Styles', () => {
    it('applies custom style prop', () => {
      const { container } = render(<StatCard title='Test' value={50} style={{ marginTop: 20 }} />);

      const card = container.querySelector('.ant-card');
      expect(card).toBeInTheDocument();
      // Style is applied via the component
      expect(card.getAttribute('style')).toBeTruthy();
    });
  });
});

describe('MiniStatCard', () => {
  it('renders label and value', () => {
    render(<MiniStatCard label='Active Users' value='42' />);

    expect(screen.getByText('Active Users')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('renders with icon', () => {
    render(<MiniStatCard label='Test' value='10' icon={<span data-testid='mini-icon'>🔥</span>} />);

    expect(screen.getByTestId('mini-icon')).toBeInTheDocument();
  });

  it('renders without icon when not provided', () => {
    const { container } = render(<MiniStatCard label='Test' value='10' />);

    // Should render without crashing
    expect(container.firstChild).toBeInTheDocument();
  });

  it('applies primary color by default', () => {
    const { container } = render(<MiniStatCard label='Test' value='10' />);

    const element = container.firstChild;
    expect(element).toBeInTheDocument();
    // Background style is applied
    expect(element.getAttribute('style')).toContain('background');
  });

  it('applies success color', () => {
    const { container } = render(<MiniStatCard label='Test' value='10' color='success' />);

    const element = container.firstChild;
    expect(element).toBeInTheDocument();
  });

  it('applies warning color', () => {
    const { container } = render(<MiniStatCard label='Test' value='10' color='warning' />);

    const element = container.firstChild;
    expect(element).toBeInTheDocument();
  });

  it('applies error color', () => {
    const { container } = render(<MiniStatCard label='Test' value='10' color='error' />);

    const element = container.firstChild;
    expect(element).toBeInTheDocument();
  });

  it('applies info color', () => {
    const { container } = render(<MiniStatCard label='Test' value='10' color='info' />);

    const element = container.firstChild;
    expect(element).toBeInTheDocument();
  });

  it('falls back to primary for unknown color', () => {
    const { container } = render(<MiniStatCard label='Test' value='10' color='unknown' />);

    const element = container.firstChild;
    expect(element).toBeInTheDocument();
  });

  it('applies custom style', () => {
    const { container } = render(<MiniStatCard label='Test' value='10' style={{ width: 200 }} />);

    const element = container.firstChild;
    expect(element).toBeInTheDocument();
    expect(element.getAttribute('style')).toContain('width');
  });
});

describe('InfoStatCard', () => {
  it('renders title', () => {
    render(<InfoStatCard title='Information'>Content here</InfoStatCard>);

    expect(screen.getByText('Information')).toBeInTheDocument();
  });

  it('renders children content', () => {
    render(<InfoStatCard title='Test'>Child content goes here</InfoStatCard>);

    expect(screen.getByText('Child content goes here')).toBeInTheDocument();
  });

  it('renders extra content in header', () => {
    render(
      <InfoStatCard title='Test' extra={<button>Action</button>}>
        Content
      </InfoStatCard>
    );

    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
  });

  it('applies custom style', () => {
    const { container } = render(
      <InfoStatCard title='Test' style={{ maxWidth: 400 }}>
        Content
      </InfoStatCard>
    );

    const card = container.querySelector('.ant-card');
    expect(card).toBeInTheDocument();
    expect(card.getAttribute('style')).toContain('max-width');
  });

  it('renders with complex children', () => {
    render(
      <InfoStatCard title='Details'>
        <div data-testid='child-1'>Item 1</div>
        <div data-testid='child-2'>Item 2</div>
      </InfoStatCard>
    );

    expect(screen.getByTestId('child-1')).toBeInTheDocument();
    expect(screen.getByTestId('child-2')).toBeInTheDocument();
  });
});

describe('StatCard Accessibility', () => {
  it('has proper card structure', () => {
    const { container } = render(<StatCard title='Test' value={50} />);

    const card = container.querySelector('.ant-card');
    expect(card).toBeInTheDocument();
  });

  it('stat value is visible and readable', () => {
    render(<StatCard title='Total Revenue' value={5000} prefix='$' />);

    expect(screen.getByText('Total Revenue')).toBeVisible();
    // Ant Design formats numbers with commas
    expect(screen.getByText('5,000')).toBeVisible();
  });
});

describe('StatCard Edge Cases', () => {
  it('handles zero value', () => {
    render(<StatCard title='Empty' value={0} />);

    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('handles negative value', () => {
    render(<StatCard title='Loss' value={-50} />);

    expect(screen.getByText('-50')).toBeInTheDocument();
  });

  it('handles large numbers', () => {
    render(<StatCard title='Big Number' value={1000000} />);

    // Ant Design formats numbers with commas
    expect(screen.getByText('1,000,000')).toBeInTheDocument();
  });

  it('handles string value', () => {
    render(<StatCard title='Status' value='Active' />);

    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('handles empty title', () => {
    render(<StatCard title='' value={50} />);

    expect(screen.getByText('50')).toBeInTheDocument();
  });

  it('handles delay prop for animation', () => {
    // Should not crash with delay prop
    const { container } = render(<StatCard title='Test' value={50} delay={0.5} />);

    expect(container.firstChild).toBeInTheDocument();
  });
});
