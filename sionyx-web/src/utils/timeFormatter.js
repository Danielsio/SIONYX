/**
 * Simple Time Formatter
 * Formats time in simple HH:MM:SS format like "7:28:40"
 */

/**
 * Format time in seconds to simple HH:MM:SS format
 * @param {number} seconds - Time in seconds
 * @returns {string} - Formatted time like "7:28:40"
 */
export const formatTimeSimple = seconds => {
  if (!seconds || seconds === 0) return '0:00:00';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;

  return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
};

/**
 * Format time in minutes to simple HH:MM format
 * @param {number} minutes - Time in minutes
 * @returns {string} - Formatted time like "7:28"
 */
export const formatMinutesSimple = minutes => {
  if (!minutes || minutes === 0) return '0:00';

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  return `${hours}:${remainingMinutes.toString().padStart(2, '0')}`;
};

// Keep the old functions for backward compatibility but mark as deprecated
export const formatMinutesHebrew = formatMinutesSimple;
export const formatTimeHebrewCompact = formatTimeSimple;
