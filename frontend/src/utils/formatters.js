/**
 * Utility Functions for Formatting
 * Version: 1.0.0
 * Last Updated: 2025-11-17
 *
 * Changelog:
 * ----------
 * v1.0.0 (2025-11-17):
 *   - Initial utility functions for formatting
 *   - Currency formatting (INR ₹)
 *   - Number formatting
 *   - Date formatting
 */

/**
 * Format number as INR currency
 * @param {number|string} amount - Amount to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted currency string with ₹ symbol
 */
export function formatCurrency(amount, decimals = 2) {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '₹0.00';
  }

  const num = typeof amount === 'string' ? parseFloat(amount) : amount;

  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}

/**
 * Format number with Indian numbering system (lakhs, crores)
 * @param {number|string} num - Number to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted number string
 */
export function formatNumber(num, decimals = 2) {
  if (num === null || num === undefined || isNaN(num)) {
    return '0';
  }

  const number = typeof num === 'string' ? parseFloat(num) : num;

  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(number);
}

/**
 * Format number with Indian numbering system, no decimals
 * @param {number|string} num - Number to format
 * @returns {string} Formatted number string
 */
export function formatWholeNumber(num) {
  return formatNumber(num, 0);
}

/**
 * Format date in DD/MM/YYYY format
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date string
 */
export function formatDate(date) {
  if (!date) return '';

  const d = new Date(date);
  if (isNaN(d.getTime())) return '';

  return d.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

/**
 * Format date in DD MMM YYYY format (e.g., 17 Nov 2025)
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date string
 */
export function formatDateLong(date) {
  if (!date) return '';

  const d = new Date(date);
  if (isNaN(d.getTime())) return '';

  return d.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

/**
 * Format date and time
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date and time string
 */
export function formatDateTime(date) {
  if (!date) return '';

  const d = new Date(date);
  if (isNaN(d.getTime())) return '';

  return d.toLocaleString('en-IN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });
}

/**
 * Format quantity with unit
 * @param {number|string} qty - Quantity
 * @param {string} unit - Unit of measurement (e.g., kg, liters, pieces)
 * @returns {string} Formatted quantity string
 */
export function formatQuantity(qty, unit) {
  if (qty === null || qty === undefined || isNaN(qty)) {
    return `0 ${unit || ''}`;
  }

  const num = typeof qty === 'string' ? parseFloat(qty) : qty;
  const formatted = formatNumber(num, 2);

  return unit ? `${formatted} ${unit}` : formatted;
}

/**
 * Format percentage
 * @param {number|string} value - Value to format as percentage
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted percentage string
 */
export function formatPercentage(value, decimals = 1) {
  if (value === null || value === undefined || isNaN(value)) {
    return '0%';
  }

  const num = typeof value === 'string' ? parseFloat(value) : value;

  return `${num.toFixed(decimals)}%`;
}

export default {
  formatCurrency,
  formatNumber,
  formatWholeNumber,
  formatDate,
  formatDateLong,
  formatDateTime,
  formatQuantity,
  formatPercentage,
};
