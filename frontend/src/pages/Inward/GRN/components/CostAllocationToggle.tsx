/**
 * ================================================================================
 * Cost Allocation Toggle Component (GRN Version)
 * ================================================================================
 */

import React from 'react';
import {
    Box,
    ToggleButton,
    ToggleButtonGroup,
    Tooltip,
    Typography,
} from '@mui/material';
import {
    Store as FarmIcon,
    Business as UsIcon,
} from '@mui/icons-material';

interface CostAllocationToggleProps {
    value: 'farm' | 'us' | undefined | string;
    onChange: (value: 'farm' | 'us') => void;
    disabled?: boolean;
    label?: string;
}

export default function CostAllocationToggle({
    value,
    onChange,
    disabled = false,
    label = "Cost Allocation *"
}: CostAllocationToggleProps) {
    const handleChange = (_event: React.MouseEvent<HTMLElement>, newValue: 'farm' | 'us' | null) => {
        if (newValue !== null) {
            onChange(newValue);
        }
    };

    const farmTooltip = (
        <Box>
            <Typography variant="body2" fontWeight="bold">Farm Responsibility</Typography>
            <Typography variant="caption">
                Cost deducted from farm invoice. Use for:
            </Typography>
            <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                <li><Typography variant="caption">Transport damage</Typography></li>
                <li><Typography variant="caption">Quality below spec</Typography></li>
                <li><Typography variant="caption">Wrong variety</Typography></li>
            </ul>
        </Box>
    );

    const usTooltip = (
        <Box>
            <Typography variant="body2" fontWeight="bold">Our Responsibility</Typography>
            <Typography variant="caption">
                Cost absorbed by us. Use for:
            </Typography>
            <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                <li><Typography variant="caption">QC wastage (our standards)</Typography></li>
                <li><Typography variant="caption">Packing overfill</Typography></li>
                <li><Typography variant="caption">Cold storage damage</Typography></li>
                <li><Typography variant="caption">Customer claims</Typography></li>
            </ul>
        </Box>
    );

    return (
        <Box>
            <Typography variant="subtitle2" gutterBottom>
                {label}
            </Typography>
            <ToggleButtonGroup
                value={value}
                exclusive
                onChange={handleChange}
                disabled={disabled}
                fullWidth
                sx={{ mb: 1 }}
                size="small"
            >
                <Tooltip title={farmTooltip} arrow>
                    <ToggleButton
                        value="farm"
                        sx={{
                            '&.Mui-selected': {
                                backgroundColor: 'error.main',
                                color: 'white',
                                '&:hover': {
                                    backgroundColor: 'error.dark',
                                },
                            },
                        }}
                    >
                        <FarmIcon sx={{ mr: 1, fontSize: 18 }} />
                        Farm
                    </ToggleButton>
                </Tooltip>
                <Tooltip title={usTooltip} arrow>
                    <ToggleButton
                        value="us"
                        sx={{
                            '&.Mui-selected': {
                                backgroundColor: 'primary.main',
                                color: 'white',
                                '&:hover': {
                                    backgroundColor: 'primary.dark',
                                },
                            },
                        }}
                    >
                        <UsIcon sx={{ mr: 1, fontSize: 18 }} />
                        Us
                    </ToggleButton>
                </Tooltip>
            </ToggleButtonGroup>
            {value && (
                <Typography variant="caption" color="text.secondary">
                    {value === 'farm'
                        ? '🔴 Cost will be deducted from farm invoice'
                        : '🔵 Cost will be absorbed in our operations'}
                </Typography>
            )}
        </Box>
    );
}
