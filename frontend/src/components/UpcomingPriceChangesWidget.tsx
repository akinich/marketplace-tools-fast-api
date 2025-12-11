import { useState, useEffect } from 'react';
import {
    Card,
    CardContent,
    Typography,
    Box,
    CircularProgress,
    Alert,
    Chip,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { EventNote as EventIcon } from '@mui/icons-material';
import priceListAPI, { PriceList } from '../api/priceList';

/**
 * Dashboard Widget - Upcoming Price Changes
 * Shows price lists that are expiring soon or becoming active soon
 */
function UpcomingPriceChangesWidget() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [upcomingPriceLists, setUpcomingPriceLists] = useState<PriceList[]>([]);
    const [expiringPriceLists, setExpiringPriceLists] = useState<PriceList[]>([]);

    useEffect(() => {
        fetchUpcomingChanges();
    }, []);

    const fetchUpcomingChanges = async () => {
        setLoading(true);
        try {
            // Get upcoming and expiring price lists
            const response = await priceListAPI.list({ limit: 100 });
            const allLists = response.price_lists;

            const today = new Date();
            const thirtyDaysFromNow = new Date();
            thirtyDaysFromNow.setDate(today.getDate() + 30);

            // Filter upcoming (will become active within 30 days)
            const upcoming = allLists.filter((pl) => {
                const validFrom = new Date(pl.valid_from);
                return validFrom > today && validFrom <= thirtyDaysFromNow && pl.is_active;
            });

            // Filter expiring (will expire within 30 days)
            const expiring = allLists.filter((pl) => {
                if (!pl.valid_to) return false;
                const validTo = new Date(pl.valid_to);
                return validTo > today && validTo <= thirtyDaysFromNow && pl.is_active;
            });

            setUpcomingPriceLists(upcoming);
            setExpiringPriceLists(expiring);
        } catch (error) {
            console.error('Failed to fetch price changes:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleClick = (priceListId: number) => {
        navigate(`/outward/price-lists/${priceListId}`);
    };

    if (loading) {
        return (
            <Card>
                <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <EventIcon sx={{ mr: 1 }} />
                        <Typography variant="h6">Upcoming Price Changes</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                        <CircularProgress size={24} />
                    </Box>
                </CardContent>
            </Card>
        );
    }

    const totalChanges = upcomingPriceLists.length + expiringPriceLists.length;

    return (
        <Card>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <EventIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Upcoming Price Changes</Typography>
                </Box>

                {totalChanges === 0 ? (
                    <Alert severity="info">
                        No price changes scheduled in the next 30 days.
                    </Alert>
                ) : (
                    <Box>
                        {upcomingPriceLists.length > 0 && (
                            <Box sx={{ mb: 2 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                    🟡 Becoming Active Soon
                                </Typography>
                                {upcomingPriceLists.map((pl) => (
                                    <Box
                                        key={pl.id}
                                        onClick={() => handleClick(pl.id)}
                                        sx={{
                                            p: 1,
                                            mb: 1,
                                            border: '1px solid #e0e0e0',
                                            borderRadius: 1,
                                            cursor: 'pointer',
                                            '&:hover': { bgcolor: '#f5f5f5' },
                                        }}
                                    >
                                        <Typography variant="body2" fontWeight="bold">
                                            {pl.price_list_name}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            Active from: {new Date(pl.valid_from).toLocaleDateString()}
                                        </Typography>
                                    </Box>
                                ))}
                            </Box>
                        )}

                        {expiringPriceLists.length > 0 && (
                            <Box>
                                <Typography variant="subtitle2" gutterBottom>
                                    🔴 Expiring Soon
                                </Typography>
                                {expiringPriceLists.map((pl) => (
                                    <Box
                                        key={pl.id}
                                        onClick={() => handleClick(pl.id)}
                                        sx={{
                                            p: 1,
                                            mb: 1,
                                            border: '1px solid #e0e0e0',
                                            borderRadius: 1,
                                            cursor: 'pointer',
                                            '&:hover': { bgcolor: '#f5f5f5' },
                                        }}
                                    >
                                        <Typography variant="body2" fontWeight="bold">
                                            {pl.price_list_name}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            Expires: {pl.valid_to ? new Date(pl.valid_to).toLocaleDateString() : 'Never'}
                                        </Typography>
                                        <Chip
                                            label={`${pl.customers_count} customers`}
                                            size="small"
                                            sx={{ ml: 1 }}
                                        />
                                    </Box>
                                ))}
                            </Box>
                        )}
                    </Box>
                )}
            </CardContent>
        </Card>
    );
}

export default UpcomingPriceChangesWidget;
