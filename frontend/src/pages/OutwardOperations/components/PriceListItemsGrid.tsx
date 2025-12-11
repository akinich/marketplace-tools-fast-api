import { useState, useEffect } from 'react';
import {
    Box,
    CircularProgress,
    IconButton,
} from '@mui/material';
import { DataGrid, GridColDef, GridRowModes, GridRowModesModel } from '@mui/x-data-grid';
import { Delete as DeleteIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import priceListAPI, { PriceListItem } from '../../../api/priceList';

interface PriceListItemsGridProps {
    priceListId: number;
    isAdmin: boolean;
}

function PriceListItemsGrid({ priceListId, isAdmin }: PriceListItemsGridProps) {
    const { enqueueSnackbar } = useSnackbar();
    const [loading, setLoading] = useState(true);
    const [items, setItems] = useState<PriceListItem[]>([]);
    const [rowModesModel, setRowModesModel] = useState<GridRowModesModel>({});

    const fetchItems = async () => {
        setLoading(true);
        try {
            const response = await priceListAPI.getItems(priceListId);
            setItems(response.items);
        } catch (error: any) {
            enqueueSnackbar('Failed to load items', { variant: 'error' });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchItems();
    }, [priceListId]);

    const handleDelete = async (id: number, itemId: number) => {
        if (!confirm('Delete this item from the price list?')) return;

        try {
            await priceListAPI.deleteItem(priceListId, itemId);
            setItems(items.filter(item => item.id !== id));
            enqueueSnackbar('Item removed', { variant: 'success' });
        } catch (error: any) {
            enqueueSnackbar('Failed to remove item', { variant: 'error' });
        }
    };

    const handleRowEditStop = (params: any) => {
        setRowModesModel({ ...rowModesModel, [params.id]: { mode: GridRowModes.View } });
    };

    const processRowUpdate = async (newRow: PriceListItem) => {
        try {
            await priceListAPI.addOrUpdateItem(priceListId, {
                item_id: newRow.item_id,
                price: newRow.price,
                notes: newRow.notes || undefined,
            });
            enqueueSnackbar('Price updated', { variant: 'success' });
            return newRow;
        } catch (error: any) {
            enqueueSnackbar('Failed to update price', { variant: 'error' });
            throw error;
        }
    };

    const columns: GridColDef[] = [
        { field: 'item_sku', headerName: 'SKU', width: 150 },
        { field: 'item_name', headerName: 'Item Name', width: 300 },
        {
            field: 'price',
            headerName: '💰 Price (INR)',
            width: 150,
            type: 'number',
            editable: isAdmin,
            headerClassName: isAdmin ? 'editable-column-header' : '',
        },
        {
            field: 'notes',
            headerName: '📝 Notes',
            width: 200,
            editable: isAdmin,
            headerClassName: isAdmin ? 'editable-column-header' : '',
        },
        {
            field: 'actions',
            headerName: 'Actions',
            width: 100,
            sortable: false,
            renderCell: (params) =>
                isAdmin ? (
                    <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(params.row.id, params.row.item_id)}
                    >
                        <DeleteIcon fontSize="small" />
                    </IconButton>
                ) : null,
        },
    ];

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box>
            <Box sx={{ mb: 2 }}>
                {items.length} item{items.length !== 1 ? 's' : ''} in price list
            </Box>
            <Box sx={{ height: 500, width: '100%' }}>
                <DataGrid
                    rows={items}
                    columns={columns}
                    editMode="row"
                    rowModesModel={rowModesModel}
                    onRowEditStop={handleRowEditStop}
                    processRowUpdate={processRowUpdate}
                    pageSizeOptions={[25, 50, 100]}
                    initialState={{
                        pagination: { paginationModel: { pageSize: 25 } },
                    }}
                    sx={{
                        '& .editable-column-header': {
                            backgroundColor: '#e3f2fd',
                            fontWeight: 'bold',
                        },
                    }}
                />
            </Box>
        </Box>
    );
}

export default PriceListItemsGrid;
