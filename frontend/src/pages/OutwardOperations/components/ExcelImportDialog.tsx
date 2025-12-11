import { useState } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Box,
    Typography,
    Alert,
    LinearProgress,
    List,
    ListItem,
    ListItemText,
} from '@mui/material';
import { Upload as UploadIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import priceListAPI, { ExcelImportResponse } from '../../../api/priceList';

interface ExcelImportDialogProps {
    open: boolean;
    priceListId: number;
    onClose: (refresh?: boolean) => void;
}

function ExcelImportDialog({ open, priceListId, onClose }: ExcelImportDialogProps) {
    const { enqueueSnackbar } = useSnackbar();
    const [file, setFile] = useState<File | null>(null);
    const [importing, setImporting] = useState(false);
    const [result, setResult] = useState<ExcelImportResponse | null>(null);
    const [isDragging, setIsDragging] = useState(false);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            setFile(event.target.files[0]);
            setResult(null);
        }
    };

    const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        setIsDragging(false);
    };

    const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        setIsDragging(false);

        const droppedFile = event.dataTransfer.files[0];
        if (droppedFile && (droppedFile.name.endsWith('.xlsx') || droppedFile.name.endsWith('.xls'))) {
            setFile(droppedFile);
            setResult(null);
        } else {
            enqueueSnackbar('Please drop an Excel file (.xlsx or .xls)', { variant: 'error' });
        }
    };

    const handleImport = async () => {
        if (!file) {
            enqueueSnackbar('Please select a file', { variant: 'error' });
            return;
        }

        setImporting(true);
        setResult(null);

        try {
            const importResult = await priceListAPI.importFromExcel(priceListId, file);
            setResult(importResult);

            if (importResult.items_failed === 0 && importResult.items_imported > 0) {
                enqueueSnackbar(`✅ ${importResult.message}`, { variant: 'success' });
            } else if (importResult.items_imported === 0 && importResult.items_updated === 0) {
                enqueueSnackbar(`❌ No items imported. Check errors below.`, { variant: 'error' });
            } else {
                enqueueSnackbar(importResult.message, { variant: 'warning' });
            }
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to import file', { variant: 'error' });
        } finally {
            setImporting(false);
        }
    };

    const handleClose = () => {
        setFile(null);
        setResult(null);
        setIsDragging(false);
        onClose(result?.items_imported || result?.items_updated ? true : false);
    };

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
            <DialogTitle>📤 Import Items from Excel</DialogTitle>
            <DialogContent>
                <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                        <strong>How to use:</strong>
                    </Typography>
                    <ol style={{ margin: '8px 0', paddingLeft: '20px' }}>
                        <li>Download the template if you haven't already</li>
                        <li>Fill in <strong>Item Name</strong>, <strong>Price</strong>, and optional Notes columns</li>
                        <li><strong>⚠️ Item names must EXACTLY match those in your item database</strong></li>
                        <li>Upload the completed file here</li>
                    </ol>
                </Alert>

                <Box
                    sx={{
                        border: isDragging ? '2px solid #4CAF50' : '2px dashed #ccc',
                        borderRadius: 2,
                        p: 3,
                        textAlign: 'center',
                        mb: 2,
                        backgroundColor: isDragging ? '#f1f8f4' : 'transparent',
                        transition: 'all 0.2s ease',
                    }}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                >
                    <input
                        accept=".xlsx,.xls"
                        style={{ display: 'none' }}
                        id="excel-file-input"
                        type="file"
                        onChange={handleFileChange}
                    />
                    <label htmlFor="excel-file-input">
                        <Button
                            variant="contained"
                            component="span"
                            startIcon={<UploadIcon />}
                            disabled={importing}
                        >
                            Select Excel File
                        </Button>
                    </label>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        or drag and drop file here
                    </Typography>
                    {file && (
                        <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
                            📄 {file.name}
                        </Typography>
                    )}
                </Box>

                {importing && (
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" gutterBottom>
                            Importing...
                        </Typography>
                        <LinearProgress />
                    </Box>
                )}

                {result && (
                    <Box sx={{ mt: 2 }}>
                        <Alert severity={result.items_imported === 0 && result.items_updated === 0 ? 'error' : result.items_failed > 0 ? 'warning' : 'success'}>
                            <Typography variant="body2">
                                <strong>{result.message}</strong>
                            </Typography>
                            <Typography variant="body2">
                                ✅ Imported: {result.items_imported} | 🔄 Updated: {result.items_updated} | ❌ Failed: {result.items_failed}
                            </Typography>
                        </Alert>

                        {result.errors && result.errors.length > 0 && (
                            <Box sx={{ mt: 2 }}>
                                <Typography variant="body2" color="error" gutterBottom>
                                    <strong>❌ Errors Found ({result.errors.length}):</strong>
                                </Typography>
                                <List dense sx={{ maxHeight: 200, overflow: 'auto', backgroundColor: '#fff3e0', borderRadius: 1, p: 1 }}>
                                    {result.errors.map((err, idx) => (
                                        <ListItem key={idx}>
                                            <ListItemText
                                                primary={`Row ${err.row_number}: Item "${err.sku}"`}
                                                secondary={err.error}
                                                secondaryTypographyProps={{ color: 'error' }}
                                            />
                                        </ListItem>
                                    ))}
                                </List>
                            </Box>
                        )}
                    </Box>
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose}>Close</Button>
                <Button
                    onClick={handleImport}
                    variant="contained"
                    disabled={!file || importing}
                >
                    Import
                </Button>
            </DialogActions>
        </Dialog>
    );
}

export default ExcelImportDialog;
