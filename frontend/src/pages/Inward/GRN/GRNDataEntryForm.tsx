import React, { useState, useEffect, useCallback } from 'react';
import {
    Box, Button, Card, TextField, Select, MenuItem,
    Table, TableBody, TableCell, TableHead, TableRow,
    Alert, Chip, Typography, CircularProgress,
    FormControl, InputLabel
} from '@mui/material';
import { TimePicker, DatePicker } from '@mui/x-date-pickers';
import { useParams, useNavigate } from 'react-router-dom';
import { grnAPI, GRNDetailResponse, GRNUpdateRequest, GRNItemUpdate, GRNItemResponse } from '../../../api/grn';
// @ts-ignore
import { adminAPI } from '../../../api/index';
import { format } from 'date-fns';
import PhotoUpload from './components/PhotoUpload';
import CostAllocationToggle from './components/CostAllocationToggle';
import { useSnackbar } from 'notistack';

interface ItemRow extends GRNItemUpdate {
    item_name: string;
    expected_quantity: number;
    final_accepted: number;
    // Photos are handled by matching with grn.photos, not stored in ItemRow state directly for upload
    // But for UI state we might track something if needed, but PhotoUpload component handles its own state for new files
}

const GRNDataEntryForm: React.FC = () => {
    const { grnId } = useParams<{ grnId: string }>();
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();

    const [grn, setGRN] = useState<GRNDetailResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [transportMethod, setTransportMethod] = useState('');
    const [boxes, setBoxes] = useState<number>(0);
    const [receivingTime, setReceivingTime] = useState<Date | null>(null);
    const [receivingDate, setReceivingDate] = useState<Date | null>(null);
    const [receiverId, setReceiverId] = useState<number | null>(null);
    const [items, setItems] = useState<ItemRow[]>([]);
    const [users, setUsers] = useState<{ id: number, name: string }[]>([]);

    useEffect(() => {
        const loadUsers = async () => {
            try {
                // Fetch users for receiver dropdown (Limit to 100 for now or add search)
                const response = await adminAPI.getUsers({ limit: 100 });
                const userList = response.users.map((u: any) => ({
                    id: u.id,
                    name: u.full_name || u.email
                }));
                setUsers(userList);
            } catch (error) {
                console.error('Failed to load users:', error);
                // Fallback to placeholder if admin API fails (e.g. permission issues)
            }
        };
        loadUsers();
    }, []);

    const loadGRN = useCallback(async () => {
        if (!grnId) return;
        try {
            setLoading(true);
            const response = await grnAPI.getById(parseInt(grnId));
            const data = response.data;
            setGRN(data);

            // Initialize form state
            setTransportMethod(data.transport_method || '');
            setBoxes(data.number_of_boxes || 0);

            if (data.receiving_time) {
                const [hours, minutes, seconds] = data.receiving_time.split(':');
                const date = new Date();
                date.setHours(parseInt(hours), parseInt(minutes), parseInt(seconds || '0'));
                setReceivingTime(date);
            }

            if (data.receiving_date) {
                setReceivingDate(new Date(data.receiving_date));
            }

            setReceiverId(data.receiver_id || null);

            // Initialize items
            const itemRows: ItemRow[] = data.items.map((item: GRNItemResponse) => ({
                item_id: item.item_id,
                item_name: item.item_name,
                expected_quantity: item.expected_quantity || 0, // Ensure field exists in API response
                gross_received: item.gross_received || 0,
                damage: item.damage || 0,
                reject: item.reject || 0,
                damage_cost_allocation: item.damage_cost_allocation,
                reject_cost_allocation: item.reject_cost_allocation,
                notes: item.notes,
                final_accepted: (item.gross_received || 0) - (item.damage || 0) - (item.reject || 0)
            }));
            setItems(itemRows);

        } catch (error) {
            console.error('Failed to load GRN:', error);
            enqueueSnackbar('Failed to load GRN details', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    }, [grnId, enqueueSnackbar]);

    useEffect(() => {
        loadGRN();
    }, [loadGRN]);

    // Calculate final accepted
    const calculateFinalAccepted = (item: ItemRow) => {
        // Ensure numbers are not NaN or negative for calculation
        const gross = isNaN(item.gross_received) ? 0 : item.gross_received;
        const damage = isNaN(item.damage) ? 0 : item.damage;
        const reject = isNaN(item.reject) ? 0 : item.reject;
        return gross - damage - reject;
    };

    // Handle item change
    const handleItemChange = (index: number, field: keyof ItemRow, value: any) => {
        const updated = [...items];
        updated[index] = { ...updated[index], [field]: value };

        // Recalculate final accepted
        if (field === 'gross_received' || field === 'damage' || field === 'reject') {
            updated[index].final_accepted = calculateFinalAccepted(updated[index]);
        }

        setItems(updated);
    };

    // Upload photos
    const handlePhotoUpload = async (itemId: number, photoType: 'damage' | 'reject', files: File[]) => {
        if (!grnId) return;
        try {
            // Find new files - this handler might be called with all files, but we only upload new ones?
            // Actually PhotoUpload component as adapted maintains "newPhotos".
            // But here we are passed 'files' which might be just the new ones if we triggered it.
            // Wait, PhotoUpload component as I wrote it triggers onUpload with ALL new files.
            // So if I add 1, onUpload([f1]). If I add another, onUpload([f1, f2]).
            // This is problematic if I call api.uploadPhotos resulting in double uploads.
            // The User snippet usage assumes: onUpload={(files) => handlePhotoUpload(..., files)}
            // And in PhotoUpload original: onPhotosChange(newPhotos).
            // If I upload immediately, I should clear the new photos in the component?
            // Or I should only upload when clicking "Save"?
            // The user snippet says:
            // await grnAPI.uploadPhotos(...)
            // loadGRN()
            // This suggests IMMEDIATE upload.

            // So in PhotoUpload, I should probably expose a way to "clear" new photos after successful upload?
            // Or better: The PhotoUpload component I wrote keeps state.
            // If I use the snippet approach, I should likely change PhotoUpload to upload on drop/selection immediately?
            // The snippet: 
            /*
              const handlePhotoUpload = async (..., files) => {
                  await grnAPI.uploadPhotos(...);
                  loadGRN();
              }
            */
            // This implies `files` are the files to be uploaded.
            // My adapted PhotoUpload calls onUpload with All currently selected NEW files.
            // If I immediately upload, I should just upload the *latest* file?
            // Or I need to change PhotoUpload to be "State-less" regarding new files if instant upload is used?
            // Actually, let's just upload ALL files passed.
            // But wait, if I have [f1] uploaded, then I add [f2], PhotoUpload sends [f1, f2].
            // Then I upload f1 again.

            // FIX: I will modify handlePhotoUpload to upload ONLY the newly added files?
            // Or easier: Just upload all passed files and rely on backend not duplication or just accept it?
            // No, backend probably stores file.

            // PROPER FIX: modify PhotoUpload to NOT maintain state of new files if we are doing instant upload.
            // But PhotoUpload as I wrote it is "controlled" or "uncontrolled" internal state.

            // Alternative: Only upload when clicking "Save Draft" or "Finalize"?
            // Snippet for handleSave: "save items data".
            // Snippet for handlePhotoUpload: "await grnAPI.uploadPhotos... loadGRN()".
            // This confirms instant upload for photos.

            // Therefore, PhotoUpload component should probably just accept a prop "onFileSelect" that gives the NEW file(s) and then it clears its internal state?
            // Or I just use the "new files" differently.

            // Since I already wrote PhotoUpload.tsx, I will use it carefully.
            // I passed `onUpload`.
            // I will change handlePhotoUpload to ONLY upload the *last added* file(s)? 
            // No, the component sends the Full list of new files.
            // I'll update `PhotoUpload.tsx` later if needed, but for now, I will just iterate and upload all `files` that are NOT already in `grn.photos`?
            // But `files` are File objects, `grn.photos` are URLs. Can't compare easy.

            // BETTER APPROACH:
            // The `PhotoUpload` component I wrote returns *Accumulated* new files.
            // I should probably *not* use instant upload in `handlePhotoUpload` if the component accumulates them.
            // I should wait for `Save` button?
            // BUT, snippet explicitly has `handlePhotoUpload` calling API.

            // Lets look at `PhotoUpload` again.
            // It has `onUpload(updatedPhotos)`.
            // If I want instant upload, I should probably modify `PhotoUpload` to have an `uploadMode` or similar?
            // Or, I simply change the logic in `GRNDataEntryForm`?

            // I will change `GRNDataEntryForm` to only `setItems` state with the files, and upload them in `handleSave`?
            // BUT `handleSave` in snippet uses `items.map(...)` sending data to `grnAPI.update`.
            // The `GRNUpdateRequest` interface does NOT include photos. Photos are separate API.
            // So Photos MUST be uploaded separately.

            // So, `handlePhotoUpload` MUST effectively upload files.
            // I will assume `PhotoUpload` component expects `onUpload` to be called with *pending* files.
            // If I upload them immediately, I should probably clear the pending files in the component.
            // But I don't have a ref to clear them easily.

            // I will stick to this:
            // I will upload files. And since `PhotoUpload` keeps them in `newPhotos`, I will likely upload duplicates if I add more files.
            // THIS IS A BUG in my plan + component combination.
            // I will modify `PhotoUpload.tsx` to accepting a prop `instantUpload={true}`?
            // Or, I will just upload them all, and then *force a re-mount* of PhotoUpload by changing key?
            // Yes, `loadGRN()` runs, `grn` updates. `existingPhotos` updates.
            // If I change the `key` of `PhotoUpload` it will reset `newPhotos` to empty.
            // I can use `key={item.item_id + '_damage_' + grn.photos.length}`.

            await grnAPI.uploadPhotos(parseInt(grnId), itemId, photoType, files);
            enqueueSnackbar('Photos uploaded successfully', { variant: 'success' });
            loadGRN();
        } catch (error) {
            console.error('Photo upload failed:', error);
            enqueueSnackbar('Photo upload failed', { variant: 'error' });
        }
    };

    const handleDeletePhoto = async (photoId: number) => {
        try {
            await grnAPI.deletePhoto(photoId);
            enqueueSnackbar('Photo deleted', { variant: 'info' });
            loadGRN();
        } catch (error) {
            console.error('Photo delete failed:', error);
            enqueueSnackbar('Failed to delete photo', { variant: 'error' });
        }
    };

    // Save GRN
    const handleSave = async (finalize = false) => {
        if (!grnId) return;

        //   // Note: Photos should be uploaded via their component interaction (instant upload expected per snippet)
        //   // If we simply stored files in `items` state, we would upload here.
        //   // But given the snippet structure, assume photos are already uploaded?
        //   // Wait, if I use the "remount key" trick, then files argument in handlePhotoUpload is correct (only new batch).

        try {
            const updateData: GRNUpdateRequest = {
                transport_method: transportMethod,
                number_of_boxes: boxes,
                receiving_time: receivingTime?.toTimeString().slice(0, 8),
                // Use local date string instead of UTC
                receiving_date: receivingDate ? format(receivingDate, 'yyyy-MM-dd') : undefined,
                receiver_id: receiverId || undefined,
                items: items.map(item => ({
                    item_id: item.item_id,
                    gross_received: item.gross_received,
                    damage: item.damage,
                    reject: item.reject,
                    damage_cost_allocation: item.damage_cost_allocation,
                    reject_cost_allocation: item.reject_cost_allocation,
                    notes: item.notes
                }))
            };

            await grnAPI.update(parseInt(grnId), updateData);

            if (finalize) {
                await grnAPI.finalize(parseInt(grnId));
                enqueueSnackbar('GRN Finalized', { variant: 'success' });
                navigate(`/inward/grn/${grnId}`);
            } else {
                enqueueSnackbar('GRN Saved', { variant: 'success' });
            }
        } catch (error) {
            console.error('Save failed:', error);
            enqueueSnackbar('Save failed: ' + (error as any).response?.data?.detail || 'Unknown error', { variant: 'error' });
        }
    };

    const onFinalizeClick = async () => {
        // Validation
        for (const item of items) {
            // Validate photos
            if (item.damage > 0) {
                const damagePhotos = grn?.photos?.filter(
                    p => p.item_id === item.item_id && p.photo_type === 'damage'
                );
                if (!damagePhotos || damagePhotos.length === 0) {
                    alert(`Please upload photos for damage on ${item.item_name}`);
                    return;
                }
                if (!item.damage_cost_allocation) {
                    alert(`Please set cost allocation for damage on ${item.item_name}`);
                    return;
                }
            }

            if (item.reject > 0) {
                const rejectPhotos = grn?.photos?.filter(
                    p => p.item_id === item.item_id && p.photo_type === 'reject'
                );
                if (!rejectPhotos || rejectPhotos.length === 0) {
                    alert(`Please upload photos for reject on ${item.item_name}`);
                    return;
                }
                if (!item.reject_cost_allocation) {
                    alert(`Please set cost allocation for reject on ${item.item_name}`);
                    return;
                }
            }
        }

        if (!receiverId) {
            alert('Please select who received the goods');
            return;
        }

        await handleSave(true);
    };

    if (loading || !grn) {
        return <Box sx={{ p: 5, textAlign: 'center' }}><CircularProgress /></Box>;
    }

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>GRN Data Entry - {grn.grn_number}</Typography>

            <Alert severity="info" sx={{ mb: 3 }}>
                <strong>Batch Number:</strong> {grn.batch_number} |
                <strong> PO:</strong> {grn.po_number} |
                <strong> Vendor:</strong> {grn.vendor_name}
            </Alert>

            <Card sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>Transport Details</Typography>

                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr 1fr' }, gap: 2, mb: 3 }}>
                    <FormControl fullWidth>
                        <InputLabel>Transport Method</InputLabel>
                        <Select
                            label="Transport Method"
                            value={transportMethod}
                            onChange={(e) => setTransportMethod(e.target.value)}
                        >
                            <MenuItem value="Truck">Truck</MenuItem>
                            <MenuItem value="Tempo">Tempo</MenuItem>
                            <MenuItem value="Farm Vehicle">Farm Vehicle</MenuItem>
                            <MenuItem value="Other">Other</MenuItem>
                        </Select>
                    </FormControl>

                    <TextField
                        label="Number of Boxes"
                        type="number"
                        value={boxes}
                        onChange={(e) => setBoxes(parseInt(e.target.value))}
                        fullWidth
                    />

                    <TimePicker
                        label="Receiving Time"
                        value={receivingTime}
                        onChange={setReceivingTime}
                        slotProps={{ textField: { fullWidth: true } }}
                    />
                    <DatePicker
                        label="Receiving Date"
                        value={receivingDate}
                        onChange={setReceivingDate}
                        slotProps={{ textField: { fullWidth: true } }}
                    />
                </Box>

                <FormControl fullWidth>
                    <InputLabel>Who Received?</InputLabel>
                    <Select
                        label="Who Received?"
                        value={receiverId || ''}
                        onChange={(e) => setReceiverId(e.target.value as number)}
                    >
                        {users.map(user => (
                            <MenuItem key={user.id} value={user.id}>{user.name}</MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </Card>

            <Card sx={{ p: 3, mb: 3, overflowX: 'auto' }}>
                <Typography variant="h6" gutterBottom>Items Received</Typography>

                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Item</TableCell>
                            <TableCell>Expected</TableCell>
                            <TableCell>Gross Received</TableCell>
                            <TableCell>Damage</TableCell>
                            <TableCell>Reject</TableCell>
                            <TableCell>Final Accepted</TableCell>
                            <TableCell>Photos</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {items.map((item: ItemRow, index) => (
                            <React.Fragment key={item.item_id}>
                                <TableRow>
                                    <TableCell>{item.item_name}</TableCell>
                                    <TableCell>{item.expected_quantity}</TableCell>
                                    <TableCell>
                                        <TextField
                                            type="number"
                                            size="small"
                                            value={item.gross_received}
                                            onChange={(e) => handleItemChange(index, 'gross_received', parseFloat(e.target.value))}
                                            inputProps={{ min: 0, step: 0.01 }}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <TextField
                                            type="number"
                                            size="small"
                                            value={item.damage}
                                            onChange={(e) => handleItemChange(index, 'damage', parseFloat(e.target.value))}
                                            inputProps={{ min: 0, step: 0.01 }}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <TextField
                                            type="number"
                                            size="small"
                                            value={item.reject}
                                            onChange={(e) => handleItemChange(index, 'reject', parseFloat(e.target.value))}
                                            inputProps={{ min: 0, step: 0.01 }}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <Chip
                                            label={item.final_accepted.toFixed(2)}
                                            color={item.final_accepted < item.expected_quantity ? 'warning' : 'success'}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        {(item.damage > 0) && (
                                            <PhotoUpload
                                                key={`damage-${item.item_id}-${grn.photos.length}`} // Force reset on new photos
                                                label="Damage Photos"
                                                onUpload={(files) => handlePhotoUpload(item.item_id, 'damage', files)}
                                                existingPhotos={grn.photos.filter(
                                                    p => p.item_id === item.item_id && p.photo_type === 'damage'
                                                )}
                                                required={true}
                                                onDelete={handleDeletePhoto}
                                            />
                                        )}
                                        {(item.reject > 0) && (
                                            <PhotoUpload
                                                key={`reject-${item.item_id}-${grn.photos.length}`} // Force reset on new photos
                                                label="Reject Photos"
                                                onUpload={(files) => handlePhotoUpload(item.item_id, 'reject', files)}
                                                existingPhotos={grn.photos.filter(
                                                    p => p.item_id === item.item_id && p.photo_type === 'reject'
                                                )}
                                                required={true}
                                                onDelete={handleDeletePhoto}
                                            />
                                        )}
                                    </TableCell>
                                </TableRow>

                                {/* Cost Allocation Row */}
                                {(item.damage > 0 || item.reject > 0) && (
                                    <TableRow>
                                        <TableCell colSpan={7} sx={{ bgcolor: '#f5f5f5' }}>
                                            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', pl: 2 }}>
                                                {item.damage > 0 && (
                                                    <CostAllocationToggle
                                                        label="Damage Cost:"
                                                        value={item.damage_cost_allocation}
                                                        onChange={(val) => handleItemChange(index, 'damage_cost_allocation', val)}
                                                    />
                                                )}
                                                {item.reject > 0 && (
                                                    <CostAllocationToggle
                                                        label="Reject Cost:"
                                                        value={item.reject_cost_allocation}
                                                        onChange={(val) => handleItemChange(index, 'reject_cost_allocation', val)}
                                                    />
                                                )}
                                            </Box>
                                        </TableCell>
                                    </TableRow>
                                )}
                            </React.Fragment>
                        ))}
                    </TableBody>
                </Table>
            </Card>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button variant="outlined" onClick={() => navigate('/inward/grn')}>
                    Cancel
                </Button>
                <Button variant="outlined" onClick={() => handleSave(false)}>
                    Save Draft
                </Button>
                <Button variant="contained" onClick={onFinalizeClick}>
                    Finalize GRN
                </Button>
            </Box>
        </Box>
    );
};

export default GRNDataEntryForm;
