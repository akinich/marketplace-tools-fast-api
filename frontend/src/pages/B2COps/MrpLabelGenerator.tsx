/**
 * MRP Label Generator Component
 * Version: 1.0.0
 * Last Updated: 2025-12-01
 *
 * Description:
 *   Merge multiple product label PDFs based on Excel quantity data.
 *   - Tab 1: Generate Labels (Upload Excel -> Preview -> Generate)
 *   - Tab 2: Manage PDF Library (Upload/List/Delete PDFs in Cloud Storage)
 */

import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Button,
    Paper,
    Alert,
    CircularProgress,
    Tabs,
    Tab,
    Chip,
    IconButton,
    Tooltip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    DialogContentText,
} from '@mui/material';
import {
    Upload as UploadIcon,
    Download as DownloadIcon,
    CheckCircle as CheckCircleIcon,
    Delete as DeleteIcon,
    Refresh as RefreshIcon,
    PictureAsPdf as PdfIcon,
    Fullscreen as FullscreenIcon,
    FullscreenExit as FullscreenExitIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, useGridApiRef } from '@mui/x-data-grid';
import { useSnackbar } from 'notistack';
import { b2cOpsAPI } from '../../api';

interface FileUploadAreaProps {
    onFileSelect: (file: File) => void;
    accept: string;
    label: string;
    loading: boolean;
}

// --- Sub-component: File Upload Area ---
const FileUploadArea: React.FC<FileUploadAreaProps> = ({ onFileSelect, accept, label, loading }) => {
    const [isDragging, setIsDragging] = useState(false);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile) onFileSelect(droppedFile);
    };

    return (
        <Paper
            sx={{
                p: 3,
                border: isDragging ? '2px dashed #1976d2' : '2px dashed transparent',
                bgcolor: isDragging ? 'action.hover' : 'background.paper',
                transition: 'all 0.2s ease',
                textAlign: 'center'
            }}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            <Typography variant="h6" gutterBottom>
                {label}
            </Typography>
            <Box sx={{ mt: 2, py: 2 }}>
                <input
                    accept={accept}
                    style={{ display: 'none' }}
                    id="file-upload-mrp"
                    type="file"
                    onChange={(e) => e.target.files && e.target.files[0] && onFileSelect(e.target.files[0])}
                />
                <label htmlFor="file-upload-mrp">
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
            </Box>
        </Paper>
    );
};

interface MRPPreviewData {
    total_items: number;
    total_pages: number;
    valid_rows: number;
    missing_pdfs: string[];
    data: any[];
}

interface LibraryFile {
    name: string;
    size: number;
    created_at: string;
}

