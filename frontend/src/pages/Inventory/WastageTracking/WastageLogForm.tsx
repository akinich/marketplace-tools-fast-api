/**
 * ================================================================================
 * Wastage Log Form Page
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Standalone page for logging wastage events.
 * ================================================================================
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Paper, Button } from '@mui/material';
import { ArrowBack as BackIcon } from '@mui/icons-material';
import WastageLogModal from './components/WastageLogModal';

export default function WastageLogForm() {
    const navigate = useNavigate();
    const [modalOpen] = useState(true);

    const handleSuccess = () => {
        navigate('/inventory/wastage-tracking');
    };

    const handleClose = () => {
        navigate('/inventory/wastage-tracking');
    };

    return (
        <Box>
            <Button
                startIcon={<BackIcon />}
                onClick={() => navigate('/inventory/wastage-tracking')}
                sx={{ mb: 2 }}
            >
                Back to Dashboard
            </Button>

            <Paper sx={{ p: 3 }}>
                <Typography variant="h5" gutterBottom>
                    Log Wastage Event
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                    Record wastage with photos and details for tracking and analytics.
                </Typography>
            </Paper>

            <WastageLogModal
                open={modalOpen}
                onClose={handleClose}
                onSuccess={handleSuccess}
            />
        </Box>
    );
}
