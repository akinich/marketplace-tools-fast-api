import React, { useState } from 'react';
import {
    Box,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TextField,
    Typography,
    Chip,
    IconButton,
    Tooltip,
    Paper,
    Button
} from '@mui/material';
import {
    Warning as WarningIcon,
    Refresh as RefreshIcon,
    AutoFixHigh as AutoFillIcon
} from '@mui/icons-material';
import { useOptimisticCell } from '../hooks/useOptimisticCell';
import { allocationApi } from '../../../api';
import { toast } from 'react-toastify';

interface AllocationGridProps {
    sheetData: any;
    onRefresh: () => void;
}

export default function AllocationGrid({ sheetData, onRefresh }: AllocationGridProps) {
    const [autoFilling, setAutoFilling] = useState(false);

    const { items, customers, cells, totals } = sheetData;

    // Helper to get cell for item-customer combination
    const getCell = (itemId: number, customerId: string) => {
        return cells.find((c: any) => c.item_id === itemId && c.customer_id === customerId);
    };

    // Helper to check if customer has any modified cells
    const hasModifiedCells = (customerId: string) => {
        return cells.some((c: any) => c.customer_id === customerId && c.order_modified);
    };

    // Helper to check if any cell for item has shortfall
    const hasShortfall = (itemId: number) => {
        return cells.some((c: any) => c.item_id === itemId && c.has_shortfall);
    };

    const handleAutoFill = async () => {
        setAutoFilling(true);
        try {
            await allocationApi.autoFillSheet(sheetData.sheet_id);
            toast.success('Auto-filled SENT quantities using FIFO');
            onRefresh();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to auto-fill');
        } finally {
            setAutoFilling(false);
        }
    };

    return (
        <Box>
            {/* Action Bar */}
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6">
                    Allocation Matrix
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                        variant="outlined"
                        startIcon={<AutoFillIcon />}
                        onClick={handleAutoFill}
                        disabled={autoFilling}
                    >
                        {autoFilling ? 'Auto-Filling...' : 'Auto-Fill SENT'}
                    </Button>
                    <IconButton onClick={onRefresh} title="Refresh">
                        <RefreshIcon />
                    </IconButton>
                </Box>
            </Box>

            {/* Totals Summary */}
            <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
                <Chip label={`Total Ordered: ${totals.total_order} kg`} color="primary" variant="outlined" />
                <Chip label={`Total Sent: ${totals.total_sent} kg`} color="success" variant="outlined" />
                {totals.shortfall > 0 && (
                    <Chip
                        label={`Shortfall: ${totals.shortfall} kg`}
                        color="warning"
                        icon={<WarningIcon />}
                    />
                )}
            </Box>

            {/* Grid */}
            <TableContainer component={Paper} sx={{ maxHeight: 'calc(100vh - 400px)', overflow: 'auto' }}>
                <Table stickyHeader size="small">
                    <TableHead>
                        <TableRow>
                            {/* Item Info Columns */}
                            <TableCell sx={{ fontWeight: 'bold', minWidth: 50 }}>NO</TableCell>
                            <TableCell sx={{ fontWeight: 'bold', minWidth: 80 }}>TYPE</TableCell>
                            <TableCell sx={{ fontWeight: 'bold', minWidth: 150 }}>VARIETY</TableCell>
                            <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>SUB VARIETY</TableCell>

                            {/* Customer Columns */}
                            {customers.map((customer: any) => (
                                <TableCell
                                    key={customer.id}
                                    align="center"
                                    sx={{ minWidth: 180, bgcolor: 'grey.50' }}
                                    colSpan={2}
                                >
                                    <Box>
                                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                                            {customer.name}
                                            {hasModifiedCells(customer.id) && (
                                                <span style={{ color: '#ff9800' }}>*</span>
                                            )}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            {customer.so_number}
                                        </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', mt: 0.5 }}>
                                        <Box sx={{ flex: 1, borderRight: '1px solid #e0e0e0', pr: 0.5 }}>
                                            <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                                                ORDER
                                            </Typography>
                                        </Box>
                                        <Box sx={{ flex: 1, pl: 0.5 }}>
                                            <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                                                SENT {hasShortfall(customer.id) && <WarningIcon sx={{ fontSize: 12, color: 'warning.main' }} />}
                                            </Typography>
                                        </Box>
                                    </Box>
                                </TableCell>
                            ))}

                            {/* Totals Column */}
                            <TableCell align="center" sx={{ fontWeight: 'bold', minWidth: 120 }} colSpan={2}>
                                TOTAL
                                <Box sx={{ display: 'flex', mt: 0.5 }}>
                                    <Box sx={{ flex: 1 }}>
                                        <Typography variant="caption">ORDER</Typography>
                                    </Box>
                                    <Box sx={{ flex: 1 }}>
                                        <Typography variant="caption">SENT</Typography>
                                    </Box>
                                </Box>
                            </TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {items.map((item: any, index: number) => {
                            const itemCells = cells.filter((c: any) => c.item_id === item.id);
                            const itemTotalOrder = itemCells.reduce((sum: number, c: any) => sum + (Number(c.order_quantity) || 0), 0);
                            const itemTotalSent = itemCells.reduce((sum: number, c: any) => sum + (Number(c.sent_quantity) || 0), 0);

                            return (
                                <TableRow key={item.id} hover>
                                    {/* Item Info */}
                                    <TableCell>{index + 1}</TableCell>
                                    <TableCell>{item.type || '-'}</TableCell>
                                    <TableCell>{item.name}</TableCell>
                                    <TableCell>{item.sub_variety || item.variety || '-'}</TableCell>

                                    {/* Customer Cells */}
                                    {customers.map((customer: any) => {
                                        const cell = getCell(item.id, customer.id);

                                        if (!cell) {
                                            return (
                                                <React.Fragment key={customer.id}>
                                                    <TableCell align="center">-</TableCell>
                                                    <TableCell align="center">-</TableCell>
                                                </React.Fragment>
                                            );
                                        }

                                        return (
                                            <React.Fragment key={customer.id}>
                                                <EditableCell
                                                    cell={cell}
                                                    field="order"
                                                    onRefresh={onRefresh}
                                                />
                                                <EditableCell
                                                    cell={cell}
                                                    field="sent"
                                                    onRefresh={onRefresh}
                                                />
                                            </React.Fragment>
                                        );
                                    })}

                                    {/* Item Totals */}
                                    <TableCell align="center" sx={{ fontWeight: 'bold', bgcolor: 'grey.100' }}>
                                        {Number(itemTotalOrder).toFixed(1)}
                                    </TableCell>
                                    <TableCell align="center" sx={{ fontWeight: 'bold', bgcolor: 'grey.100' }}>
                                        {Number(itemTotalSent).toFixed(1)}
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Legend */}
            <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Box sx={{ width: 16, height: 16, bgcolor: '#FFF59D', border: '1px solid #ccc' }} />
                    <Typography variant="caption">Shortfall (SENT \u003c ORDER)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Box sx={{ width: 16, height: 16, bgcolor: '#FFE0B2', border: '1px solid #ccc' }} />
                    <Typography variant="caption">ORDER Modified</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Typography variant="caption">*</Typography>
                    <Typography variant="caption">= Customer has modifications</Typography>
                </Box>
            </Box>
        </Box>
    );
}

// Editable Cell Component with Optimistic Updates
interface EditableCellProps {
    cell: any;
    field: 'order' | 'sent';
    onRefresh: () => void;
}

function EditableCell({ cell, field, onRefresh }: EditableCellProps) {
    const { value, updateValue, isUpdating, error } = useOptimisticCell({
        cellId: cell.id,
        initialValue: field === 'order' ? cell.order_quantity : (cell.sent_quantity || ''),
        version: cell.version,
        field: field,
        onSuccess: onRefresh
    });

    const [localValue, setLocalValue] = useState(String(value));
    const [isFocused, setIsFocused] = useState(false);

    const isShortfall = field === 'sent' && cell.has_shortfall;
    const isModified = field === 'order' && cell.order_modified;

    const handleBlur = () => {
        setIsFocused(false);
        if (localValue !== value && localValue !== '') {
            updateValue(parseFloat(localValue) || 0);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            (e.target as HTMLInputElement).blur();
        }
    };

    React.useEffect(() => {
        setLocalValue(String(value));
    }, [value]);

    const bgColor = isShortfall
        ? '#FFF59D'  // Yellow for shortfall
        : isModified
            ? '#FFE0B2'  // Orange for modified
            : 'transparent';

    return (
        <TableCell
            align="center"
            sx={{
                bgcolor: bgColor,
                p: 0.5,
                position: 'relative'
            }}
        >
            {error && (
                <Tooltip title={error}>
                    <WarningIcon
                        sx={{
                            position: 'absolute',
                            top: 2,
                            right: 2,
                            fontSize: 12,
                            color: 'error.main'
                        }}
                    />
                </Tooltip>
            )}
            <TextField
                value={isFocused ? localValue : (value || '')}
                onChange={(e) => setLocalValue(e.target.value)}
                onFocus={() => setIsFocused(true)}
                onBlur={handleBlur}
                onKeyPress={handleKeyPress}
                disabled={isUpdating}
                size="small"
                type="number"
                inputProps={{
                    step: 0.1,
                    min: 0,
                    style: { textAlign: 'center', padding: '4px' }
                }}
                sx={{
                    width: '80px',
                    '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                            border: isFocused ? '1px solid #1976d2' : '1px solid transparent',
                        },
                        '&:hover fieldset': {
                            border: '1px solid #999',
                        },
                    },
                    '& input': {
                        fontSize: '0.875rem',
                    }
                }}
            />
        </TableCell>
    );
}
