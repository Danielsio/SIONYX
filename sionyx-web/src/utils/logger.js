/**
 * Application Logger Utility
 *
 * Centralizes logging with level control and context.
 * In production, only warnings and errors are shown.
 * In development, all log levels are active.
 *
 * Usage:
 *   import { logger } from '../utils/logger';
 *   logger.info('Loaded users', { count: 5 });
 *   logger.error('Failed to load', error);
 */

const isDev = import.meta.env.DEV;

const LEVELS = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

// In production, suppress debug and info logs
const minLevel = isDev ? LEVELS.debug : LEVELS.warn;

const createLogger = () => ({
  debug: (...args) => {
    if (minLevel <= LEVELS.debug) console.debug('[DEBUG]', ...args);
  },
  info: (...args) => {
    if (minLevel <= LEVELS.info) console.log('[INFO]', ...args);
  },
  warn: (...args) => {
    if (minLevel <= LEVELS.warn) console.warn('[WARN]', ...args);
  },
  error: (...args) => {
    if (minLevel <= LEVELS.error) console.error('[ERROR]', ...args);
  },
});

export const logger = createLogger();
