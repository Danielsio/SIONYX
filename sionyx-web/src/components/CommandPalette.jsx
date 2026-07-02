import { useEffect, useMemo, useRef, useState } from 'react';
import { Input, Modal, Typography, Empty } from 'antd';
import { SearchOutlined, EnterOutlined } from '@ant-design/icons';

const { Text } = Typography;

/**
 * ⌘K / Ctrl+K command palette: jump to a page or run a dynamic command
 * (e.g. find a user). Static commands come from the shell's nav config;
 * `getDynamicCommands(query)` lets each console add live results.
 */
const CommandPalette = ({ open, onClose, commands = [], getDynamicCommands }) => {
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setQuery('');
      setActiveIndex(0);
      // Focus after the modal finishes mounting.
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    const staticMatches = q
      ? commands.filter(
          c =>
            c.label.toLowerCase().includes(q) ||
            (c.keywords || '').toLowerCase().includes(q)
        )
      : commands;
    const dynamicMatches = q && getDynamicCommands ? getDynamicCommands(query.trim()) : [];
    return [...dynamicMatches, ...staticMatches].slice(0, 8);
  }, [query, commands, getDynamicCommands]);

  useEffect(() => {
    setActiveIndex(0);
  }, [results.length]);

  const run = command => {
    onClose();
    command.onSelect();
  };

  const onKeyDown = e => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(i => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(i => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && results[activeIndex]) {
      e.preventDefault();
      run(results[activeIndex]);
    }
  };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      closable={false}
      width={560}
      style={{ top: 96 }}
      styles={{ body: { padding: 12 } }}
      destroyOnHidden
    >
      <Input
        ref={inputRef}
        size='large'
        prefix={<SearchOutlined />}
        placeholder='חיפוש מהיר: עמוד, משתמש, פעולה…'
        value={query}
        onChange={e => setQuery(e.target.value)}
        onKeyDown={onKeyDown}
        variant='borderless'
        aria-label='חיפוש מהיר'
      />
      <div style={{ marginTop: 8, maxHeight: 360, overflowY: 'auto' }} role='listbox'>
        {results.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description='אין תוצאות' />
        ) : (
          results.map((command, index) => (
            <div
              key={command.key}
              role='option'
              aria-selected={index === activeIndex}
              onMouseEnter={() => setActiveIndex(index)}
              onClick={() => run(command)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 12px',
                borderRadius: 8,
                cursor: 'pointer',
                background: index === activeIndex ? 'rgba(102, 126, 234, 0.12)' : 'transparent',
              }}
            >
              {command.icon}
              <div style={{ flex: 1, minWidth: 0 }}>
                <Text style={{ display: 'block' }} ellipsis>
                  {command.label}
                </Text>
                {command.hint && (
                  <Text type='secondary' style={{ fontSize: 12 }}>
                    {command.hint}
                  </Text>
                )}
              </div>
              {index === activeIndex && <EnterOutlined style={{ opacity: 0.45 }} />}
            </div>
          ))
        )}
      </div>
    </Modal>
  );
};

export default CommandPalette;
