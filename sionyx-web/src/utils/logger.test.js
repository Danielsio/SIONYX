import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

describe('logger', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should export a logger object with all log methods', async () => {
    const { logger } = await import('./logger');
    expect(logger).toBeDefined();
    expect(typeof logger.debug).toBe('function');
    expect(typeof logger.info).toBe('function');
    expect(typeof logger.warn).toBe('function');
    expect(typeof logger.error).toBe('function');
  });

  it('debug should not throw when called', async () => {
    const { logger } = await import('./logger');
    expect(() => logger.debug('test debug')).not.toThrow();
  });

  it('info should not throw when called', async () => {
    const { logger } = await import('./logger');
    expect(() => logger.info('test info')).not.toThrow();
  });

  it('warn should call console.warn in any environment', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const { logger } = await import('./logger');
    logger.warn('test warning', { detail: 'extra' });
    expect(warnSpy).toHaveBeenCalledWith('[WARN]', 'test warning', { detail: 'extra' });
  });

  it('error should call console.error in any environment', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { logger } = await import('./logger');
    logger.error('test error', new Error('fail'));
    expect(errorSpy).toHaveBeenCalled();
    expect(errorSpy.mock.calls[0][0]).toBe('[ERROR]');
    expect(errorSpy.mock.calls[0][1]).toBe('test error');
  });

  it('warn should accept multiple arguments', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const { logger } = await import('./logger');
    logger.warn('a', 'b', 'c');
    expect(warnSpy).toHaveBeenCalledWith('[WARN]', 'a', 'b', 'c');
  });

  it('error should accept multiple arguments', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { logger } = await import('./logger');
    logger.error('msg1', 'msg2');
    expect(errorSpy).toHaveBeenCalledWith('[ERROR]', 'msg1', 'msg2');
  });

  it('all methods should be callable without arguments', async () => {
    vi.spyOn(console, 'debug').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
    const { logger } = await import('./logger');
    expect(() => {
      logger.debug();
      logger.info();
      logger.warn();
      logger.error();
    }).not.toThrow();
  });
});
