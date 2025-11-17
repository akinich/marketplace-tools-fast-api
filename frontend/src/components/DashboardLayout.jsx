/**
 * Dashboard Layout with Sidebar Navigation
 * Version: 1.0.0
 */

import React, { useState, useEffect } from 'react';
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
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  AdminPanelSettings as AdminIcon,
  Inventory as InventoryIcon,
  Science as BioflocIcon,
  AccountCircle,
  Logout,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';

import useAuthStore from '../store/authStore';
import { dashboardAPI } from '../api';

const DRAWER_WIDTH = 260;

export default function DashboardLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { enqueueSnackbar } = useSnackbar();
  const { user, logout } = useAuthStore();

  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [modules, setModules] = useState([]);
  const [expandedModules, setExpandedModules] = useState({});

  // Fetch user accessible modules
  useEffect(() => {
    const fetchModules = async () => {
      try {
        const data = await dashboardAPI.getUserModules();
        setModules(data.modules);
      } catch (error) {
        console.error('Failed to fetch modules:', error);
      }
    };

    fetchModules();
  }, []);

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

  const handleModuleClick = (moduleKey) => {
    if (moduleKey === 'dashboard') {
      navigate('/dashboard');
    } else {
      // Toggle expand for modules with sub-menus
      setExpandedModules((prev) => ({
        ...prev,
        [moduleKey]: !prev[moduleKey],
      }));
    }
  };

  const getModuleIcon = (moduleKey) => {
    const icons = {
      dashboard: <DashboardIcon />,
      admin: <AdminIcon />,
      inventory: <InventoryIcon />,
      biofloc: <BioflocIcon />,
    };
    return icons[moduleKey] || <DashboardIcon />;
  };

  const drawer = (
    <Box>
      <Toolbar sx={{ backgroundColor: 'primary.main', color: 'white' }}>
        <Typography variant="h6" noWrap component="div">
          Farm Management
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

        {/* Dynamic Modules */}
        {modules.map((module) => (
          <React.Fragment key={module.module_key}>
            <ListItem disablePadding>
              <ListItemButton
                selected={location.pathname.startsWith(`/${module.module_key}`)}
                onClick={() => handleModuleClick(module.module_key)}
              >
                <ListItemIcon>{getModuleIcon(module.module_key)}</ListItemIcon>
                <ListItemText primary={module.module_name} />
                {['admin', 'inventory'].includes(module.module_key) && (
                  expandedModules[module.module_key] ? <ExpandLess /> : <ExpandMore />
                )}
              </ListItemButton>
            </ListItem>

            {/* Sub-menus for Admin */}
            {module.module_key === 'admin' && (
              <Collapse in={expandedModules.admin} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  <ListItemButton
                    sx={{ pl: 4 }}
                    selected={location.pathname === '/admin/users'}
                    onClick={() => navigate('/admin/users')}
                  >
                    <ListItemText primary="User Management" />
                  </ListItemButton>
                  <ListItemButton
                    sx={{ pl: 4 }}
                    selected={location.pathname === '/admin/activity'}
                    onClick={() => navigate('/admin/activity')}
                  >
                    <ListItemText primary="Activity Logs" />
                  </ListItemButton>
                </List>
              </Collapse>
            )}

            {/* Sub-menus for Inventory */}
            {module.module_key === 'inventory' && (
              <Collapse in={expandedModules.inventory} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  <ListItemButton
                    sx={{ pl: 4 }}
                    selected={location.pathname === '/inventory/items'}
                    onClick={() => navigate('/inventory/items')}
                  >
                    <ListItemText primary="Items" />
                  </ListItemButton>
                  <ListItemButton
                    sx={{ pl: 4 }}
                    selected={location.pathname === '/inventory/stock'}
                    onClick={() => navigate('/inventory/stock')}
                  >
                    <ListItemText primary="Stock Operations" />
                  </ListItemButton>
                  <ListItemButton
                    sx={{ pl: 4 }}
                    selected={location.pathname === '/inventory/purchase-orders'}
                    onClick={() => navigate('/inventory/purchase-orders')}
                  >
                    <ListItemText primary="Purchase Orders" />
                  </ListItemButton>
                  <ListItemButton
                    sx={{ pl: 4 }}
                    selected={location.pathname === '/inventory/alerts'}
                    onClick={() => navigate('/inventory/alerts')}
                  >
                    <ListItemText primary="Alerts" />
                  </ListItemButton>
                </List>
              </Collapse>
            )}
          </React.Fragment>
        ))}
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
            {user?.full_name || 'User'}
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
    </Box>
  );
}
