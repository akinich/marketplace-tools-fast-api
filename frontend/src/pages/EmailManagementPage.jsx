import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Tabs,
  Tab,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Alert
} from '@mui/material';
import { Send as SendIcon, Email as EmailIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { emailAPI } from '../api/email';

function EmailManagementPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [currentTab, setCurrentTab] = useState(0);
  const [loading, setLoading] = useState(false);

  // Test dialog
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [testing, setTesting] = useState(false);

  // Email queue
  const [emailQueue, setEmailQueue] = useState([]);

  // Recipients
  const [recipients, setRecipients] = useState([]);
  const [editingRecipient, setEditingRecipient] = useState(null);

  useEffect(() => {
    if (currentTab === 0) loadQueue();
    if (currentTab === 1) loadRecipients();
  }, [currentTab]);

  const loadQueue = async () => {
    try {
      setLoading(true);
      const data = await emailAPI.getQueue();
      setEmailQueue(data);
      setLoading(false);
    } catch (error) {
      enqueueSnackbar('Failed to load email queue', { variant: 'error' });
      setLoading(false);
    }
  };

  const loadRecipients = async () => {
    try {
      setLoading(true);
      const data = await emailAPI.getRecipients();
      setRecipients(data);
      setLoading(false);
    } catch (error) {
      enqueueSnackbar('Failed to load recipients', { variant: 'error' });
      setLoading(false);
    }
  };

  const handleTestSMTP = async () => {
    try {
      setTesting(true);
      await emailAPI.testSMTP(testEmail);
      enqueueSnackbar(`Test email sent to ${testEmail}`, { variant: 'success' });
      setTestDialogOpen(false);
      setTestEmail('');
      setTesting(false);
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Test email failed', { variant: 'error' });
      setTesting(false);
    }
  };

  const handleUpdateRecipients = async (notificationType, emails) => {
    try {
      await emailAPI.updateRecipients(notificationType, {
        notification_type: notificationType,
        recipient_emails: emails.split(',').map(e => e.trim()).filter(e => e),
        is_active: true
      });
      enqueueSnackbar('Recipients updated', { variant: 'success' });
      loadRecipients();
      setEditingRecipient(null);
    } catch (error) {
      enqueueSnackbar('Failed to update recipients', { variant: 'error' });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'sent': return 'success';
      case 'failed': return 'error';
      case 'pending': return 'warning';
      case 'sending': return 'info';
      default: return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4">Email Management</Typography>
          <Button
            variant="contained"
            startIcon={<SendIcon />}
            onClick={() => setTestDialogOpen(true)}
          >
            Test SMTP
          </Button>
        </Box>

        <Tabs value={currentTab} onChange={(e, v) => setCurrentTab(v)} sx={{ mb: 3 }}>
          <Tab label="Email Queue" />
          <Tab label="Recipients" />
          <Tab label="Templates" />
        </Tabs>

        {/* Email Queue Tab */}
        {currentTab === 0 && (
          <Box>
            <Typography variant="h6" gutterBottom>Recent Emails</Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>To</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Attempts</TableCell>
                  <TableCell>Created</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {emailQueue.map(email => (
                  <TableRow key={email.id}>
                    <TableCell>{email.to_email}</TableCell>
                    <TableCell>{email.subject}</TableCell>
                    <TableCell>
                      <Chip
                        label={email.status}
                        color={getStatusColor(email.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{email.attempts} / {email.max_attempts}</TableCell>
                    <TableCell>{new Date(email.created_at).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        )}

        {/* Recipients Tab */}
        {currentTab === 1 && (
          <Box>
            <Typography variant="h6" gutterBottom>Notification Recipients</Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Enter comma-separated email addresses for each notification type
            </Alert>
            <Grid container spacing={3}>
              {recipients.map(recipient => (
                <Grid item xs={12} key={recipient.notification_type}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      {recipient.notification_type.replace(/_/g, ' ').toUpperCase()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {recipient.description}
                    </Typography>
                    <TextField
                      fullWidth
                      size="small"
                      label="Email addresses (comma-separated)"
                      defaultValue={recipient.recipient_emails.join(', ')}
                      onBlur={(e) => handleUpdateRecipients(recipient.notification_type, e.target.value)}
                      placeholder="email1@example.com, email2@example.com"
                    />
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {/* Templates Tab */}
        {currentTab === 2 && (
          <Box>
            <Typography variant="h6" gutterBottom>Email Templates</Typography>
            <Alert severity="info">
              Email templates are managed in the database. Contact your administrator to modify templates.
            </Alert>
          </Box>
        )}
      </Paper>

      {/* Test SMTP Dialog */}
      <Dialog open={testDialogOpen} onClose={() => setTestDialogOpen(false)}>
        <DialogTitle>Test SMTP Configuration</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Test Email Address"
            type="email"
            value={testEmail}
            onChange={(e) => setTestEmail(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleTestSMTP}
            disabled={!testEmail || testing}
            variant="contained"
          >
            {testing ? 'Sending...' : 'Send Test Email'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default EmailManagementPage;
