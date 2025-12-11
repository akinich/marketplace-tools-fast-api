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

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            setFile(event.target.files[0]);
            setResult(null);
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

            if (importResult.success) {
                enqueueSnackbar(importResult.message, { variant: 'success' });
            } else {
                enqueueSnackbar('Import completed with errors', { variant: 'warning' });
            }
        } catch (error: any) {
            enqueueSnackbar('Failed to import file', { variant: 'error' });
        } finally {
            setImporting(false);
        }
    };

    const handleClose = () => {
        setFile(null);
        setResult(null);
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
                        <li>Fill in SKU, Price, and optional Notes columns</li>
                        <li>SKUs must exist in your item database</li>
                        <li>Upload the completed file here</li>
                    </ol>
                </Alert>

                <Box
                    sx={{
                        border: '2px dashed #ccc',
                        borderRadius: 2,
                        p: 3,
                        textAlign: 'center',
                        mb: 2,
                    }}
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
                    {file && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
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
                        <Alert severity={result.items_failed > 0 ? 'warning' : 'success'}>
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
                                    <strong>Errors:</strong>
                                </Typography>
                                <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
                                    {result.errors.map((err, idx) => (
                                        <ListItem key={idx}>
                                            <ListItemText
                                                primary={`Row ${err.row_number}: ${err.sku}`}
                                                secondary={err.error}
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
