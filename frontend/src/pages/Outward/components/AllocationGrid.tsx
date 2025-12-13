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
    Paper,
    Button
} from '@mui/material';
import {
    Warning as WarningIcon,
    Refresh as RefreshIcon,
    AutoFixHigh as AutoFillIcon,
    Fullscreen as FullscreenIcon,
    FullscreenExit as FullscreenExitIcon
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
    const [fullscreen, setFullscreen] = useState(false);

    const { items, customers, cells, totals } = sheetData;

    // Helper to get cell for item-customer combination
    const getCell = (itemId: number, customerId: string) => {
        return cells.find((c: any) => c.item_id === itemId && c.customer_id === customerId);
    };

    // Helper to check if customer has any modified cells
    const hasModifiedCells = (customerId: string) => {
        return cells.some((c: any) => c.customer_id === customerId && c.order_modified);
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
        <Box sx={{
            position: fullscreen ? 'fixed' : 'relative',
            top: fullscreen ? 0 : 'auto',
            left: fullscreen ? 0 : 'auto',
            right: fullscreen ? 0 : 'auto',
            bottom: fullscreen ? 0 : 'auto',
            zIndex: fullscreen ? 1300 : 'auto',
            bgcolor: fullscreen ? 'background.default' : 'transparent',
            p: fullscreen ? 3 : 0
        }}>
            {/* Toolbar */}
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Button
                    variant="contained"
                    startIcon={autoFilling ? <RefreshIcon /> : <AutoFillIcon />}
                    onClick={handleAutoFill}
                    disabled={autoFilling}
                >
                    {autoFilling ? 'Auto-filling...' : 'Auto-Fill SENT (FIFO)'}
                </Button>

                <Box sx={{ display: 'flex', gap: 1 }}>
                    <IconButton onClick={onRefresh} title="Refresh">
                        <RefreshIcon />
                    </IconButton>
                    <IconButton onClick={() => setFullscreen(!fullscreen)} title={fullscreen ? "Exit Fullscreen" : "Fullscreen"}>
                        {fullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
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
            <TableContainer
                component={Paper}
                sx={{
                    maxHeight: fullscreen ? 'calc(100vh - 200px)' : 600,
                    position: 'relative',
                    overflow: 'auto'
                }}
            >
                <Table stickyHeader size="small" sx={{ '& .MuiTableCell-root': { borderRight: '1px solid rgba(224, 224, 224, 1)' } }}>
                    <TableHead>
                        <TableRow>
                            {/* Sticky Left Columns */}
                            <TableCell
                                sx={{
                                    fontWeight: 'bold',
                                    position: 'sticky',
                                    left: 0,
                                    zIndex: 3,
                                    bgcolor: 'background.paper',
                                    borderRight: '2px solid #e0e0e0'
                                }}
                            >
                                #
                            </TableCell>
                            <TableCell
                                sx={{
                                    fontWeight: 'bold',
                                    position: 'sticky',
                                    left: 40,
                                    zIndex: 3,
                                    bgcolor: 'background.paper',
                                    borderRight: '2px solid #e0e0e0',
                                    minWidth: 150
                                }}
                            >
                                Item Name
                            </TableCell>

                            {/* Item Totals - Moved to left after Item Name */}
                            <TableCell
                                align="center"
                                sx={{
                                    fontWeight: 'bold',
                                    bgcolor: 'grey.100',
                                    position: 'sticky',
                                    left: 190,
                                    zIndex: 3,
                                    borderRight: '2px solid #e0e0e0',
                                    minWidth: 80
                                }}
                            >
                                ORDER Total
                            </TableCell>
                            <TableCell
                                align="center"
                                sx={{
                                    fontWeight: 'bold',
                                    bgcolor: 'grey.100',
                                    position: 'sticky',
                                    left: 270,
                                    zIndex: 3,
                                    borderRight: '2px solid #666',
                                    minWidth: 80
                                }}
                            >
                                SENT Total
                            </TableCell>

                            {/* Customer Columns */}
                            {customers.map((customer: any) => (
                                <TableCell
                                    key={customer.id}
                                    colSpan={2}
                                    align="center"
                                    sx={{
                                        fontWeight: 'bold',
                                        borderLeft: '1px solid #e0e0e0',
                                        bgcolor: hasModifiedCells(customer.id) ? '#fff3e0' : 'inherit'
                                    }}
                                >
                                    <Box>
                                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                                            {customer.name}
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
                                                SENT
                                            </Typography>
                                        </Box>
                                    </Box>
                                </TableCell>
                            ))}


                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {items.map((item: any, index: number) => {
                            const itemCells = cells.filter((c: any) => c.item_id === item.id);
                            const itemTotalOrder = itemCells.reduce((sum: number, c: any) => sum + (Number(c.order_quantity) || 0), 0);
                            const itemTotalSent = itemCells.reduce((sum: number, c: any) => sum + (Number(c.sent_quantity) || 0), 0);

                            return (
                                <TableRow key={item.id} hover>
                                    {/* Sticky Left Columns */}
                                    <TableCell
                                        sx={{
                                            position: 'sticky',
                                            left: 0,
                                            zIndex: 1,
                                            bgcolor: 'background.paper',
                                            borderRight: '2px solid #e0e0e0'
                                        }}
                                    >
                                        {index + 1}
                                    </TableCell>
                                    <TableCell
                                        sx={{
                                            position: 'sticky',
                                            left: 40,
                                            zIndex: 1,
                                            bgcolor: 'background.paper',
                                            borderRight: '2px solid #e0e0e0'
                                        }}
                                    >
                                        {item.name}
                                    </TableCell>

                                    {/* Item Totals - Moved to left after Item Name */}
                                    <TableCell
                                        align="center"
                                        sx={{
                                            fontWeight: 'bold',
                                            bgcolor: 'grey.100',
                                            position: 'sticky',
                                            left: 190,
                                            zIndex: 1,
                                            borderRight: '2px solid #e0e0e0'
                                        }}
                                    >
                                        {Number(itemTotalOrder).toFixed(1)}
                                    </TableCell>
                                    <TableCell
                                        align="center"
                                        sx={{
                                            fontWeight: 'bold',
                                            bgcolor: 'grey.100',
                                            position: 'sticky',
                                            left: 270,
                                            zIndex: 1,
                                            borderRight: '2px solid #666'
                                        }}
                                    >
                                        {Number(itemTotalSent).toFixed(1)}
                                    </TableCell>

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


                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
            </TableContainer>
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

    return (
        <TableCell
            align="center"
            sx={{
                bgcolor: isShortfall ? '#fff3e0' : isModified ? '#e3f2fd' : 'inherit',
                position: 'relative'
            }}
        >
            <TextField
                size="small"
                type="number"
                value={localValue}
                onChange={(e) => setLocalValue(e.target.value)}
                onFocus={() => setIsFocused(true)}
                onBlur={handleBlur}
                onKeyPress={handleKeyPress}
                disabled={isUpdating}
                error={!!error}
                InputProps={{
                    inputProps: {
                        min: 0,
                        step: 0.1,
                        style: { textAlign: 'center' }
                    }
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
