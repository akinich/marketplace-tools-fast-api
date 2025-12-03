import React from 'react';
import { Box, Typography, Alert } from '@mui/material';

function WooCustomerMaster() {
    console.log('🧪 WooCustomerMaster TEST component loaded');

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h3" gutterBottom>
                🧪 WooCommerce Customer Master - TEST
            </Typography>
            <Alert severity="success" sx={{ mt: 2 }}>
                ✅ Component is rendering! This is a simplified test version.
            </Alert>
            <Typography sx={{ mt: 2 }}>
                If you see this message, the component file is being loaded correctly.
                The issue is likely with the API calls or data fetching.
            </Typography>
        </Box>
    );
}

export default WooCustomerMaster;
