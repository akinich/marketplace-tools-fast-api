import { useState } from 'react';
import { allocationApi } from '../../../api';

interface UseOptimisticCellProps {
    cellId: number;
    initialValue: number | string;
    version: number;
    field: 'order' | 'sent';
    onSuccess?: () => void;
}

export function useOptimisticCell({
    cellId,
    initialValue,
    version,
    field,
    onSuccess
}: UseOptimisticCellProps) {
    const [value, setValue] = useState(initialValue);
    const [currentVersion, setCurrentVersion] = useState(version);
    const [isUpdating, setIsUpdating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const updateValue = async (newValue: number) => {
        // 1. Optimistic update (immediate UI change)
        const oldValue = value;
        const oldVersion = currentVersion;
        setValue(newValue);
        setError(null);

        // 2. Send to backend
        setIsUpdating(true);
        try {
            const updateData = field === 'order'
                ? { order_quantity: newValue, version: currentVersion }
                : { sent_quantity: newValue, version: currentVersion };

            const result = await allocationApi.updateCell(cellId, updateData);

            // 3. Confirm update with new version
            setCurrentVersion(result.cell.version);
            setValue(field === 'order' ? result.cell.order_quantity : result.cell.sent_quantity);

            if (onSuccess) {
                onSuccess();
            }
        } catch (err: any) {
            // 4. Handle errors
            if (err.response?.status === 409) {
                // Version conflict - reload required
                setError('Cell updated by another user');
                // Revert to old value temporarily
                setValue(oldValue);
                setCurrentVersion(oldVersion);

                // Trigger refresh to get latest data
                if (onSuccess) {
                    setTimeout(onSuccess, 500);
                }
            } else {
                // Other errors - revert
                setValue(oldValue);
                setError(err.response?.data?.detail || 'Update failed');
            }
        } finally {
            setIsUpdating(false);
        }
    };

    return {
        value,
        updateValue,
        isUpdating,
        error,
        version: currentVersion
    };
}
