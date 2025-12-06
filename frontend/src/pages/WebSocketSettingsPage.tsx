/**
 * WebSocket Settings Page
 * Version: 1.0.0
 * Last Updated: 2025-11-23
 *
 * Changelog:
 * ----------
 * v1.0.0 (2025-11-23):
 *   - Initial WebSocket settings page
 *   - Real-time connection status indicator
 *   - List of WebSocket-enabled features
 *   - Information about automatic connection
 *   - Styled with Material-UI components matching system design
 *
 * Description:
 *   Settings page for WebSocket/Real-time notifications. Displays connection
 *   status and information about real-time features. WebSocket connection is
 *   established automatically on login.
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Chip,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Card,
  CardContent,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Dashboard as DashboardIcon,
  ConfirmationNumber as TicketIcon,

  People as PeopleIcon,
  SignalCellularAlt as SignalIcon,
} from '@mui/icons-material';

function WebSocketSettingsPage() {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('checking');

  useEffect(() => {
    // Check WebSocket connection status
    const checkConnection = async () => {
      try {
        // Try to import websocket service
        const module = await import('../services/websocket').catch(() => null);

        if (module && module.default) {
          const ws = module.default;
          const connected = ws.ws && ws.ws.readyState === WebSocket.OPEN;
          setIsConnected(connected);
          setConnectionStatus(connected ? 'connected' : 'disconnected');
        } else {
          setIsConnected(false);
          setConnectionStatus('not_configured');
        }
      } catch (error) {
        console.error('Error checking WebSocket status:', error);
        setIsConnected(false);
        setConnectionStatus('error');
      }
    };

    checkConnection();

    // Check connection status every 5 seconds
    const interval = setInterval(checkConnection, 5000);

    return () => clearInterval(interval);
  }, []);

  const realTimeFeatures = [
    {
      icon: <DashboardIcon />,
      title: 'Dashboard Statistics',
      description: 'Live updates for farm metrics and system health',
    },
    {
      icon: <TicketIcon />,
      title: 'Ticket Notifications',
      description: 'Instant alerts when new tickets are created or updated',
    },
    {
      icon: <NotificationsIcon />,
      title: 'Low Stock Alerts',
      description: 'Real-time notifications for system alerts',
    },
    {
      icon: <PeopleIcon />,
      title: 'User Presence',
      description: 'See which team members are currently online',
    },
  ];

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'success';
      case 'disconnected':
        return 'warning';
      case 'not_configured':
        return 'default';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'disconnected':
        return 'Disconnected';
      case 'not_configured':
        return 'Not Configured';
      case 'error':
        return 'Connection Error';
      default:
        return 'Checking...';
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <NotificationsIcon sx={{ fontSize: 40, color: 'primary.main' }} />
        <Box>
          <Typography variant="h4" fontWeight="bold">
            Real-time Notifications
          </Typography>
          <Typography variant="body2" color="text.secondary">
            WebSocket connection for live updates
          </Typography>
        </Box>
      </Box>

      {/* Connection Status Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Connection Status
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {isConnected ? (
                  <CheckCircleIcon sx={{ color: 'success.main' }} />
                ) : (
                  <ErrorIcon sx={{ color: 'error.main' }} />
                )}
                <Chip
                  label={getStatusText()}
                  color={getStatusColor()}
                  size="small"
                />
              </Box>
              {isConnected && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Receiving live updates
                </Typography>
              )}
            </Box>
            <SignalIcon sx={{ fontSize: 60, color: isConnected ? 'success.main' : 'text.disabled' }} />
          </Box>

          {!isConnected && connectionStatus !== 'checking' && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              WebSocket connection is not active. Real-time updates are disabled.
              Try refreshing the page or logging out and back in.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Information Card */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Alert severity="info" sx={{ mb: 2 }}>
          WebSocket connection is established automatically when you log in.
          The connection enables real-time updates throughout the application.
        </Alert>

        <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
          Real-time Features
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <List>
          {realTimeFeatures.map((feature, index) => (
            <React.Fragment key={index}>
              <ListItem alignItems="flex-start">
                <ListItemIcon sx={{ mt: 1 }}>
                  {feature.icon}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="subtitle1" fontWeight="medium">
                      {feature.title}
                    </Typography>
                  }
                  secondary={
                    <Typography variant="body2" color="text.secondary">
                      {feature.description}
                    </Typography>
                  }
                />
              </ListItem>
              {index < realTimeFeatures.length - 1 && <Divider variant="inset" component="li" />}
            </React.Fragment>
          ))}
        </List>
      </Paper>

      {/* Technical Information */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Technical Information
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <Typography variant="body2" color="text.secondary" paragraph>
          <strong>Protocol:</strong> WebSocket (WSS for secure connections)
        </Typography>

        <Typography variant="body2" color="text.secondary" paragraph>
          <strong>Connection:</strong> Automatic on login, maintained throughout session
        </Typography>

        <Typography variant="body2" color="text.secondary" paragraph>
          <strong>Reconnection:</strong> Automatic with exponential backoff on connection loss
        </Typography>

        <Typography variant="body2" color="text.secondary">
          <strong>Authentication:</strong> JWT token-based, same as HTTP API
        </Typography>
      </Paper>
    </Container>
  );
}

export default WebSocketSettingsPage;
