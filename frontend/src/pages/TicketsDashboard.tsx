/**
 * Tickets Dashboard
 * Shows aggregated stats for all three ticket types: Internal, B2B, B2C
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Container,
    Typography,
    Grid,
    Card,
    CardContent,
    CardActionArea,
    CircularProgress,
    Alert,
} from '@mui/material';
import {
    BugReport as InternalIcon,
    Business as B2BIcon,
    Home as B2CIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { dashboardAPI } from '../api';

interface CategoryStats {
    total: number;
    open: number;
    in_progress: number;
    resolved: number;
    closed: number;
}

interface DashboardStats {
    internal: CategoryStats;
    b2b: CategoryStats;
    b2c: CategoryStats;
}

export default function TicketsDashboard() {
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            const response = await fetch('/api/tickets/dashboard-stats', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            });
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error('Failed to fetch dashboard stats:', error);
            enqueueSnackbar('Failed to load dashboard stats', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (!stats) {
        return (
            <Alert severity="error">Failed to load dashboard statistics</Alert>
        );
    }

    const categories = [
        {
            key: 'internal',
            title: 'Internal Tickets',
            subtitle: 'ERP system issues and feature requests',
            icon: <InternalIcon sx={{ fontSize: 48 }} />,
            color: '#1976d2',
            route: '/tickets/internal',
            stats: stats.internal,
        },
        {
            key: 'b2b',
            title: 'B2B Tickets',
            subtitle: 'Customer issues for hotels and restaurants',
            icon: <B2BIcon sx={{ fontSize: 48 }} />,
            color: '#2e7d32',
            route: '/tickets/b2b',
            stats: stats.b2b,
        },
        {
            key: 'b2c',
            title: 'B2C Tickets',
            subtitle: 'Customer issues for direct-to-home customers',
            icon: <B2CIcon sx={{ fontSize: 48 }} />,
            color: '#ed6c02',
            route: '/tickets/b2c',
            stats: stats.b2c,
        },
    ];

    return (
        <Container maxWidth="xl">
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" gutterBottom>
                    Tickets Dashboard
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Overview of all ticket activity across Internal, B2B, and B2C categories
                </Typography>
            </Box>

            {categories.map((category) => (
                <Box key={category.key} sx={{ mb: 4 }}>
                    <Card
                        sx={{
                            mb: 2,
                            borderLeft: `4px solid ${category.color}`,
                        }}
                    >
                        <CardActionArea onClick={() => navigate(category.route)}>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                    <Box sx={{ color: category.color, mr: 2 }}>
                                        {category.icon}
                                    </Box>
                                    <Box>
                                        <Typography variant="h5" gutterBottom>
                                            {category.title}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {category.subtitle}
                                        </Typography>
                                    </Box>
                                </Box>

                                <Grid container spacing={2}>
                                    <Grid item xs={6} sm={2.4}>
                                        <Box sx={{ textAlign: 'center' }}>
                                            <Typography variant="h4" color="info.main">
                                                {category.stats.open}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                Open
                                            </Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={6} sm={2.4}>
                                        <Box sx={{ textAlign: 'center' }}>
                                            <Typography variant="h4" color="warning.main">
                                                {category.stats.in_progress}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                In Progress
                                            </Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={6} sm={2.4}>
                                        <Box sx={{ textAlign: 'center' }}>
                                            <Typography variant="h4" color="success.main">
                                                {category.stats.resolved}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                Resolved
                                            </Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={6} sm={2.4}>
                                        <Box sx={{ textAlign: 'center' }}>
                                            <Typography variant="h4" color="text.secondary">
                                                {category.stats.closed}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                Closed
                                            </Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={12} sm={2.4}>
                                        <Box sx={{ textAlign: 'center' }}>
                                            <Typography variant="h4">
                                                {category.stats.total}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                Total
                                            </Typography>
                                        </Box>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </CardActionArea>
                    </Card>
                </Box>
            ))}
        </Container>
    );
}
