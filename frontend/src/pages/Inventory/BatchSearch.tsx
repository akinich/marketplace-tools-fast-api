/**
 * Batch Search Component
 * Version: 1.0.0
 * Created: 2024-12-04
 *
 * Description:
 *   Reusable search and filter component for batch tracking
 *   - Batch number search
 *   - Status filter
 *   - Date range filter
 *   - Repacked batch filter
 */

import React, { useState } from 'react';
import {
    Box,
    Paper,
    TextField,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    FormControlLabel,
    Checkbox,
    Grid,
} from '@mui/material';
import {
    Search as SearchIcon,
    Clear as ClearIcon,
} from '@mui/icons-material';
import { BatchStatus, SearchBatchesRequest } from '../../api/batchTracking';

interface BatchSearchProps {
    onSearch: (filters: SearchBatchesRequest) => void;
    loading?: boolean;
}

export default function BatchSearch({ onSearch, loading = false }: BatchSearchProps) {
    const [batchNumber, setBatchNumber] = useState('');
    const [status, setStatus] = useState<string>('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [isRepacked, setIsRepacked] = useState(false);

    const handleSearch = () => {
        const filters: SearchBatchesRequest = {};

        if (batchNumber) filters.batch_number = batchNumber;
        if (status) filters.status = status as BatchStatus;
        if (dateFrom) filters.date_from = dateFrom;
        if (dateTo) filters.date_to = dateTo;
        if (isRepacked) filters.is_repacked = true;

        onSearch(filters);
    };

    const handleClear = () => {
        setBatchNumber('');
        setStatus('');
        setDateFrom('');
        setDateTo('');
        setIsRepacked(false);
        onSearch({});
    };

    return (
        <Paper sx={{ p: 3, mb: 3 }}>
            <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                    <TextField
                        fullWidth
                        label="Batch Number"
                        value={batchNumber}
                        onChange={(e) => setBatchNumber(e.target.value)}
                        placeholder="B/2526/0001"
                    />
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <FormControl fullWidth>
                        <InputLabel>Status</InputLabel>
                        <Select
                            value={status}
                            label="Status"
                            onChange={(e) => setStatus(e.target.value)}
                        >
                            <MenuItem value="">All</MenuItem>
                            <MenuItem value={BatchStatus.ORDERED}>Ordered</MenuItem>
                            <MenuItem value={BatchStatus.RECEIVED}>Received</MenuItem>
                            <MenuItem value={BatchStatus.IN_GRADING}>In Grading</MenuItem>
                            <MenuItem value={BatchStatus.IN_PACKING}>In Packing</MenuItem>
                            <MenuItem value={BatchStatus.IN_INVENTORY}>In Inventory</MenuItem>
                            <MenuItem value={BatchStatus.ALLOCATED}>Allocated</MenuItem>
                            <MenuItem value={BatchStatus.IN_TRANSIT}>In Transit</MenuItem>
                            <MenuItem value={BatchStatus.DELIVERED}>Delivered</MenuItem>
                            <MenuItem value={BatchStatus.ARCHIVED}>Archived</MenuItem>
                        </Select>
                    </FormControl>
                </Grid>

                <Grid item xs={12} sm={6} md={2}>
                    <TextField
                        fullWidth
                        label="Date From"
                        type="date"
                        value={dateFrom}
                        onChange={(e) => setDateFrom(e.target.value)}
                        InputLabelProps={{ shrink: true }}
                    />
                </Grid>

                <Grid item xs={12} sm={6} md={2}>
                    <TextField
                        fullWidth
                        label="Date To"
                        type="date"
                        value={dateTo}
                        onChange={(e) => setDateTo(e.target.value)}
                        InputLabelProps={{ shrink: true }}
                    />
                </Grid>

                <Grid item xs={12} sm={6} md={2}>
                    <FormControlLabel
                        control={
                            <Checkbox
                                checked={isRepacked}
                                onChange={(e) => setIsRepacked(e.target.checked)}
                            />
                        }
                        label="Repacked Only"
                    />
                </Grid>

                <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button
                            variant="contained"
                            startIcon={<SearchIcon />}
                            onClick={handleSearch}
                            disabled={loading}
                        >
                            Search
                        </Button>
                        <Button
                            variant="outlined"
                            startIcon={<ClearIcon />}
                            onClick={handleClear}
                            disabled={loading}
                        >
                            Clear
                        </Button>
                    </Box>
                </Grid>
            </Grid>
        </Paper>
    );
}