export default function MrpLabelGenerator() {
    const { enqueueSnackbar } = useSnackbar();
    const previewGridRef = useGridApiRef();
    const libraryGridRef = useGridApiRef();
    const [tabValue, setTabValue] = useState(0);

    // --- Tab 1 State: Generation ---
    const [excelFile, setExcelFile] = useState<File | null>(null);
    const [previewData, setPreviewData] = useState<MRPPreviewData | null>(null);
    const [loadingPreview, setLoadingPreview] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [isPreviewFullscreen, setIsPreviewFullscreen] = useState(false);

    // --- Tab 2 State: Library ---
    const [libraryFiles, setLibraryFiles] = useState<LibraryFile[]>([]);
    const [loadingLibrary, setLoadingLibrary] = useState(false);
    const [uploadingPdf, setUploadingPdf] = useState(false);
    const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
    const [isLibraryFullscreen, setIsLibraryFullscreen] = useState(false);

    // Fetch library on tab change
    useEffect(() => {
        if (tabValue === 1) {
            fetchLibrary();
        }
    }, [tabValue]);

    // --- Tab 1 Functions ---
    const handleExcelUpload = async (file: File) => {
        if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
            enqueueSnackbar('Invalid file type. Please upload Excel file.', { variant: 'error' });
            return;
        }

        setExcelFile(file);
        setLoadingPreview(true);
        setPreviewData(null);

        try {
            const data = await b2cOpsAPI.previewMrpLabels(file);
            setPreviewData(data);
            enqueueSnackbar('Excel file processed successfully!', { variant: 'success' });
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to process file', { variant: 'error' });
            setExcelFile(null);
        } finally {
            setLoadingPreview(false);
        }
    };

    const handleGenerate = async () => {
        if (!previewData) return;
        setGenerating(true);
        try {
            const blob = await b2cOpsAPI.generateMrpLabels(previewData.data);

            // Download
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            // Filename is in content-disposition header usually, but we can generate one
            const timestamp = new Date().toISOString().slice(0, 16).replace(/[-:T]/g, '').slice(0, 13);
            const isZip = previewData.total_pages > 25;
            link.download = `mrp_labels_${timestamp}.${isZip ? 'zip' : 'pdf'}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            enqueueSnackbar('Labels generated successfully!', { variant: 'success' });
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to generate labels', { variant: 'error' });
        } finally {
            setGenerating(false);
        }
    };

    // --- Tab 2 Functions ---
    const fetchLibrary = async () => {
        setLoadingLibrary(true);
        try {
            const files = await b2cOpsAPI.listMrpLibrary();
            setLibraryFiles(files);
        } catch (error) {
            enqueueSnackbar('Failed to load PDF library', { variant: 'error' });
        } finally {
            setLoadingLibrary(false);
        }
    };

    const handlePdfUpload = async (file: File) => {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            enqueueSnackbar('Only PDF files allowed', { variant: 'error' });
            return;
        }

        setUploadingPdf(true);
        try {
            await b2cOpsAPI.uploadMrpPdf(file);
            enqueueSnackbar(`Uploaded ${file.name}`, { variant: 'success' });
            fetchLibrary(); // Refresh list
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Upload failed', { variant: 'error' });
        } finally {
            setUploadingPdf(false);
        }
    };

    const handleDeletePdf = async () => {
        if (!deleteConfirm) return;
        try {
            await b2cOpsAPI.deleteMrpPdf(deleteConfirm);
            enqueueSnackbar('PDF deleted', { variant: 'success' });
            fetchLibrary();
        } catch (error) {
            enqueueSnackbar('Delete failed', { variant: 'error' });
        } finally {
            setDeleteConfirm(null);
        }
    };

    // --- Columns ---
    const previewColumns: GridColDef[] = [
        { field: 'id', headerName: '#', width: 70 },
        { field: 'item_id', headerName: 'Item ID', width: 120 },
        { field: 'variation_id', headerName: 'Variation ID', width: 120 },
        { field: 'quantity', headerName: 'Qty', width: 100 },
        {
            field: 'pdf_filename',
            headerName: 'PDF File',
            width: 200,
            renderCell: (params) => (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {params.row.is_available ? (
                        <CheckCircleIcon color="success" fontSize="small" />
                    ) : (
                        <Tooltip title="PDF Missing in Library">
                            <Chip label="Missing" color="error" size="small" />
                        </Tooltip>
                    )}
                    {params.value}
                </Box>
            )
        },
    ];

    const libraryColumns: GridColDef[] = [
        {
            field: 'name',
            headerName: 'Filename',
            width: 300,
            renderCell: (params) => (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PdfIcon color="error" />
                    {params.value}
                </Box>
            )
        },
        {
            field: 'size',
            headerName: 'Size (KB)',
            width: 120,
            valueGetter: (params) => Math.round(params.row.size / 1024)
        },
        {
            field: 'created_at',
            headerName: 'Uploaded At',
            width: 200,
            valueFormatter: (params) => new Date(params.value).toLocaleString()
        },
        {
            field: 'actions',
            headerName: 'Actions',
            width: 100,
            renderCell: (params) => (
                <IconButton
                    color="error"
                    onClick={() => setDeleteConfirm(params.row.name)}
                >
                    <DeleteIcon />
                </IconButton>
            )
        }
    ];

    return (
        <Box>
            <Box sx={{ mb: 3 }}>
                <Typography variant="h4" gutterBottom fontWeight="bold">
                    🔖 MRP Label Generator
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Merge product label PDFs based on Excel quantity data
                </Typography>
            </Box>

            <Paper sx={{ mb: 3 }}>
                <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
                    <Tab label="📊 Generate Labels" />
                    <Tab label="📂 Manage PDF Library" />
                </Tabs>

                {/* TAB 1: GENERATE */}
                {tabValue === 0 && (
                    <Box sx={{ p: 3 }}>
                        <FileUploadArea
                            label="Upload Excel File (.xlsx)"
                            accept=".xlsx,.xls"
                            onFileSelect={handleExcelUpload}
                            loading={loadingPreview}
                        />

                        {excelFile && (
                            <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'center' }}>
                                <CheckCircleIcon color="success" />
                                <Typography>{excelFile.name}</Typography>
                            </Box>
                        )}

                        {previewData && (
                            <Box sx={{ mt: 4 }}>
                                <Typography variant="h6" gutterBottom>Summary</Typography>
                                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 2, mb: 3 }}>
                                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                                        <Typography variant="body2" color="text.secondary">Total Items</Typography>
                                        <Typography variant="h5">{previewData.total_items}</Typography>
                                    </Paper>
                                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                                        <Typography variant="body2" color="text.secondary">Total Pages</Typography>
                                        <Typography variant="h5">{previewData.total_pages}</Typography>
                                    </Paper>
                                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                                        <Typography variant="body2" color="text.secondary">Missing PDFs</Typography>
                                        <Typography variant="h5" color={previewData.missing_pdfs.length > 0 ? "error" : "success"}>
                                            {previewData.missing_pdfs.length}
                                        </Typography>
                                    </Paper>
                                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                                        <Typography variant="body2" color="text.secondary">Output Files</Typography>
                                        <Typography variant="h5">
                                            {Math.ceil(previewData.total_pages / 25)}
                                            {previewData.total_pages > 25 && <Chip label="ZIP" size="small" color="info" sx={{ ml: 1 }} />}
                                        </Typography>
                                    </Paper>
                                </Box>

                                {previewData.missing_pdfs.length > 0 && (
                                    <Alert severity="warning" sx={{ mb: 3 }}>
                                        ⚠️ {previewData.missing_pdfs.length} PDFs are missing from the library. These items will be skipped.
                                        <Box sx={{ mt: 1 }}>
                                            Missing: {previewData.missing_pdfs.slice(0, 10).join(', ')}
                                            {previewData.missing_pdfs.length > 10 && '...'}
                                        </Box>
                                    </Alert>
                                )}

                                <Typography variant="h6" gutterBottom>Data Preview</Typography>
                                <Box sx={{
                                    height: isPreviewFullscreen ? '100vh' : 400,
                                    width: '100%',
                                    ...(isPreviewFullscreen && {
                                        position: 'fixed',
                                        top: 0,
                                        left: 0,
                                        right: 0,
                                        bottom: 0,
                                        zIndex: 9999,
                                        bgcolor: 'background.paper',
                                    }),
                                    mb: 3,
                                }}>
                                    <DataGrid
                                        apiRef={previewGridRef}
                                        rows={previewData.data?.map((row, i) => ({ id: i, ...row })) || []}
                                        columns={previewColumns}
                                        pageSizeOptions={[10, 25, 50]}
                                        initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
                                        slots={{
                                            toolbar: () => (
                                                <Box sx={{ p: 1, display: 'flex', gap: 1, alignItems: 'center', borderBottom: '1px solid #e0e0e0' }}>
                                                    <Box sx={{ flexGrow: 1 }} />
                                                    <Button
                                                        startIcon={isPreviewFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
                                                        onClick={() => setIsPreviewFullscreen(!isPreviewFullscreen)}
                                                        size="small"
                                                    >
                                                        {isPreviewFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
                                                    </Button>
                                                </Box>
                                            ),
                                        }}
                                        sx={{
                                            border: '1px solid #e0e0e0',
                                            height: '100%',
                                            '& .MuiDataGrid-cell': {
                                                borderRight: '1px solid #e0e0e0',
                                            },
                                            '& .MuiDataGrid-columnHeaders': {
                                                borderBottom: '2px solid #e0e0e0',
                                                backgroundColor: '#fafafa',
                                            },
                                            '& .MuiDataGrid-columnHeader': {
                                                borderRight: '1px solid #e0e0e0',
                                            },
                                        }}
                                    />
                                </Box>

                                <Button
                                    variant="contained"
                                    size="large"
                                    fullWidth
                                    startIcon={generating ? <CircularProgress size={20} color="inherit" /> : <DownloadIcon />}
                                    onClick={handleGenerate}
                                    disabled={generating || previewData.valid_rows === 0}
                                >
                                    {generating ? 'Generating...' : '🚀 Generate Merged PDF'}
                                </Button>
                            </Box>
                        )}
                    </Box>
                )}

                {/* TAB 2: LIBRARY */}
                {tabValue === 1 && (
                    <Box sx={{ p: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                            <Typography variant="h6">PDF Library</Typography>
                            <Button startIcon={<RefreshIcon />} onClick={fetchLibrary}>Refresh</Button>
                        </Box>

                        <Box sx={{ mb: 4 }}>
                            <FileUploadArea
                                label="Upload PDF Files"
                                accept=".pdf"
                                onFileSelect={handlePdfUpload}
                                loading={uploadingPdf}
                            />
                        </Box>

                        <Box sx={{
                            height: isLibraryFullscreen ? '100vh' : 500,
                            width: '100%',
                            ...(isLibraryFullscreen && {
                                position: 'fixed',
                                top: 0,
                                left: 0,
                                right: 0,
                                bottom: 0,
                                zIndex: 9999,
                                bgcolor: 'background.paper',
                            })
                        }}>
                            <DataGrid
                                apiRef={libraryGridRef}
                                rows={libraryFiles.map((f, i) => ({ id: i, ...f }))}
                                columns={libraryColumns}
                                loading={loadingLibrary}
                                pageSizeOptions={[10, 25, 50]}
                                initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
                                slots={{
                                    toolbar: () => (
                                        <Box sx={{ p: 1, display: 'flex', gap: 1, alignItems: 'center', borderBottom: '1px solid #e0e0e0' }}>
                                            <Box sx={{ flexGrow: 1 }} />
                                            <Button
                                                startIcon={isLibraryFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
                                                onClick={() => setIsLibraryFullscreen(!isLibraryFullscreen)}
                                                size="small"
                                            >
                                                {isLibraryFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
                                            </Button>
                                        </Box>
                                    ),
                                }}
                                sx={{
                                    border: '1px solid #e0e0e0',
                                    height: '100%',
                                    '& .MuiDataGrid-cell': {
                                        borderRight: '1px solid #e0e0e0',
                                    },
                                    '& .MuiDataGrid-columnHeaders': {
                                        borderBottom: '2px solid #e0e0e0',
                                        backgroundColor: '#fafafa',
                                    },
                                    '& .MuiDataGrid-columnHeader': {
                                        borderRight: '1px solid #e0e0e0',
                                    },
                                }}
                            />
                        </Box>
                    </Box>
                )}
            </Paper>

            {/* Delete Confirmation Dialog */}
            <Dialog open={!!deleteConfirm} onClose={() => setDeleteConfirm(null)}>
                <DialogTitle>Confirm Delete</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        Are you sure you want to delete <strong>{deleteConfirm}</strong>? This action cannot be undone.
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteConfirm(null)}>Cancel</Button>
                    <Button onClick={handleDeletePdf} color="error" autoFocus>Delete</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}
