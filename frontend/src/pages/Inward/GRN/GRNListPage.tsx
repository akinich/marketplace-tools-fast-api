import React, { useState, useEffect } from 'react';
import {
    Box, Button, Card, Chip, TextField, Select, MenuItem, Typography
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useNavigate } from 'react-router-dom';
import { grnAPI, GRNResponse, GRNListParams } from '../../../api/grn';

const GRNListPage: React.FC = () => {
    const navigate = useNavigate();
    const [grns, setGRNs] = useState<GRNResponse[]>([]);
    const [loading, setLoading] = useState(false);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(0);
    const [pageSize, setPageSize] = useState(20);

    const loadGRNs = async () => {
        setLoading(true);
        try {
            const params: GRNListParams = {
                page: page + 1, // API is likely 1-indexed
                limit: pageSize,
            };
            const response = await grnAPI.list(params);
            setGRNs(response.data.grns);
            setTotal(response.data.total);
        } catch (error) {
            console.error('Failed to load GRNs:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadGRNs();
    }, [page, pageSize]);

    const getStatusColor = (status: string) => {
        const colors: { [key: string]: 'warning' | 'success' | 'default' | 'primary' | 'secondary' | 'error' | 'info' } = {
            draft: 'warning',
            completed: 'success',
            locked: 'default' // 'default' might not be valid for Chip color prop in latest MUI, usually 'default' works or need specific
        };
        return colors[status] || 'default';
    };

    const columns: GridColDef[] = [
        { field: 'grn_number', headerName: 'GRN #', width: 150 },
        { field: 'po_number', headerName: 'PO #', width: 150 },
        { field: 'batch_number', headerName: 'Batch #', width: 150 },
        { field: 'vendor_name', headerName: 'Vendor', width: 200 },
        { field: 'receiving_date', headerName: 'Receiving Date', width: 130 },
        {
            field: 'status',
            headerName: 'Status',
            width: 120,
            renderCell: (params) => (
                <Chip
                    label={params.value ? params.value.toUpperCase() : ''}
                    color={getStatusColor(params.value)}
                    size="small"
                />
            )
        },
        {
            field: 'actions',
            headerName: 'Actions',
            width: 300,
            renderCell: (params) => (
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                        size="small"
                        variant="outlined"
                        onClick={() => navigate(`/inward/grn/${params.row.id}`)}
                    >
                        View
                    </Button>
                    {params.row.status === 'draft' && (
                        <>
                            <Button
                                size="small"
                                variant="contained"
                                onClick={() => navigate(`/inward/grn/${params.row.id}/edit`)}
                            >
                                Enter Data
                            </Button>
                            <Button
                                size="small"
                                variant="text"
                                onClick={() => handlePrintBlank(params.row.id)}
                            >
                                Print Blank
                            </Button>
                        </>
                    )}
                </Box>
            )
        }
    ];

    const handlePrintBlank = async (grnId: number) => {
        try {
            const response = await grnAPI.generateBlankPDF(grnId);
            // Ensure response.data is Blob, axios might need responseType: 'blob' in call (it is there in api/grn.ts)
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            window.open(url);
        } catch (error) {
            console.error('Failed to generate PDF:', error);
            alert('Failed to generate PDF');
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" sx={{ mb: 3 }}>
                Goods Receipt Notes (GRN)
            </Typography>

            {/* Filters can be added here */}
            <Card sx={{ p: 2, mb: 3 }}>
                {/* Placeholder for filter controls */}
                <Typography variant="body2" color="textSecondary">Filter functionality to be implemented.</Typography>
            </Card>

            {/* DataGrid */}
            <Card>
                <div style={{ height: 600, width: '100%' }}>
                    <DataGrid
                        rows={grns}
                        columns={columns}
                        loading={loading}
                        rowCount={total}
                        paginationMode="server"
                        paginationModel={{ page, pageSize }}
                        onPaginationModelChange={(model) => {
                            setPage(model.page);
                            setPageSize(model.pageSize);
                        }}
                        pageSizeOptions={[20, 50, 100]}
                    />
                </div>
            </Card>
        </Box>
    );
};

export default GRNListPage;
