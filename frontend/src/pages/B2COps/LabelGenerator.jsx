/**
 * Label Generator Component
 * Version: 1.0.0
 * Last Updated: 2025-12-01
 *
 * Description:
 *   Generate printable PDF shipping labels from Excel/CSV files
 *   - File upload with preview
 *   - Configurable fonts and dimensions
 *   - Auto duplicate removal and validation
 *   - Batch processing (25 labels per PDF, ZIP if >25)
 *   - Activity logging
 */

import React, { useState } from 'react';
import {
    Box,
    Typography,
    Button,
    Paper,
    Alert,
    CircularProgress,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    TextField,
    Chip,
} from '@mui/material';
import {
    Upload as UploadIcon,
    Download as DownloadIcon,
    ExpandMore as ExpandMoreIcon,
    CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';
import { b2cOpsAPI } from '../../api';

const AVAILABLE_FONTS = [
    { value: 'Courier-Bold', label: 'Courier Bold (Default)' },
    { value: 'Helvetica', label: 'Helvetica' },
    { value: 'Helvetica-Bold', label: 'Helvetica Bold' },
    { value: 'Times-Roman', label: 'Times Roman' },
    { value: 'Times-Bold', label: 'Times Bold' },
    { value: 'Courier', label: 'Courier' },
];

export default function LabelGenerator() {
    const { enqueueSnackbar } = useSnackbar();

    // State
    const [file, setFile] = useState(null);
    const [previewData, setPreviewData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [generating, setGenerating] = useState(false);

    // Configuration
    const [fontName, setFontName] = useState('Courier-Bold');
    const [fontAdjustment, setFontAdjustment] = useState(0);
    const [widthMm, setWidthMm] = useState(50);
    const [heightMm, setHeightMm] = useState(30);

    // Drag and drop handlers
    const [isDragging, setIsDragging] = useState(false);

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);

        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile) {
            validateAndLoadFile(droppedFile);
        }
    };

    const validateAndLoadFile = async (uploadedFile) => {
        // Validate file type
        const validTypes = ['.xlsx', '.xls', '.csv'];
        const fileExt = uploadedFile.name.substring(uploadedFile.name.lastIndexOf('.')).toLowerCase();

        if (!validTypes.includes(fileExt)) {
            enqueueSnackbar('Invalid file type. Please upload Excel or CSV file.', { variant: 'error' });
            return;
        }

        // Validate file size (20MB)
        if (uploadedFile.size > 20 * 1024 * 1024) {
            enqueueSnackbar('File too large. Maximum size is 20 MB.', { variant: 'error' });
            return;
        }

        setFile(uploadedFile);
        setLoading(true);

        try {
            const preview = await b2cOpsAPI.previewLabels(uploadedFile);
            setPreviewData(preview);
            enqueueSnackbar('File loaded successfully!', { variant: 'success' });
        } catch (error) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to load file', { variant: 'error' });
            setFile(null);
            setPreviewData(null);
        } finally {
            setLoading(false);
        }
    };

    // Handle file upload (click)
    const handleFileUpload = (event) => {
        const uploadedFile = event.target.files[0];
        if (uploadedFile) {
            validateAndLoadFile(uploadedFile);
        }
    };

    // Handle label generation
    const handleGenerate = async () => {
        if (!previewData) return;

        setGenerating(true);
        try {
            const config = {
                font_name: fontName,
                font_adjustment: fontAdjustment,
                width_mm: widthMm,
                height_mm: heightMm,
            };

            const blob = await b2cOpsAPI.generateLabels(previewData.all_data, config);

            // Download the file
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            const timestamp = new Date().toISOString().slice(0, 16).replace(/[-:T]/g, '').slice(0, 13);
            const isZip = previewData.valid_labels > 25;
            link.download = `shipping_labels_${timestamp}.${isZip ? 'zip' : 'pdf'}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            enqueueSnackbar('Labels generated successfully!', { variant: 'success' });
        } catch (error) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to generate labels', { variant: 'error' });
        } finally {
            setGenerating(false);
        }
    };

    // DataGrid columns
    const columns = [
        { field: 'id', headerName: '#', width: 70 },
        { field: 'order #', headerName: 'Order #', width: 150 },
        { field: 'name', headerName: 'Customer Name', width: 300 },
    ];

    // Prepare rows for DataGrid
    const rows = previewData?.preview_data?.map((item, idx) => ({
        id: idx + 1,
        ...item,
    })) || [];

    return (
        <Box>
            {/* Header */}
            <Box sx={{ mb: 3 }}>
                <Typography variant="h4" gutterBottom fontWeight="bold">
                    🏷️ Shipping Labels
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Generate printable shipping labels from Excel/CSV files
                </Typography>
            </Box>

            {/* Configuration Panel */}
            <Accordion sx={{ mb: 3 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>⚙️ Label Configuration</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 3 }}>
                        {/* Font Settings */}
                        <Box>
                            <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                                Font Settings
                            </Typography>
                            <FormControl fullWidth sx={{ mb: 2 }}>
                                <InputLabel>Font Style</InputLabel>
                                <Select
                                    value={fontName}
                                    label="Font Style"
                                    onChange={(e) => setFontName(e.target.value)}
                                >
                                    {AVAILABLE_FONTS.map((font) => (
                                        <MenuItem key={font.value} value={font.value}>
                                            {font.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                            <TextField
                                label="Font Size Adjustment"
                                type="number"
                                value={fontAdjustment}
                                onChange={(e) => setFontAdjustment(parseInt(e.target.value) || 0)}
                                inputProps={{ min: -5, max: 5 }}
                                fullWidth
                                helperText="Fine-tune font size (+/- points)"
                            />
                        </Box>

                        {/* Label Dimensions */}
                        <Box>
                            <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                                Label Dimensions
                            </Typography>
                            <TextField
                                label="Width (mm)"
                                type="number"
                                value={widthMm}
                                onChange={(e) => setWidthMm(parseInt(e.target.value) || 50)}
                                inputProps={{ min: 10, max: 500 }}
                                fullWidth
                                sx={{ mb: 2 }}
                            />
                            <TextField
                                label="Height (mm)"
                                type="number"
                                value={heightMm}
                                onChange={(e) => setHeightMm(parseInt(e.target.value) || 30)}
                                inputProps={{ min: 10, max: 500 }}
                                fullWidth
                            />
                        </Box>
                    </Box>
                </AccordionDetails>
            </Accordion>

            {/* File Upload */}
            <Paper
                sx={{
                    p: 3,
                    mb: 3,
                    border: isDragging ? '2px dashed #1976d2' : '2px dashed transparent',
                    bgcolor: isDragging ? 'action.hover' : 'background.paper',
                    transition: 'all 0.2s ease'
                }}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <Typography variant="h6" gutterBottom>
                    📤 Upload File
                </Typography>
                <Box sx={{ mt: 2, textAlign: 'center', py: 3 }}>
                    <input
                        accept=".xlsx,.xls,.csv"
                        style={{ display: 'none' }}
                        id="file-upload"
                        type="file"
                        onChange={handleFileUpload}
                    />
                    <label htmlFor="file-upload">
                        <Button
                            variant="outlined"
                            component="span"
                            startIcon={<UploadIcon />}
                            disabled={loading}
                            size="large"
                        >
                            {loading ? 'Loading...' : 'Choose File or Drag & Drop Here'}
                        </Button>
                    </label>
                    {file && (
                        <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                            <CheckCircleIcon color="success" />
                            <Typography variant="body2">{file.name}</Typography>
                        </Box>
                    )}
                </Box>
                <Alert severity="info" sx={{ mt: 2 }}>
                    File must contain <strong>order #</strong> and <strong>name</strong> columns (case-insensitive)
                </Alert>
            </Paper>

            {/* Preview Section */}
            {previewData && (
                <Paper sx={{ p: 3, mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        📊 Summary
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 2, mb: 3 }}>
                        <Box>
                            <Typography variant="body2" color="text.secondary">
                                Total Entries
                            </Typography>
                            <Typography variant="h5">{previewData.total_entries}</Typography>
                        </Box>
                        <Box>
                            <Typography variant="body2" color="text.secondary">
                                Duplicates Removed
                            </Typography>
                            <Typography variant="h5">{previewData.duplicates_removed}</Typography>
                        </Box>
                        <Box>
                            <Typography variant="body2" color="text.secondary">
                                Labels to Generate
                            </Typography>
                            <Typography variant="h5" color="primary">
                                {previewData.valid_labels}
                            </Typography>
                        </Box>
                        <Box>
                            <Typography variant="body2" color="text.secondary">
                                PDF Files
                            </Typography>
                            <Typography variant="h5">
                                {Math.ceil(previewData.valid_labels / 25)}
                                {previewData.valid_labels > 25 && (
                                    <Chip label="ZIP" size="small" color="info" sx={{ ml: 1 }} />
                                )}
                            </Typography>
                        </Box>
                    </Box>

                    {previewData.valid_labels > 25 && (
                        <Alert severity="warning" sx={{ mb: 2 }}>
                            ⚠️ Generating {previewData.valid_labels} labels. Will be split into{' '}
                            {Math.ceil(previewData.valid_labels / 25)} PDFs (25 labels each) and zipped.
                        </Alert>
                    )}

                    <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                        👀 Data Preview
                    </Typography>
                    <Box sx={{ height: 400, width: '100%' }}>
                        <DataGrid
                            rows={rows}
                            columns={columns}
                            initialState={{
                                pagination: { paginationModel: { pageSize: 20 } },
                            }}
                            pageSizeOptions={[10, 20, 50]}
                            disableRowSelectionOnClick
                        />
                    </Box>
                    {previewData.preview_data.length < previewData.valid_labels && (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                            Showing first {previewData.preview_data.length} of {previewData.valid_labels} labels
                        </Typography>
                    )}

                    <Button
                        variant="contained"
                        color="primary"
                        size="large"
                        startIcon={generating ? <CircularProgress size={20} /> : <DownloadIcon />}
                        onClick={handleGenerate}
                        disabled={generating}
                        fullWidth
                        sx={{ mt: 3 }}
                    >
                        {generating ? 'Generating...' : `🚀 Generate ${previewData.valid_labels} Labels`}
                    </Button>
                </Paper>
            )}

            {/* Help Section */}
            {!previewData && (
                <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography>📖 How to Use</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <Typography variant="body2" component="div">
                            <strong>Instructions:</strong>
                            <ol>
                                <li>
                                    <strong>File Format:</strong> Upload Excel (.xlsx, .xls) or CSV file with columns{' '}
                                    <code>order #</code> and <code>name</code>
                                </li>
                                <li>
                                    <strong>Configuration:</strong> Optionally adjust font style, size, and label dimensions
                                </li>
                                <li>
                                    <strong>Preview:</strong> Review data summary and first 20 labels
                                </li>
                                <li>
                                    <strong>Generate:</strong> Click to create PDF labels (or ZIP if &gt;25 labels)
                                </li>
                            </ol>

                            <strong>Label Format:</strong>
                            <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
                                {`#12345
─────────────
CUSTOMER NAME`}
                            </pre>

                            <strong>Features:</strong>
                            <ul>
                                <li>Auto-removes duplicates and empty rows</li>
                                <li>25 labels per PDF (multiple PDFs zipped if needed)</li>
                                <li>Smart text wrapping and font sizing</li>
                                <li>One label per page for label printers</li>
                            </ul>
                        </Typography>
                    </AccordionDetails>
                </Accordion>
            )}
        </Box>
    );
}
