import { describe, it, expect } from 'vitest';
import {
  formatTimeSimple,
  formatMinutesSimple,
  formatMinutesHebrew,
  formatTimeHebrewCompact,
} from './timeFormatter';

describe('timeFormatter', () => {
  describe('formatTimeSimple', () => {
    it('returns "0:00:00" for 0 seconds', () => {
      expect(formatTimeSimple(0)).toBe('0:00:00');
    });

    it('returns "0:00:00" for null/undefined', () => {
      expect(formatTimeSimple(null)).toBe('0:00:00');
      expect(formatTimeSimple(undefined)).toBe('0:00:00');
    });

    it('formats seconds correctly', () => {
      expect(formatTimeSimple(45)).toBe('0:00:45');
    });

    it('formats minutes and seconds correctly', () => {
      expect(formatTimeSimple(125)).toBe('0:02:05'); // 2 min 5 sec
    });

    it('formats hours, minutes and seconds correctly', () => {
      expect(formatTimeSimple(3661)).toBe('1:01:01'); // 1 hr 1 min 1 sec
    });

    it('formats large hours correctly', () => {
      expect(formatTimeSimple(36000)).toBe('10:00:00'); // 10 hours
    });

    it('pads minutes and seconds with leading zeros', () => {
      expect(formatTimeSimple(3605)).toBe('1:00:05'); // 1 hr 0 min 5 sec
    });

    it('handles exact hour boundaries', () => {
      expect(formatTimeSimple(3600)).toBe('1:00:00'); // exactly 1 hour
      expect(formatTimeSimple(7200)).toBe('2:00:00'); // exactly 2 hours
    });

    it('handles the example from docs: 7:28:40', () => {
      // 7 hours * 3600 + 28 minutes * 60 + 40 seconds = 26920
      expect(formatTimeSimple(26920)).toBe('7:28:40');
    });
  });

  describe('formatMinutesSimple', () => {
    it('returns "0:00" for 0 minutes', () => {
      expect(formatMinutesSimple(0)).toBe('0:00');
    });

    it('returns "0:00" for null/undefined', () => {
      expect(formatMinutesSimple(null)).toBe('0:00');
      expect(formatMinutesSimple(undefined)).toBe('0:00');
    });

    it('formats minutes under an hour correctly', () => {
      expect(formatMinutesSimple(45)).toBe('0:45');
    });

    it('formats exact hours correctly', () => {
      expect(formatMinutesSimple(60)).toBe('1:00');
      expect(formatMinutesSimple(120)).toBe('2:00');
    });

    it('formats hours and minutes correctly', () => {
      expect(formatMinutesSimple(90)).toBe('1:30'); // 1.5 hours
      expect(formatMinutesSimple(150)).toBe('2:30'); // 2.5 hours
    });

    it('pads minutes with leading zeros', () => {
      expect(formatMinutesSimple(65)).toBe('1:05');
      expect(formatMinutesSimple(601)).toBe('10:01');
    });

    it('handles large values', () => {
      expect(formatMinutesSimple(1440)).toBe('24:00'); // 24 hours
      expect(formatMinutesSimple(2880)).toBe('48:00'); // 48 hours
    });

    it('handles the example from docs: 7:28', () => {
      expect(formatMinutesSimple(448)).toBe('7:28'); // 7 * 60 + 28 = 448
    });
  });

  describe('backward compatibility aliases', () => {
    it('formatMinutesHebrew is an alias for formatMinutesSimple', () => {
      expect(formatMinutesHebrew).toBe(formatMinutesSimple);
      expect(formatMinutesHebrew(90)).toBe('1:30');
    });

    it('formatTimeHebrewCompact is an alias for formatTimeSimple', () => {
      expect(formatTimeHebrewCompact).toBe(formatTimeSimple);
      expect(formatTimeHebrewCompact(3661)).toBe('1:01:01');
    });
  });
});


