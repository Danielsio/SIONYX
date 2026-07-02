import { Typography } from 'antd';

const { Title, Text } = Typography;

/**
 * Standard page header: title + optional subtitle on the right (RTL),
 * actions on the left. First piece of the shared component kit — every page
 * re-implemented this block with drifting inline styles; index.css already
 * carries responsive rules for the `page-header` class.
 */
const PageHeader = ({ title, subtitle, actions = null }) => (
  <div
    className='page-header'
    style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      flexWrap: 'wrap',
      gap: 16,
    }}
  >
    <div>
      <Title level={2} style={{ margin: 0, fontWeight: 700 }}>
        {title}
      </Title>
      {subtitle && (
        <Text type='secondary' style={{ fontSize: 14 }}>
          {subtitle}
        </Text>
      )}
    </div>
    {actions && <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>{actions}</div>}
  </div>
);

export default PageHeader;
