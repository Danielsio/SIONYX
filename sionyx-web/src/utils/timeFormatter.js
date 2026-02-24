/**
 * Time Formatter with Hebrew unit labels
 */

/**
 * Format time in seconds to a human-readable Hebrew string.
 * @param {number} seconds - Time in seconds
 * @returns {string} - e.g. "7 שעות ו-28 דקות" or "45 דקות" or "30 שניות"
 */
export const formatTimeSimple = seconds => {
  if (!seconds || seconds <= 0) return '0 דקות';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0 && minutes > 0) return `${hours} שעות ו-${minutes} דקות`;
  if (hours > 0) return `${hours} שעות`;
  if (minutes > 0 && secs > 0) return `${minutes} דקות ו-${secs} שניות`;
  if (minutes > 0) return `${minutes} דקות`;
  return `${secs} שניות`;
};

/**
 * Format time in minutes to a human-readable Hebrew string.
 * @param {number} minutes - Time in minutes
 * @returns {string} - e.g. "167 שעות ו-20 דקות" or "45 דקות"
 */
export const formatMinutesSimple = minutes => {
  if (!minutes || minutes <= 0) return '0 דקות';

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  if (hours > 0 && remainingMinutes > 0) return `${hours} שעות ו-${remainingMinutes} דקות`;
  if (hours > 0) return `${hours} שעות`;
  return `${remainingMinutes} דקות`;
};

export const formatMinutesHebrew = formatMinutesSimple;
export const formatTimeHebrewCompact = formatTimeSimple;
