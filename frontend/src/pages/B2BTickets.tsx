/**
 * B2B Tickets Page
 * Filters tickets by category='b2b'
 * Reuses existing TicketsModule component with category filter
 */

import React from 'react';
import { Box, Typography } from '@mui/material';

export default function B2BTickets() {
    return (
        <Box>
            <Typography variant="h5" gutterBottom>
                B2B Tickets
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
                Customer issues for hotels and restaurants
            </Typography>
            {/* TODO: Implement B2B tickets list with category filter */}
            <Typography color="text.secondary">
                B2B tickets functionality coming soon. Use the existing tickets module at /tickets for now.
            </Typography>
        </Box>
    );
}
