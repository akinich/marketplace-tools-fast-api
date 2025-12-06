/**
 * ================================================================================
 * Wastage Chart Component
 * ================================================================================
 * Version: 1.0.0
 * Created: 2024-12-06
 *
 * Reusable chart component using Recharts for wastage analytics.
 * Supports bar, pie, and line charts with responsive design.
 * ================================================================================
 */


import { Box, Typography, Paper, useTheme, useMediaQuery } from '@mui/material';
import {
    BarChart,
    Bar,
    PieChart,
    Pie,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Cell,
} from 'recharts';

interface WastageChartProps {
    type: 'bar' | 'pie' | 'line';
    data: any[];
    title?: string;
    xKey?: string;
    yKey?: string;
    nameKey?: string;
    colors?: string[];
    height?: number;
}

const DEFAULT_COLORS = [
    '#8884d8',
    '#82ca9d',
    '#ffc658',
    '#ff7c7c',
    '#a4de6c',
    '#d0ed57',
    '#83a6ed',
    '#8dd1e1',
];

export default function WastageChart({
    type,
    data,
    title,
    xKey = 'name',
    yKey = 'value',
    nameKey = 'name',
    colors = DEFAULT_COLORS,
    height = 300,
}: WastageChartProps) {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

    if (!data || data.length === 0) {
        return (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                    No data available
                </Typography>
            </Paper>
        );
    }

    const renderChart = () => {
        switch (type) {
            case 'bar':
                return (
                    <ResponsiveContainer width="100%" height={height}>
                        <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis
                                dataKey={xKey}
                                angle={isMobile ? -45 : 0}
                                textAnchor={isMobile ? 'end' : 'middle'}
                                height={isMobile ? 80 : 30}
                            />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey={yKey} fill={colors[0]} />
                        </BarChart>
                    </ResponsiveContainer>
                );

            case 'pie':
                return (
                    <ResponsiveContainer width="100%" height={height}>
                        <PieChart>
                            <Pie
                                data={data}
                                dataKey={yKey}
                                nameKey={nameKey}
                                cx="50%"
                                cy="50%"
                                outerRadius={isMobile ? 60 : 80}
                                label={!isMobile}
                            >
                                {data.map((_entry, index) => (
                                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                                ))}
                            </Pie>
                            <Tooltip />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                );

            case 'line':
                return (
                    <ResponsiveContainer width="100%" height={height}>
                        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis
                                dataKey={xKey}
                                angle={isMobile ? -45 : 0}
                                textAnchor={isMobile ? 'end' : 'middle'}
                                height={isMobile ? 80 : 30}
                            />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey={yKey} stroke={colors[0]} strokeWidth={2} />
                        </LineChart>
                    </ResponsiveContainer>
                );

            default:
                return null;
        }
    };

    return (
        <Paper sx={{ p: 2 }}>
            {title && (
                <Typography variant="h6" gutterBottom>
                    {title}
                </Typography>
            )}
            <Box sx={{ width: '100%', height }}>
                {renderChart()}
            </Box>
        </Paper>
    );
}
