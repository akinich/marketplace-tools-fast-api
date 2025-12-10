/**
 * ============================================================================
 * Marketplace ERP - Ticket Detail Page  
 * ============================================================================
 * Version: 1.0.0
 * Last Updated: 2025-12-10
 *
 * Description:
 *   Unified ticket detail/edit page for all ticket categories (Internal, B2B, B2C).
 *   Displays ticket information, comments, and admin controls.
 *   Based on original farm2-app-fast-api pattern.
 * ============================================================================
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Box,
    Typography,
    Button,
    Card,
    CardContent,
    Grid,
    TextField,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Chip,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    CircularProgress,
    Alert,
    Divider,
    List,
    ListItem,
    ListItemText,
    ListItemAvatar,
    Avatar,
} from '@mui/material';
import {
    ArrowBack as BackIcon,
    Delete as DeleteIcon,
    Close as CloseIcon,
    Send as SendIcon,
    Edit as EditIcon,
    BugReport as BugIcon,
    Lightbulb as FeatureIcon,
    TrendingUp as UpgradeIcon,
    MoreHoriz as OthersIcon,
    Build as QualityIcon,
    LocalShipping as DeliveryIcon,
    ShoppingCart as OrderIcon,
    AssignmentReturn as ReturnIcon,
    Comment as CommentIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import useAuthStore from '../store/authStore';
import { ticketsAPI } from '../api';

// ============================================================================
// TYPES
// ============================================================================

interface TicketDetail {
    id: number;
    title: string;
    description: string;
    ticket_type: string;
    ticket_category: string;
    status: string;
    priority: string | null;
    created_by_id: string;
    created_by_name: string;
    created_by_email: string;
    created_at: string;
    updated_at: string;
    closed_by_id: string | null;
    closed_by_name: string | null;
    closed_at: string | null;
    // B2B/B2C specific fields
    customer_name?: string;
    customer_email?: string;
    customer_phone?: string;
    woocommerce_order_id?: string;
    sales_order_id?: string;
    invoice_id?: string;
    batch_number?: string;
    delivery_date?: string;
    photo_urls?: string[];
    comments: Comment[];
}

interface Comment {
    id: number;
    ticket_id: number;
    user_id: string;
    user_name: string;
    user_email: string;
    comment: string;
    created_at: string;
    updated_at: string;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const TICKET_TYPES: Record<string, { label: string; icon: JSX.Element; color: 'error' | 'info' | 'success' | 'warning' | 'default' }> = {
    issue: { label: 'Issue', icon: <BugIcon />, color: 'error' },
    feature_request: { label: 'Feature Request', icon: <FeatureIcon />, color: 'info' },
    upgrade: { label: 'Upgrade', icon: <UpgradeIcon />, color: 'success' },
    others: { label: 'Others', icon: <OthersIcon />, color: 'default' },
    quality_issue: { label: 'Quality Issue', icon: <QualityIcon />, color: 'error' },
    delivery_issue: { label: 'Delivery Issue', icon: <DeliveryIcon />, color: 'warning' },
    order_issue: { label: 'Order Issue', icon: <OrderIcon />, color: 'warning' },
    return_request: { label: 'Return Request', icon: <ReturnIcon />, color: 'info' },
    general: { label: 'General', icon: <CommentIcon />, color: 'default' },
};

const STATUS_CONFIG: Record<string, { label: string; color: 'info' | 'warning' | 'success' | 'default' }> = {
    open: { label: 'Open', color: 'info' },
    in_progress: { label: 'In Progress', color: 'warning' },
    resolved: { label: 'Resolved', color: 'success' },
    closed: { label: 'Closed', color: 'default' },
};

const PRIORITY_CONFIG: Record<string, { label: string; color: 'success' | 'info' | 'warning' | 'error' }> = {
    low: { label: 'Low', color: 'success' },
    medium: { label: 'Medium', color: 'info' },
    high: { label: 'High', color: 'warning' },
    critical: { label: 'Critical', color: 'error' },
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

const formatDate = (dateString: string | null): string => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
};

const getInitials = (name: string): string => {
    return name
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function TicketDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { enqueueSnackbar } = useSnackbar();
    const user = useAuthStore((state) => state.user);
    const isAdmin = user?.role === 'Admin';

    // State
    const [ticket, setTicket] = useState<TicketDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [newComment, setNewComment] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [editingCommentId, setEditingCommentId] = useState<number | null>(null);
    const [editCommentText, setEditCommentText] = useState('');

    // Dialog states
    const [adminDialogOpen, setAdminDialogOpen] = useState(false);
    const [closeDialogOpen, setCloseDialogOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [deleteCommentId, setDeleteCommentId] = useState<number | null>(null);

    // Admin update state
    const [adminUpdate, setAdminUpdate] = useState({
        status: '',
        priority: '',
    });
    const [closeComment, setCloseComment] = useState('');

    // Fetch ticket
    const fetchTicket = async () => {
        if (!id) return;

        setLoading(true);
        try {
            const data = await ticketsAPI.getTicket(parseInt(id));
            setTicket(data);
            setAdminUpdate({
                status: data.status || '',
                priority: data.priority || '',
            });
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to fetch ticket', { variant: 'error' });
            navigate('/tickets/dashboard');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTicket();
    }, [id]);

    // Add comment
    const handleAddComment = async () => {
        if (!newComment.trim() || !id) return;

        setSubmitting(true);
        try {
            await ticketsAPI.addComment(parseInt(id), { comment: newComment });
            setNewComment('');
            await fetchTicket();
            enqueueSnackbar('Comment added', { variant: 'success' });
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to add comment', { variant: 'error' });
        } finally {
            setSubmitting(false);
        }
    };

    // Edit comment
    const handleEditComment = async (commentId: number) => {
        if (!editCommentText.trim()) return;

        try {
            await ticketsAPI.updateComment(commentId, { comment: editCommentText });
            setEditingCommentId(null);
            setEditCommentText('');
            await fetchTicket();
            enqueueSnackbar('Comment updated', { variant: 'success' });
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to update comment', { variant: 'error' });
        }
    };

    // Delete comment
    const handleDeleteComment = async (commentId: number) => {
        try {
            await ticketsAPI.deleteComment(commentId);
            setDeleteCommentId(null);
            await fetchTicket();
            enqueueSnackbar('Comment deleted', { variant: 'success' });
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to delete comment', { variant: 'error' });
        }
    };

    // Admin update ticket
    const handleAdminUpdate = async () => {
        if (!id) return;

        try {
            const updateData: any = {};
            if (adminUpdate.status) updateData.status = adminUpdate.status;
            if (adminUpdate.priority) updateData.priority = adminUpdate.priority;

            await ticketsAPI.adminUpdateTicket(parseInt(id), updateData);
            setAdminDialogOpen(false);
            await fetchTicket();
            enqueueSnackbar('Ticket updated', { variant: 'success' });
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to update ticket', { variant: 'error' });
        }
    };

    // Close ticket
    const handleCloseTicket = async () => {
        if (!id) return;

        try {
            await ticketsAPI.closeTicket(parseInt(id), closeComment || null);
            setCloseDialogOpen(false);
            setCloseComment('');
            await fetchTicket();
            enqueueSnackbar('Ticket closed', { variant: 'success' });
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to close ticket', { variant: 'error' });
        }
    };

    // Delete ticket
    const handleDeleteTicket = async () => {
        if (!id) return;

        try {
            await ticketsAPI.deleteTicket(parseInt(id));
            setDeleteDialogOpen(false);
            enqueueSnackbar('Ticket deleted successfully', { variant: 'success' });

            // Navigate back to appropriate page
            const category = ticket?.ticket_category || 'internal';
            navigate(`/tickets/${category}`);
        } catch (error: any) {
            enqueueSnackbar(error.response?.data?.detail || 'Failed to delete ticket', { variant: 'error' });
        }
    };

    // Navigate back
    const handleBack = () => {
        const category = ticket?.ticket_category || 'internal';
        navigate(`/tickets/${category}`);
    };

    // Loading state
    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    // Ticket not found
    if (!ticket) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">Ticket not found</Alert>
            </Box>
        );
    }

    // Configs
    const typeConfig = TICKET_TYPES[ticket.ticket_type] || TICKET_TYPES.others;
    const statusConfig = STATUS_CONFIG[ticket.status] || STATUS_CONFIG.open;
    const priorityConfig = ticket.priority ? PRIORITY_CONFIG[ticket.priority] : null;
    const isClosed = ticket.status === 'closed';
    const isCreator = ticket.created_by_id === user?.id;

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
                <Box>
                    <Typography variant="h5" gutterBottom>
                        #{ticket.id} - {ticket.title}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Chip
                            icon={typeConfig.icon}
                            label={typeConfig.label}
                            color={typeConfig.color}
                            variant="outlined"
                            size="small"
                        />
                        <Chip
                            label={statusConfig.label}
                            color={statusConfig.color}
                            size="small"
                        />
                        {priorityConfig && (
                            <Chip
                                label={priorityConfig.label}
                                color={priorityConfig.color}
                                variant="outlined"
                                size="small"
                            />
                        )}
                        <Chip
                            label={ticket.ticket_category.toUpperCase()}
                            size="small"
                            variant="outlined"
                        />
                    </Box>
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                        variant="outlined"
                        startIcon={<BackIcon />}
                        onClick={handleBack}
                    >
                        Back
                    </Button>
                    {(isAdmin || isCreator) && (
                        <Button
                            variant="outlined"
                            color="error"
                            startIcon={<DeleteIcon />}
                            onClick={() => setDeleteDialogOpen(true)}
                        >
                            Delete
                        </Button>
                    )}
                    {isAdmin && !isClosed && (
                        <>
                            <Button
                                variant="outlined"
                                onClick={() => setAdminDialogOpen(true)}
                            >
                                Update
                            </Button>
                            <Button
                                variant="contained"
                                color="error"
                                startIcon={<CloseIcon />}
                                onClick={() => setCloseDialogOpen(true)}
                            >
                                Close Ticket
                            </Button>
                        </>
                    )}
                </Box>
            </Box>

            <Grid container spacing={3}>
                {/* Left: Ticket Details */}
                <Grid item xs={12} md={7}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>Description</Typography>
                            <Typography variant="body1" paragraph sx={{ whiteSpace: 'pre-wrap' }}>
                                {ticket.description}
                            </Typography>

                            <Divider sx={{ my: 2 }} />

                            <Grid container spacing={2}>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Created By</Typography>
                                    <Typography variant="body1">{ticket.created_by_name}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Created At</Typography>
                                    <Typography variant="body1">{formatDate(ticket.created_at)}</Typography>
                                </Grid>
                                <Grid item xs={6}>
                                    <Typography variant="body2" color="text.secondary">Updated At</Typography>
                                    <Typography variant="body1">{formatDate(ticket.updated_at)}</Typography>
                                </Grid>
                                {ticket.closed_at && (
                                    <>
                                        <Grid item xs={6}>
                                            <Typography variant="body2" color="text.secondary">Closed At</Typography>
                                            <Typography variant="body1">{formatDate(ticket.closed_at)}</Typography>
                                        </Grid>
                                        <Grid item xs={6}>
                                            <Typography variant="body2" color="text.secondary">Closed By</Typography>
                                            <Typography variant="body1">{ticket.closed_by_name || '-'}</Typography>
                                        </Grid>
                                    </>
                                )}
                            </Grid>

                            {/* Category-specific fields */}
                            {(ticket.ticket_category === 'b2b' || ticket.ticket_category === 'b2c') && (
                                <>
                                    <Divider sx={{ my: 2 }} />
                                    <Typography variant="h6" gutterBottom>Customer Information</Typography>
                                    <Grid container spacing={2}>
                                        {ticket.customer_name && (
                                            <Grid item xs={6}>
                                                <Typography variant="body2" color="text.secondary">Customer Name</Typography>
                                                <Typography variant="body1">{ticket.customer_name}</Typography>
                                            </Grid>
                                        )}
                                        {ticket.customer_email && (
                                            <Grid item xs={6}>
                                                <Typography variant="body2" color="text.secondary">Email</Typography>
                                                <Typography variant="body1">{ticket.customer_email}</Typography>
                                            </Grid>
                                        )}
                                        {ticket.customer_phone && (
                                            <Grid item xs={6}>
                                                <Typography variant="body2" color="text.secondary">Phone</Typography>
                                                <Typography variant="body1">{ticket.customer_phone}</Typography>
                                            </Grid>
                                        )}
                                        {ticket.woocommerce_order_id && (
                                            <Grid item xs={6}>
                                                <Typography variant="body2" color="text.secondary">WooCommerce Order</Typography>
                                                <Typography variant="body1">{ticket.woocommerce_order_id}</Typography>
                                            </Grid>
                                        )}
                                        {ticket.sales_order_id && (
                                            <Grid item xs={6}>
                                                <Typography variant="body2" color="text.secondary">Sales Order</Typography>
                                                <Typography variant="body1">{ticket.sales_order_id}</Typography>
                                            </Grid>
                                        )}
                                        {ticket.invoice_id && (
                                            <Grid item xs={6}>
                                                <Typography variant="body2" color="text.secondary">Invoice</Typography>
                                                <Typography variant="body1">{ticket.invoice_id}</Typography>
                                            </Grid>
                                        )}
                                        {ticket.batch_number && (
                                            <Grid item xs={6}>
                                                <Typography variant="body2" color="text.secondary">Batch Number</Typography>
                                                <Typography variant="body1">{ticket.batch_number}</Typography>
                                            </Grid>
                                        )}
                                        {ticket.delivery_date && (
                                            <Grid item xs={6}>
                                                <Typography variant="body2" color="text.secondary">Delivery Date</Typography>
                                                <Typography variant="body1">{ticket.delivery_date}</Typography>
                                            </Grid>
                                        )}
                                    </Grid>
                                </>
                            )}
                        </CardContent>
                    </Card>
                </Grid>

                {/* Right: Comments */}
                <Grid item xs={12} md={5}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Comments ({ticket.comments?.length || 0})
                            </Typography>

                            {/* Comments List */}
                            {ticket.comments && ticket.comments.length > 0 ? (
                                <List sx={{ maxHeight: 400, overflow: 'auto', mb: 2 }}>
                                    {ticket.comments.map((comment) => (
                                        <ListItem key={comment.id} alignItems="flex-start" sx={{ px: 0 }}>
                                            <ListItemAvatar>
                                                <Avatar>{getInitials(comment.user_name)}</Avatar>
                                            </ListItemAvatar>
                                            <ListItemText
                                                primary={
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                        <Typography variant="subtitle2">{comment.user_name}</Typography>
                                                        <Typography variant="caption" color="text.secondary">
                                                            {formatDate(comment.created_at)}
                                                        </Typography>
                                                    </Box>
                                                }
                                                secondary={
                                                    editingCommentId === comment.id ? (
                                                        <Box sx={{ mt: 1 }}>
                                                            <TextField
                                                                fullWidth
                                                                multiline
                                                                rows={2}
                                                                size="small"
                                                                value={editCommentText}
                                                                onChange={(e) => setEditCommentText(e.target.value)}
                                                            />
                                                            <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                                                                <Button size="small" onClick={() => handleEditComment(comment.id)}>
                                                                    Save
                                                                </Button>
                                                                <Button
                                                                    size="small"
                                                                    onClick={() => {
                                                                        setEditingCommentId(null);
                                                                        setEditCommentText('');
                                                                    }}
                                                                >
                                                                    Cancel
                                                                </Button>
                                                            </Box>
                                                        </Box>
                                                    ) : (
                                                        <Box>
                                                            <Typography variant="body2" sx={{ mt: 0.5, whiteSpace: 'pre-wrap' }}>
                                                                {comment.comment}
                                                            </Typography>
                                                            {(isAdmin || comment.user_id === user?.id) && (
                                                                <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                                                                    <Button
                                                                        size="small"
                                                                        startIcon={<EditIcon />}
                                                                        onClick={() => {
                                                                            setEditingCommentId(comment.id);
                                                                            setEditCommentText(comment.comment);
                                                                        }}
                                                                    >
                                                                        Edit
                                                                    </Button>
                                                                    <Button
                                                                        size="small"
                                                                        color="error"
                                                                        startIcon={<DeleteIcon />}
                                                                        onClick={() => setDeleteCommentId(comment.id)}
                                                                    >
                                                                        Delete
                                                                    </Button>
                                                                </Box>
                                                            )}
                                                        </Box>
                                                    )
                                                }
                                            />
                                        </ListItem>
                                    ))}
                                </List>
                            ) : (
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    No comments yet
                                </Typography>
                            )}

                            {/* Add Comment Form */}
                            {!isClosed && (
                                <>
                                    <Divider sx={{ my: 2 }} />
                                    <TextField
                                        fullWidth
                                        multiline
                                        rows={3}
                                        placeholder="Add a comment..."
                                        value={newComment}
                                        onChange={(e) => setNewComment(e.target.value)}
                                        disabled={submitting}
                                    />
                                    <Button
                                        fullWidth
                                        variant="contained"
                                        startIcon={<SendIcon />}
                                        onClick={handleAddComment}
                                        disabled={submitting || !newComment.trim()}
                                        sx={{ mt: 1 }}
                                    >
                                        {submitting ? 'Sending...' : 'Send Comment'}
                                    </Button>
                                </>
                            )}
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Admin Update Dialog */}
            <Dialog open={adminDialogOpen} onClose={() => setAdminDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Update Ticket</DialogTitle>
                <DialogContent>
                    <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <FormControl fullWidth>
                            <InputLabel>Status</InputLabel>
                            <Select
                                value={adminUpdate.status}
                                label="Status"
                                onChange={(e) => setAdminUpdate({ ...adminUpdate, status: e.target.value })}
                            >
                                <MenuItem value="open">Open</MenuItem>
                                <MenuItem value="in_progress">In Progress</MenuItem>
                                <MenuItem value="resolved">Resolved</MenuItem>
                            </Select>
                        </FormControl>
                        <FormControl fullWidth>
                            <InputLabel>Priority</InputLabel>
                            <Select
                                value={adminUpdate.priority}
                                label="Priority"
                                onChange={(e) => setAdminUpdate({ ...adminUpdate, priority: e.target.value })}
                            >
                                <MenuItem value="">Not Set</MenuItem>
                                <MenuItem value="low">Low</MenuItem>
                                <MenuItem value="medium">Medium</MenuItem>
                                <MenuItem value="high">High</MenuItem>
                                <MenuItem value="critical">Critical</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setAdminDialogOpen(false)}>Cancel</Button>
                    <Button variant="contained" onClick={handleAdminUpdate}>Update</Button>
                </DialogActions>
            </Dialog>

            {/* Close Ticket Dialog */}
            <Dialog open={closeDialogOpen} onClose={() => setCloseDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Close Ticket</DialogTitle>
                <DialogContent>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Are you sure you want to close this ticket? You can optionally add a closing comment.
                    </Typography>
                    <TextField
                        fullWidth
                        multiline
                        rows={3}
                        label="Closing Comment (Optional)"
                        value={closeComment}
                        onChange={(e) => setCloseComment(e.target.value)}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCloseDialogOpen(false)}>Cancel</Button>
                    <Button variant="contained" color="error" onClick={handleCloseTicket}>
                        Close Ticket
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Delete Ticket Dialog */}
            <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
                <DialogTitle>Delete Ticket</DialogTitle>
                <DialogContent>
                    <Alert severity="warning" sx={{ mb: 2 }}>
                        This action cannot be undone!
                    </Alert>
                    <Typography variant="body2" color="text.secondary">
                        Are you sure you want to delete this ticket? All associated comments will also be deleted.
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
                    <Button variant="contained" color="error" onClick={handleDeleteTicket}>
                        Delete Ticket
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Delete Comment Dialog */}
            <Dialog open={deleteCommentId !== null} onClose={() => setDeleteCommentId(null)}>
                <DialogTitle>Delete Comment</DialogTitle>
                <DialogContent>
                    <Typography variant="body2" color="text.secondary">
                        Are you sure you want to delete this comment?
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteCommentId(null)}>Cancel</Button>
                    <Button
                        variant="contained"
                        color="error"
                        onClick={() => deleteCommentId && handleDeleteComment(deleteCommentId)}
                    >
                        Delete
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}
"
