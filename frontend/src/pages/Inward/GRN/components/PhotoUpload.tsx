/**
 * ================================================================================
 * Photo Upload Component (GRN Version)
 * ================================================================================
 * Adapted for GRN Management
 */

import { useState, useRef, useEffect } from 'react';
import {
    Box,
    Button,
    IconButton,
    Typography,
    Paper,
    Grid,
    CircularProgress,
} from '@mui/material';
import {
    CloudUpload as UploadIcon,
    CameraAlt as CameraIcon,
    Delete as DeleteIcon,
    Image as ImageIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { validatePhoto } from '../../../../utils/photoUpload';
import { GRNPhotoResponse } from '../../../../api/grn';

interface PhotoUploadProps {
    onUpload: (files: File[]) => void;
    onDelete?: (photoId: number) => void;
    maxPhotos?: number;
    required?: boolean;
    initialPhotos?: File[];
    existingPhotos?: GRNPhotoResponse[];
    label?: string;
}

export default function PhotoUpload({
    onUpload,
    onDelete,
    maxPhotos = 10,
    required = true,
    initialPhotos = [],
    existingPhotos = [],
    label = "Drag & Drop Photos Here",
}: PhotoUploadProps) {
    const { enqueueSnackbar } = useSnackbar();
    const [newPhotos, setNewPhotos] = useState<File[]>(initialPhotos);
    const [previews, setPreviews] = useState<string[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const cameraInputRef = useRef<HTMLInputElement>(null);

    // Generate preview URLs for NEW photos
    useEffect(() => {
        const newPreviews = newPhotos.map((file) => URL.createObjectURL(file));
        setPreviews(newPreviews);
        return () => {
            newPreviews.forEach((url) => URL.revokeObjectURL(url));
        };
    }, [newPhotos]);

    // Handle file selection
    const handleFiles = (files: FileList | null) => {
        if (!files || files.length === 0) return;

        setUploading(true);
        const fileArray = Array.from(files);
        const validFiles: File[] = [];

        // Validate each file
        for (const file of fileArray) {
            const validation = validatePhoto(file);
            if (!validation.valid) {
                enqueueSnackbar(validation.error, { variant: 'error' });
                continue;
            }

            // Check max photos limit (existing + new)
            if (existingPhotos.length + newPhotos.length + validFiles.length >= maxPhotos) {
                enqueueSnackbar(`Maximum ${maxPhotos} photos allowed`, { variant: 'warning' });
                break;
            }

            validFiles.push(file);
        }

        if (validFiles.length > 0) {
            const updatedPhotos = [...newPhotos, ...validFiles];
            setNewPhotos(updatedPhotos);
            onUpload(updatedPhotos);
            enqueueSnackbar(`${validFiles.length} photo(s) added`, { variant: 'success' });
        }

        setUploading(false);
    };

    // Handle drag events
    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        handleFiles(e.dataTransfer.files);
    };

    // Handle file browser
    const handleBrowseClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        handleFiles(e.target.files);
        // Reset input value to allow selecting the same file again
        e.target.value = '';
    };

    // Handle camera
    const handleCameraClick = () => {
        cameraInputRef.current?.click();
    };

    const handleCameraInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        handleFiles(e.target.files);
        e.target.value = '';
    };

    // Handle delete new photo
    const handleDeleteNewPhoto = (index: number) => {
        const updatedPhotos = newPhotos.filter((_, i) => i !== index);
        setNewPhotos(updatedPhotos);
        onUpload(updatedPhotos);
        enqueueSnackbar('Photo removed', { variant: 'info' });
    };

    // NOTE: Deleting existing photos usually requires API call. 
    // For this component we'll assume we only manage NEW photos upload here, 
    // or we might need a callback to delete existing.
    // The handover snippet shows `deletePhoto` in API but doesn't show it passed to this component.
    // We will display existing photos as read-only or just preview.

    const totalPhotos = existingPhotos.length + newPhotos.length;

    return (
        <Box>
            <Typography variant="subtitle2" gutterBottom>
                {label} {required && '*'}
            </Typography>

            {/* Upload Area */}
            <Paper
                sx={{
                    p: 3,
                    border: '2px dashed',
                    borderColor: isDragging || (required && totalPhotos === 0) ? 'primary.main' : 'grey.300',
                    backgroundColor: isDragging ? 'action.hover' : 'background.paper',
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    '&:hover': {
                        borderColor: 'primary.main',
                        backgroundColor: 'action.hover',
                    },
                }}
                onDragEnter={handleDragEnter}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={handleBrowseClick}
            >
                <Box sx={{ textAlign: 'center' }}>
                    {uploading ? (
                        <CircularProgress />
                    ) : (
                        <>
                            <ImageIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                            <Typography variant="h6" gutterBottom>
                                Drag & Drop Photos Here
                            </Typography>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                or click to browse
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                Max 10MB per photo • JPG, JPEG, PNG
                                {required && ' • Minimum 1 photo required'}
                            </Typography>
                        </>
                    )}
                </Box>
            </Paper>

            {/* Action Buttons */}
            <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                <Button
                    variant="outlined"
                    startIcon={<UploadIcon />}
                    onClick={handleBrowseClick}
                    disabled={uploading || totalPhotos >= maxPhotos}
                >
                    Browse Files
                </Button>
                <Button
                    variant="outlined"
                    startIcon={<CameraIcon />}
                    onClick={handleCameraClick}
                    disabled={uploading || totalPhotos >= maxPhotos}
                >
                    Take Photo
                </Button>
                <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto', alignSelf: 'center' }}>
                    {totalPhotos} / {maxPhotos} photos
                </Typography>
            </Box>

            {/* Hidden File Inputs */}
            <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/jpg,image/png"
                multiple
                style={{ display: 'none' }}
                onChange={handleFileInputChange}
            />
            <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                style={{ display: 'none' }}
                onChange={handleCameraInputChange}
            />

            {/* Photo Previews */}
            {totalPhotos > 0 && (
                <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                        Photos ({totalPhotos})
                    </Typography>
                    <Grid container spacing={2}>
                        {/* Existing Photos */}
                        {existingPhotos.map((photo) => (
                            <Grid item xs={6} sm={4} md={3} key={`existing-${photo.id}`}>
                                <Paper
                                    sx={{
                                        position: 'relative',
                                        paddingTop: '100%',
                                        overflow: 'hidden',
                                        '&:hover .delete-button': {
                                            opacity: 1,
                                        },
                                    }}
                                >
                                    <Box
                                        component="img"
                                        src={photo.photo_url}
                                        alt={`Existing ${photo.id}`}
                                        sx={{
                                            position: 'absolute',
                                            top: 0,
                                            left: 0,
                                            width: '100%',
                                            height: '100%',
                                            objectFit: 'cover',
                                        }}
                                    />

                                    {onDelete && (
                                        <IconButton
                                            className="delete-button"
                                            onClick={() => onDelete(photo.id)}
                                            sx={{
                                                position: 'absolute',
                                                top: 4,
                                                right: 4,
                                                backgroundColor: 'rgba(0, 0, 0, 0.6)',
                                                color: 'white',
                                                opacity: 0,
                                                transition: 'opacity 0.3s',
                                                '&:hover': {
                                                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                                },
                                            }}
                                            size="small"
                                        >
                                            <DeleteIcon fontSize="small" />
                                        </IconButton>
                                    )}
                                    <Paper
                                        sx={{
                                            position: 'absolute',
                                            bottom: 0,
                                            left: 0,
                                            right: 0,
                                            mr: onDelete ? 0 : 0, // Just consistent
                                        }}
                                        elevation={0}
                                        square
                                    >
                                        {/* No size info for existing usually, so maybe just hover effect */}
                                    </Paper>
                                </Paper>
                            </Grid>
                        ))}

                        {/* New Photos */}
                        {newPhotos.map((photo, index) => (
                            <Grid item xs={6} sm={4} md={3} key={`new-${index}`}>
                                <Paper
                                    sx={{
                                        position: 'relative',
                                        paddingTop: '100%',
                                        overflow: 'hidden',
                                        '&:hover .delete-button': {
                                            opacity: 1,
                                        },
                                    }}
                                >
                                    <Box
                                        component="img"
                                        src={previews[index]}
                                        alt={`New Upload ${index + 1}`}
                                        sx={{
                                            position: 'absolute',
                                            top: 0,
                                            left: 0,
                                            width: '100%',
                                            height: '100%',
                                            objectFit: 'cover',
                                        }}
                                    />
                                    <IconButton
                                        className="delete-button"
                                        onClick={() => handleDeleteNewPhoto(index)}
                                        sx={{
                                            position: 'absolute',
                                            top: 4,
                                            right: 4,
                                            backgroundColor: 'rgba(0, 0, 0, 0.6)',
                                            color: 'white',
                                            opacity: 0,
                                            transition: 'opacity 0.3s',
                                            '&:hover': {
                                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                            },
                                        }}
                                        size="small"
                                    >
                                        <DeleteIcon fontSize="small" />
                                    </IconButton>
                                    <Typography
                                        variant="caption"
                                        sx={{
                                            position: 'absolute',
                                            bottom: 0,
                                            left: 0,
                                            right: 0,
                                            backgroundColor: 'rgba(0, 0, 0, 0.6)',
                                            color: 'white',
                                            p: 0.5,
                                            textAlign: 'center',
                                        }}
                                    >
                                        {(photo.size / 1024 / 1024).toFixed(2)} MB
                                    </Typography>
                                </Paper>
                            </Grid>
                        ))}
                    </Grid>
                </Box>
            )}

            {/* Validation Message */}
            {required && totalPhotos === 0 && (
                <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                    At least 1 photo is required
                </Typography>
            )}
        </Box>
    );
}
