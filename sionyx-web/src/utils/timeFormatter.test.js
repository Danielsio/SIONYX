import { describe, it, expect } from 'vitest';
import {
  formatTimeSimple,
  formatMinutesSimple,
  formatMinutesHebrew,
  formatTimeHebrewCompact,
} from './timeFormatter';

describe('timeFormatter', () => {
  describe('formatTimeSimple', () => {
    it('returns "0 דקות" for 0 seconds', () => {
      expect(formatTimeSimple(0)).toBe('0 דקות');
    });

    it('returns "0 דקות" for null/undefined', () => {
      expect(formatTimeSimple(null)).toBe('0 דקות');
      expect(formatTimeSimple(undefined)).toBe('0 דקות');
    });

    it('formats seconds only', () => {
      expect(formatTimeSimple(45)).toBe('45 שניות');
    });

    it('formats minutes and seconds', () => {
      expect(formatTimeSimple(125)).toBe('2 דקות ו-5 שניות');
    });

    it('formats hours and minutes', () => {
      expect(formatTimeSimple(3661)).toBe('1 שעות ו-1 דקות');
    });

    it('formats exact hours', () => {
      expect(formatTimeSimple(3600)).toBe('1 שעות');
      expect(formatTimeSimple(7200)).toBe('2 שעות');
    });

    it('formats large values', () => {
      expect(formatTimeSimple(36000)).toBe('10 שעות');
    });

    it('formats minutes without seconds', () => {
      expect(formatTimeSimple(300)).toBe('5 דקות');
    });
  });

  describe('formatMinutesSimple', () => {
    it('returns "0 דקות" for 0 minutes', () => {
      expect(formatMinutesSimple(0)).toBe('0 דקות');
    });

    it('returns "0 דקות" for null/undefined', () => {
      expect(formatMinutesSimple(null)).toBe('0 דקות');
      expect(formatMinutesSimple(undefined)).toBe('0 דקות');
    });

    it('formats minutes under an hour', () => {
      expect(formatMinutesSimple(45)).toBe('45 דקות');
    });

    it('formats exact hours', () => {
      expect(formatMinutesSimple(60)).toBe('1 שעות');
      expect(formatMinutesSimple(120)).toBe('2 שעות');
    });

    it('formats hours and minutes', () => {
      expect(formatMinutesSimple(90)).toBe('1 שעות ו-30 דקות');
      expect(formatMinutesSimple(150)).toBe('2 שעות ו-30 דקות');
    });

    it('handles large values', () => {
      expect(formatMinutesSimple(1440)).toBe('24 שעות');
      expect(formatMinutesSimple(2880)).toBe('48 שעות');
    });

    it('formats typical usage', () => {
      expect(formatMinutesSimple(448)).toBe('7 שעות ו-28 דקות');
    });
  });

  describe('backward compatibility aliases', () => {
    it('formatMinutesHebrew is an alias for formatMinutesSimple', () => {
      expect(formatMinutesHebrew).toBe(formatMinutesSimple);
      expect(formatMinutesHebrew(90)).toBe('1 שעות ו-30 דקות');
    });

    it('formatTimeHebrewCompact is an alias for formatTimeSimple', () => {
      expect(formatTimeHebrewCompact).toBe(formatTimeSimple);
      expect(formatTimeHebrewCompact(3661)).toBe('1 שעות ו-1 דקות');
    });
  });
});
