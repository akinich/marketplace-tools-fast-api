/**
 * Dashboard Layout with Sidebar Navigation
 * Version: 1.10.0
 * Last Updated: 2025-11-23
 *
 * Changelog:
 * ----------
 * v1.10.0 (2025-11-23):
 *   - Integrated WebSocket real-time notifications
 *   - Show toast notifications for ticket created/updated events
 *   - Listen for user online/offline presence updates
 *   - Removed hardcoded API Keys menu item (now under Communication module)
 *   - API Keys accessible via Communication > API Keys in hierarchical navigation
 *   - Cleaned up navigation structure for better module organization
 *
 * v1.9.0 (2025-11-23):
 *   - Added API Keys menu item to sidebar navigation
 *   - Added VpnKey icon for API keys section
 *
 * v1.8.0 (2025-11-23):
 *   - Fixed parent module navigation behavior
 *   - Parent modules with sub-modules now only expand/collapse (no navigation)
 *   - Prevents page refresh when clicking on Communication or other parent modules
 *   - Added Communication module icon and route mappings
 *
 * v1.7.0 (2025-11-22):
 *   - Added Settings menu item to sidebar navigation (Admin only)
 *   - Settings accessible between Dashboard and dynamic modules
 *   - Admin role check with proper navigation and selection highlighting
 *
 * v1.6.0 (2025-11-22):
 *   - Auto-expand parent module in sidebar based on current URL path
 *   - Fixes issue where refreshing a sub-module page (e.g., /admin/users) collapsed the sidebar
 *   - Parent module now stays expanded when navigating to or refreshing sub-module pages
 *
 * v1.5.0 (2025-11-22):

 *   - Added admin_telegram route mapping for Telegram Notifications settings
 *   - Both admin sub-modules now accessible from navigation sidebar
 *
 * v1.4.0 (2025-11-21):
 *   - Added "My Profile" option in user menu dropdown
 *   - Added Person icon import
 *
 * v1.3.0 (2025-11-20):
 *   - Added 30-minute inactivity timeout with auto-logout
 *   - Tracks user activity (mouse, keyboard, scroll, touch)
 *   - Shows warning dialog before logout
 *   - Resets timer on any user activity
 *
 * v1.2.0 (2025-11-17):
 *   - Implemented fully hierarchical module navigation
 *   - Dynamically loads sub-modules from API (parent_module_id)
 *   - Filters to show only top-level modules, sub-modules nested under parents
 *   - Maps sub-module keys to proper routes
 *   - Fixed issue where sub-modules were showing flat in sidebar
 *
 * v1.1.0 (2025-11-17):
 *   - Fixed duplicate dashboard appearing in sidebar
 *   - Added Module Management submenu to Admin Panel

 *   - Improved module filtering to exclude dashboard from dynamic list
 *
 * v1.0.0 (2025-11-17):
 *   - Initial dashboard layout with sidebar navigation
 *   - Dynamic module loading from API
 *   - Expandable/collapsible submenus
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Menu,
  MenuItem,
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  AdminPanelSettings as AdminIcon,
  ShoppingCart as B2COpsIcon,
  ConfirmationNumber as TicketsIcon,
  Code as DevelopmentIcon,
  Campaign as CommunicationIcon,
  VpnKey as VpnKeyIcon,
  Storage as DatabaseIcon,
  Inventory2 as InventoryIcon,
  LocalShipping as InwardIcon,
  AccountCircle,
  Logout,
  Lock,
  Person,
  ExpandLess,
  ExpandMore,
  Warning as WarningIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';

import useAuthStore from '../store/authStore';
import { dashboardAPI } from '../api';
import websocketService from '../services/websocket';

const DRAWER_WIDTH = 260;
const SESSION_TIMEOUT = 30 * 60 * 1000; // 2 minutes in milliseconds (for testing)
const WARNING_TIME = 60 * 1000; // Show warning 1 minute before timeout

export default function DashboardLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { enqueueSnackbar } = useSnackbar();
  const { user, logout } = useAuthStore();

  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [allModules, setAllModules] = useState([]);
  const [expandedModules, setExpandedModules] = useState({});

  // Session timeout state
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false);
  const [timeoutCountdown, setTimeoutCountdown] = useState(60);
  const timeoutRef = useRef(null);
  const warningTimeoutRef = useRef(null);
  const countdownRef = useRef(null);
  const isWarningShownRef = useRef(false);

  // Handle session timeout logout
  const handleSessionTimeout = useCallback(async () => {
    setShowTimeoutWarning(false);
    isWarningShownRef.current = false;
    await logout();
    enqueueSnackbar('Session expired due to inactivity', { variant: 'warning' });
    navigate('/login');
  }, [logout, navigate, enqueueSnackbar]);

  // Reset the inactivity timer
  const resetTimer = useCallback(() => {
    // Clear existing timers
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current);
    if (countdownRef.current) clearInterval(countdownRef.current);

    // Hide warning if shown
    setShowTimeoutWarning(false);
    isWarningShownRef.current = false;
    setTimeoutCountdown(60);

    // Set warning timer (1 minute before timeout)
    warningTimeoutRef.current = setTimeout(() => {
      setShowTimeoutWarning(true);
      isWarningShownRef.current = true;
      setTimeoutCountdown(60);

      // Start countdown
      countdownRef.current = setInterval(() => {
        setTimeoutCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(countdownRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }, SESSION_TIMEOUT - WARNING_TIME);

    // Set logout timer
    timeoutRef.current = setTimeout(() => {
      handleSessionTimeout();
    }, SESSION_TIMEOUT);
  }, [handleSessionTimeout]);

  // Continue session (user clicked "Stay Logged In")
  const handleContinueSession = () => {
    resetTimer();
    enqueueSnackbar('Session extended', { variant: 'success' });
  };

  // Set up activity listeners
  useEffect(() => {
    // Check if session expired while tab was closed
    const lastActivity = localStorage.getItem('last_activity');
    if (lastActivity) {
      const timeSinceLastActivity = Date.now() - parseInt(lastActivity);
      if (timeSinceLastActivity > SESSION_TIMEOUT) {
        // Session expired while tab was closed
        enqueueSnackbar('Session expired due to inactivity', { variant: 'warning' });
        logout();
        navigate('/login');
        return;
      }
    }

    const activityEvents = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart', 'click'];

    const handleActivity = () => {
      // Store last activity timestamp
      localStorage.setItem('last_activity', Date.now().toString());

      // Only reset timer if warning is not shown
      if (!isWarningShownRef.current) {
        resetTimer();
      }
    };

    // Add event listeners
    activityEvents.forEach((event) => {
      document.addEventListener(event, handleActivity);
    });

    // Initialize timer and set initial last activity
    localStorage.setItem('last_activity', Date.now().toString());
    resetTimer();

    // Cleanup
    return () => {
      activityEvents.forEach((event) => {
        document.removeEventListener(event, handleActivity);
      });
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current);
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, [resetTimer, logout, navigate, enqueueSnackbar]);

  // Fetch user accessible modules
  useEffect(() => {
    const fetchModules = async () => {
      try {
        console.log('[DashboardLayout] Fetching user modules...');
        const data = await dashboardAPI.getUserModules();
        console.log('[DashboardLayout] Modules received:', data);
        setAllModules(data.modules || []);
        if (!data.modules || data.modules.length === 0) {
          console.warn('[DashboardLayout] No modules returned from API');
        }
      } catch (error) {
        console.error('[DashboardLayout] Failed to fetch modules:', error);
        enqueueSnackbar('Failed to load navigation modules. Please refresh the page.', {
          variant: 'error',
          persist: true
        });
      }
    };

    fetchModules();
  }, [enqueueSnackbar]);

  // Set up WebSocket event listeners for real-time notifications
  useEffect(() => {
    // Listen for ticket created events
    const handleTicketCreated = (data) => {
      enqueueSnackbar(`New ticket created: ${data.title}`, {
        variant: 'info',
        autoHideDuration: 5000
      });
    };

    // Listen for ticket updated events
    const handleTicketUpdated = (data) => {
      enqueueSnackbar(`Ticket updated: ${data.title}`, {
        variant: 'info',
        autoHideDuration: 5000
      });
    };

    // Listen for notifications
    const handleNotification = (data) => {
      enqueueSnackbar(data.message, {
        variant: data.type || 'info',
        autoHideDuration: 5000
      });
    };

    // Register listeners
    websocketService.on('ticket.created', handleTicketCreated);
    websocketService.on('ticket.updated', handleTicketUpdated);
    websocketService.on('notification', handleNotification);

    // Cleanup
    return () => {
      websocketService.off('ticket.created', handleTicketCreated);
      websocketService.off('ticket.updated', handleTicketUpdated);
      websocketService.off('notification', handleNotification);
    };
  }, [enqueueSnackbar]);

  // Auto-expand parent module based on current path
  useEffect(() => {
    if (allModules.length === 0) return;

    // Check if current path matches a sub-module
    const currentPath = location.pathname;

    // Find which parent module should be expanded
    const pathParts = currentPath.split('/').filter(Boolean);
    if (pathParts.length >= 2) {
      const parentKey = pathParts[0]; // e.g., 'admin', 'communication'

      // Expand this parent module
      setExpandedModules((prev) => ({
        ...prev,
        [parentKey]: true,
      }));
    }
  }, [location.pathname, allModules]);

  // Separate top-level modules and sub-modules
  const topLevelModules = allModules.filter((m) => !m.parent_module_id && m.module_key !== 'dashboard');
  const getSubModules = (parentModuleId) => {
    return allModules.filter((m) => m.parent_module_id === parentModuleId);
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleMenuClose();
    await logout();
    enqueueSnackbar('Logged out successfully', { variant: 'success' });
    navigate('/login');
  };

  const handleModuleClick = (moduleKey, hasSubModules) => {
    if (moduleKey === 'dashboard') {
      navigate('/dashboard');
    } else if (hasSubModules) {
      // If module has sub-modules, only toggle expand/collapse (don't navigate)
      setExpandedModules((prev) => ({
        ...prev,
        [moduleKey]: !prev[moduleKey],
      }));
    } else {
      // If no sub-modules, navigate to the module's route
      navigate(`/${moduleKey}`);
    }
  };

  const getModuleIcon = (moduleKey) => {
    const icons = {
      dashboard: <DashboardIcon />,
      admin: <AdminIcon />,
      b2c_ops: <B2COpsIcon />,
      b2c_management: <B2COpsIcon />,
      tickets: <TicketsIcon />,
      development: <DevelopmentIcon />,
      communication: <CommunicationIcon />,
      database_management: <DatabaseIcon />,
      inventory: <InventoryIcon />,
      inward: <InwardIcon />,
    };
    return icons[moduleKey] || <DashboardIcon />;
  };

  // Map sub-module keys to routes
  const getSubModuleRoute = (parentModuleKey, subModuleKey) => {
    // Admin sub-modules (hardcoded for now)
    const adminRoutes = {
      admin_users: '/admin/users',
      admin_modules: '/admin/modules',
      admin_activity: '/admin/activity',
      admin_security: '/admin/security',

      admin_telegram: '/admin/telegram',
    };




    // B2C Ops sub-modules
    const b2cOpsRoutes = {
      order_extractor: '/b2c-ops/order-extractor',
      label_generator: '/b2c-ops/label-generator',
      mrp_label_generator: '/b2c-ops/mrp-label-generator',
    };

    // B2C Management sub-modules
    const b2cManagementRoutes = {
      woo_to_zoho_export: '/b2c-ops/woo-to-zoho-export',
      stock_price_updater: '/b2c-ops/stock-price-updater',
      order_place_test: '/b2c-ops/order-place-test',
    };

    // Database Management sub-modules
    const databaseManagementRoutes = {
      woo_customer_master: '/database-management/woo-customer-master',
      woo_item_master: '/database-management/woo-item-master',
      zoho_customer_master: '/database-management/zoho-customer-master',
      zoho_item_master: '/database-management/zoho-item-master',
      zoho_vendor_master: '/database-management/zoho-vendor-master',
    };

    // Communication sub-modules
    const communicationRoutes = {
      com_telegram: '/communication/telegram',
      com_smtp: '/communication/smtp',
      com_webhooks: '/communication/webhooks',
      com_api_keys: '/communication/api-keys',
      com_websockets: '/communication/websockets',
    };

    // Inventory sub-modules
    const inventoryRoutes = {
      batch_tracking: '/inventory/batch-tracking',
      wastage_tracking: '/inventory/wastage-tracking',
    };

    // Inward Operations sub-modules
    const inwardRoutes = {
      purchase_orders: '/inward/purchase-orders',
      vendor_pricing: '/inward/vendor-pricing',
    };

    if (parentModuleKey === 'admin') {
      return adminRoutes[subModuleKey] || `/admin/${subModuleKey.replace('admin_', '')}`;
    } else if (parentModuleKey === 'b2c_ops') {
      return b2cOpsRoutes[subModuleKey] || `/b2c-ops/${subModuleKey.replace('b2c_ops_', '')}`;
    } else if (parentModuleKey === 'b2c_management') {
      return b2cManagementRoutes[subModuleKey] || `/b2c-ops/${subModuleKey}`;
    } else if (parentModuleKey === 'communication') {
      return communicationRoutes[subModuleKey] || `/communication/${subModuleKey.replace('com_', '')}`;
    } else if (parentModuleKey === 'database_management') {
      return databaseManagementRoutes[subModuleKey] || `/database-management/${subModuleKey}`;
    } else if (parentModuleKey === 'inventory') {
      return inventoryRoutes[subModuleKey] || `/inventory/${subModuleKey}`;
    } else if (parentModuleKey === 'inward') {
      return inwardRoutes[subModuleKey] || `/inward/${subModuleKey}`;
    }

    // Default: construct route from keys
    return `/${parentModuleKey}/${subModuleKey.replace(`${parentModuleKey}_`, '')}`;
  };

  const drawer = (
    <Box>
      <Toolbar sx={{ backgroundColor: 'primary.main', color: 'white' }}>
        <Typography variant="h6" noWrap component="div">
          Marketplace ERP
        </Typography>
      </Toolbar>
      <Divider />

      <List>
        {/* Dashboard */}
        <ListItem disablePadding>
          <ListItemButton
            selected={location.pathname === '/dashboard' || location.pathname === '/'}
            onClick={() => navigate('/dashboard')}
          >
            <ListItemIcon>
              <DashboardIcon />
            </ListItemIcon>
            <ListItemText primary="Dashboard" />
          </ListItemButton>
        </ListItem>



        {/* Dynamic Modules (only top-level, exclude dashboard) */}
        {topLevelModules.map((module) => {
          const subModules = getSubModules(module.module_id);
          const hasSubModules = subModules.length > 0;

          return (
            <React.Fragment key={module.module_key}>
              <ListItem disablePadding>
                <ListItemButton
                  selected={location.pathname.startsWith(`/${module.module_key}`)}
                  onClick={() => handleModuleClick(module.module_key, hasSubModules)}
                >
                  <ListItemIcon>{getModuleIcon(module.module_key)}</ListItemIcon>
                  <ListItemText primary={module.module_name} />
                  {hasSubModules && (
                    expandedModules[module.module_key] ? <ExpandLess /> : <ExpandMore />
                  )}
                </ListItemButton>
              </ListItem>

              {/* Dynamic Sub-menus */}
              {hasSubModules && (
                <Collapse in={expandedModules[module.module_key]} timeout="auto" unmountOnExit>
                  <List component="div" disablePadding>
                    {subModules.map((subModule) => {
                      const route = getSubModuleRoute(module.module_key, subModule.module_key);
                      return (
                        <ListItemButton
                          key={subModule.module_key}
                          sx={{ pl: 4 }}
                          selected={location.pathname === route}
                          onClick={() => navigate(route)}
                        >
                          <ListItemText primary={subModule.module_name} />
                        </ListItemButton>
                      );
                    })}
                  </List>
                </Collapse>
              )}
            </React.Fragment>
          );
        })}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { sm: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Welcome, {user?.full_name || 'User'}
          </Typography>

          <IconButton color="inherit" onClick={handleMenuOpen}>
            <AccountCircle />
          </IconButton>

          <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
            <MenuItem disabled>
              <Typography variant="body2" color="text.secondary">
                {user?.email}
              </Typography>
            </MenuItem>
            <MenuItem disabled>
              <Typography variant="caption" color="text.secondary">
                Role: {user?.role}
              </Typography>
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => { handleMenuClose(); navigate('/profile'); }}>
              <ListItemIcon>
                <Person fontSize="small" />
              </ListItemIcon>
              My Profile
            </MenuItem>
            <MenuItem onClick={() => { handleMenuClose(); navigate('/change-password'); }}>
              <ListItemIcon>
                <Lock fontSize="small" />
              </ListItemIcon>
              Change Password
            </MenuItem>
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <Logout fontSize="small" />
              </ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <Box component="nav" sx={{ width: { sm: DRAWER_WIDTH }, flexShrink: { sm: 0 } }}>
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH },
          }}
        >
          {drawer}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${DRAWER_WIDTH}px)` },
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>

      {/* Session Timeout Warning Dialog */}
      <Dialog
        open={showTimeoutWarning}
        onClose={() => { }} // Prevent closing by clicking outside
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon color="warning" />
          Session Timeout Warning
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Your session will expire due to inactivity.
          </Typography>
          <Typography variant="h4" color="error" align="center" sx={{ my: 2 }}>
            {timeoutCountdown}s
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Click "Stay Logged In" to continue your session, or you will be automatically logged out.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleSessionTimeout} color="inherit">
            Logout Now
          </Button>
          <Button onClick={handleContinueSession} variant="contained" color="primary">
            Stay Logged In
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
