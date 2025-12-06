/**
 * Date Utility Functions
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Utilities for date formatting and validation
 */

/**
 * Format date to DD/MM/YYYY (Indian format) for display
 */
export const formatDateForDisplay = (dateString: string): string => {
    if (!dateString) return '';

    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();

    return `${day}/${month}/${year}`;
};

/**
 * Format date to YYYY-MM-DD (ISO format) for API
 */
export const formatDateForAPI = (date: Date | string): string => {
    if (!date) return '';

    const d = typeof date === 'string' ? new Date(date) : date;
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
};

/**
 * Parse DD/MM/YYYY to Date object
 */
export const parseDateFromDisplay = (dateString: string): Date | null => {
    if (!dateString) return null;

    const parts = dateString.split('/');
    if (parts.length !== 3) return null;

    const day = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1; // Month is 0-indexed
    const year = parseInt(parts[2], 10);

    return new Date(year, month, day);
};

/**
 * Validate that delivery date is on or after dispatch date
 */
export const validateDeliveryDate = (dispatchDate: string, deliveryDate: string): string | null => {
    if (!dispatchDate || !deliveryDate) return null;

    const dispatch = new Date(dispatchDate);
    const delivery = new Date(deliveryDate);

    if (delivery < dispatch) {
        return 'Delivery date must be on or after dispatch date';
    }

    return null;
};

/**
 * Check if date gap is unusually long (> 3 days)
 */
export const checkDateGap = (dispatchDate: string, deliveryDate: string): string | null => {
    if (!dispatchDate || !deliveryDate) return null;

    const dispatch = new Date(dispatchDate);
    const delivery = new Date(deliveryDate);

    const daysDiff = Math.floor((delivery.getTime() - dispatch.getTime()) / (1000 * 60 * 60 * 24));

    if (daysDiff > 3) {
        return `Warning: Unusually long delivery time (${daysDiff} days)`;
    }

    return null;
};

/**
 * Get today's date in YYYY-MM-DD format
 */
export const getTodayISO = (): string => {
    return formatDateForAPI(new Date());
};

/**
 * Check if date is in the future
 */
export const isFutureDate = (dateString: string): boolean => {
    if (!dateString) return false;

    const date = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    return date > today;
};

/**
 * Get days until date
 */
export const getDaysUntil = (dateString: string): number => {
    if (!dateString) return 0;

    const date = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const daysDiff = Math.floor((date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

    return daysDiff;
};
