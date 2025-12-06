/**
 * B2C Tickets Page
 * Filters tickets by category='b2c'
 * Reuses existing TicketsModule component with category filter
 */

import React from 'react';
import { Box, Typography } from '@mui/material';

export default function B2CTickets() {
    return (
        <Box>
            <Typography variant="h5" gutterBottom>
                B2C Tickets
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
                Customer issues for direct-to-home customers
            </Typography>
            {/* TODO: Implement B2C tickets list with category filter */}
            <Typography color="text.secondary">
                B2C tickets functionality coming soon. Use the existing tickets module at /tickets for now.
            </Typography>
        </Box>
    );
}
