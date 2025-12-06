/**
 * Coming Soon Page Component
 * Version: 1.0.0
 * Created: 2025-12-07
 *
 * Description:
 *   Reusable "Coming Soon" page for modules under development
 *   Displays module name, description, and estimated timeline
 */

import React from 'react';
import { Box, Container, Typography, Paper, Chip } from '@mui/material';
import { Construction as ConstructionIcon } from '@mui/icons-material';

export default function ComingSoon({
    moduleName = "Module",
    description = "This module is currently under development.",
    estimatedPhase = "Coming Soon",
    priority = "MEDIUM"
}) {
    const getPriorityColor = (priority) => {
        switch (priority.toUpperCase()) {
            case 'CRITICAL':
                return 'error';
            case 'HIGH':
                return 'warning';
            case 'MEDIUM':
                return 'info';
            case 'LOW':
                return 'default';
            default:
                return 'default';
        }
    };

    return (
        <Container maxWidth="md">
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '60vh',
                    textAlign: 'center',
                }}
            >
                <Paper
                    elevation={3}
                    sx={{
                        p: 6,
                        borderRadius: 2,
                        backgroundColor: 'background.paper',
                        width: '100%',
                    }}
                >
                    <ConstructionIcon
                        sx={{
                            fontSize: 100,
                            color: 'warning.main',
                            mb: 3,
                        }}
                    />

                    <Typography variant="h3" gutterBottom fontWeight="bold">
                        {moduleName}
                    </Typography>

                    <Chip
                        label={`Priority: ${priority}`}
                        color={getPriorityColor(priority)}
                        sx={{ mb: 3 }}
                    />

                    <Typography variant="h6" color="text.secondary" paragraph>
                        {description}
                    </Typography>

                    <Box sx={{ mt: 4 }}>
                        <Typography variant="body1" color="text.secondary">
                            <strong>Estimated Timeline:</strong> {estimatedPhase}
                        </Typography>
                    </Box>

                    <Box
                        sx={{
                            mt: 4,
                            p: 2,
                            backgroundColor: 'info.lighter',
                            borderRadius: 1,
                            border: '1px solid',
                            borderColor: 'info.light',
                        }}
                    >
                        <Typography variant="body2" color="text.secondary">
                            This module is part of our development roadmap and will be available soon.
                            Thank you for your patience!
                        </Typography>
                    </Box>
                </Paper>
            </Box>
        </Container>
    );
}
