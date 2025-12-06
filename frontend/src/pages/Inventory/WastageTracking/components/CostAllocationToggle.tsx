/**
 * ================================================================================
 * Cost Allocation Toggle Component
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Toggle switch for Farm/Us cost allocation with visual distinction and tooltips.
 * Auto-defaults based on wastage stage.
 * ================================================================================
 */

import { useEffect } from 'react';
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
import { CostAllocation, WastageStage } from '../../../../api/wastageTracking';

interface CostAllocationToggleProps {
    value: CostAllocation | string;
    onChange: (value: CostAllocation) => void;
    defaultStage?: WastageStage | string;
    disabled?: boolean;
}

export default function CostAllocationToggle({
    value,
    onChange,
    defaultStage,
    disabled = false,
}: CostAllocationToggleProps) {
    const handleChange = (_event: React.MouseEvent<HTMLElement>, newValue: CostAllocation | null) => {
        if (newValue !== null) {
            onChange(newValue);
        }
    };

    // Auto-default based on stage
    useEffect(() => {
        if (defaultStage && !value) {
            // Default to Farm for receiving stage, Us for all others
            const defaultValue = defaultStage === WastageStage.RECEIVING
                ? CostAllocation.FARM
                : CostAllocation.US;
            onChange(defaultValue);
        }
    }, [defaultStage, value, onChange]);

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
                Cost Allocation *
            </Typography>
            <ToggleButtonGroup
                value={value}
                exclusive
                onChange={handleChange}
                disabled={disabled}
                fullWidth
                sx={{ mb: 1 }}
            >
                <Tooltip title={farmTooltip} arrow>
                    <ToggleButton
                        value={CostAllocation.FARM}
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
                        <FarmIcon sx={{ mr: 1 }} />
                        Farm
                    </ToggleButton>
                </Tooltip>
                <Tooltip title={usTooltip} arrow>
                    <ToggleButton
                        value={CostAllocation.US}
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
                        <UsIcon sx={{ mr: 1 }} />
                        Us
                    </ToggleButton>
                </Tooltip>
            </ToggleButtonGroup>
            <Typography variant="caption" color="text.secondary">
                {value === CostAllocation.FARM
                    ? '🔴 Cost will be deducted from farm invoice'
                    : '🔵 Cost will be absorbed in our operations'}
            </Typography>
        </Box>
    );
}
