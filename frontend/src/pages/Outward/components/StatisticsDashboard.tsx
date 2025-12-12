import { useState, useEffect } from 'react';
import {
    Box,
    Grid,
    Card,
    CardContent,
    Typography,
    CircularProgress,
    Alert,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Chip
} from '@mui/material';
import {
    TrendingUp,
    TrendingDown,
    CheckCircle,
    Warning
} from '@mui/icons-material';
import { allocationApi } from '../../../api';

interface StatisticsDashboardProps {
    sheetId: number;
}

export default function StatisticsDashboard({ sheetId }: StatisticsDashboardProps) {
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadStatistics();
    }, [sheetId]);

    const loadStatistics = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await allocationApi.getStatistics(sheetId);
            setStats(data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load statistics');
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

    if (error) {
        return <Alert severity="error">{error}</Alert>;
    }

    if (!stats) {
        return null;
    }

    const { summary, by_item, by_customer, shortfalls } = stats;

    return (
        <Box>
            {/* Summary Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <Box>
                                    <Typography color="text.secondary" variant="caption">
                                        Total Ordered
                                    </Typography>
                                    <Typography variant="h4">
                                        {summary.total_ordered.toFixed(1)}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        kg
                                    </Typography>
                                </Box>
                                <TrendingUp sx={{ fontSize: 40, color: 'primary.main', opacity: 0.3 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <Box>
                                    <Typography color="text.secondary" variant="caption">
                                        Total Sent
                                    </Typography>
                                    <Typography variant="h4" color="success.main">
                                        {summary.total_sent.toFixed(1)}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        kg
                                    </Typography>
                                </Box>
                                <CheckCircle sx={{ fontSize: 40, color: 'success.main', opacity: 0.3 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <Box>
                                    <Typography color="text.secondary" variant="caption">
                                        Shortfall
                                    </Typography>
                                    <Typography variant="h4" color={summary.total_shortfall > 0 ? 'warning.main' : 'success.main'}>
                                        {summary.total_shortfall.toFixed(1)}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        kg
                                    </Typography>
                                </Box>
                                {summary.total_shortfall > 0 ? (
                                    <Warning sx={{ fontSize: 40, color: 'warning.main', opacity: 0.3 }} />
                                ) : (
                                    <CheckCircle sx={{ fontSize: 40, color: 'success.main', opacity: 0.3 }} />
                                )}
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <Box>
                                    <Typography color="text.secondary" variant="caption">
                                        Fulfillment Rate
                                    </Typography>
                                    <Typography variant="h4" color={summary.fulfillment_rate >= 95 ? 'success.main' : 'warning.main'}>
                                        {summary.fulfillment_rate.toFixed(1)}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        %
                                    </Typography>
                                </Box>
                                {summary.fulfillment_rate >= 95 ? (
                                    <TrendingUp sx={{ fontSize: 40, color: 'success.main', opacity: 0.3 }} />
                                ) : (
                                    <TrendingDown sx={{ fontSize: 40, color: 'warning.main', opacity: 0.3 }} />
                                )}
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Shortfalls Table (if any) */}
            {shortfalls && shortfalls.length > 0 && (
                <Box sx={{ mb: 4 }}>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                        <Warning sx={{ verticalAlign: 'middle', mr: 1, color: 'warning.main' }} />
                        Shortfalls
                    </Typography>
                    <TableContainer component={Paper}>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell sx={{ fontWeight: 'bold' }}>Item</TableCell>
                                    <TableCell sx={{ fontWeight: 'bold' }}>Customer</TableCell>
                                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>Ordered</TableCell>
                                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>Sent</TableCell>
                                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>Shortage</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {shortfalls.map((sf: any, index: number) => (
                                    <TableRow key={index} hover>
                                        <TableCell>{sf.item_name}</TableCell>
                                        <TableCell>{sf.customer_name}</TableCell>
                                        <TableCell align="right">{sf.ordered.toFixed(1)} kg</TableCell>
                                        <TableCell align="right">{sf.sent.toFixed(1)} kg</TableCell>
                                        <TableCell align="right">
                                            <Chip
                                                label={`${sf.shortage.toFixed(1)} kg`}
                                                color="warning"
                                                size="small"
                                            />
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </Box>
            )}

            {/* By Item Breakdown */}
            <Box sx={{ mb: 4 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>
                    By Item
                </Typography>
                <TableContainer component={Paper}>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell sx={{ fontWeight: 'bold' }}>Item</TableCell>
                                <TableCell align="right" sx={{ fontWeight: 'bold' }}>Total Ordered</TableCell>
                                <TableCell align="right" sx={{ fontWeight: 'bold' }}>Total Sent</TableCell>
                                <TableCell align="right" sx={{ fontWeight: 'bold' }}>Shortfall</TableCell>
                                <TableCell align="center" sx={{ fontWeight: 'bold' }}>Customers Affected</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {by_item.map((item: any) => (
                                <TableRow key={item.item_id} hover>
                                    <TableCell>{item.item_name}</TableCell>
                                    <TableCell align="right">{item.total_ordered.toFixed(1)} kg</TableCell>
                                    <TableCell align="right">{item.total_sent.toFixed(1)} kg</TableCell>
                                    <TableCell align="right">
                                        {item.shortfall > 0 ? (
                                            <Chip
                                                label={`${item.shortfall.toFixed(1)} kg`}
                                                color="warning"
                                                size="small"
                                            />
                                        ) : (
                                            <span style={{ color: '#4caf50' }}>-</span>
                                        )}
                                    </TableCell>
                                    <TableCell align="center">{item.customers_affected}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Box>

            {/* By Customer Breakdown */}
            <Box>
                <Typography variant="h6" sx={{ mb: 2 }}>
                    By Customer
                </Typography>
                <TableContainer component={Paper}>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell sx={{ fontWeight: 'bold' }}>Customer</TableCell>
                                <TableCell align="right" sx={{ fontWeight: 'bold' }}>Total Ordered</TableCell>
                                <TableCell align="right" sx={{ fontWeight: 'bold' }}>Total Sent</TableCell>
                                <TableCell align="center" sx={{ fontWeight: 'bold' }}>Fulfillment Rate</TableCell>
                                <TableCell align="center" sx={{ fontWeight: 'bold' }}>Invoice Status</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {by_customer.map((customer: any) => (
                                <TableRow key={customer.customer_id} hover>
                                    <TableCell>{customer.customer_name}</TableCell>
                                    <TableCell align="right">{customer.total_ordered.toFixed(1)} kg</TableCell>
                                    <TableCell align="right">{customer.total_sent.toFixed(1)} kg</TableCell>
                                    <TableCell align="center">
                                        <Chip
                                            label={`${customer.fulfillment_rate.toFixed(1)}%`}
                                            color={customer.fulfillment_rate >= 95 ? 'success' : 'warning'}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell align="center">
                                        <Chip
                                            label={customer.invoice_status}
                                            color={
                                                customer.invoice_status === 'invoiced' ? 'success' :
                                                    customer.invoice_status === 'ready' ? 'primary' :
                                                        'default'
                                            }
                                            size="small"
                                        />
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Box>
        </Box>
    );
}
