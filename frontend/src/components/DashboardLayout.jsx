/**
 * Dashboard Layout with Sidebar Navigation
 * Version: 1.2.0
 * Last Updated: 2025-11-17
 *
 * Changelog:
 * ----------
 * v1.2.0 (2025-11-17):
 *   - Implemented fully hierarchical module navigation
 *   - Dynamically loads sub-modules from API (parent_module_id)
 *   - Filters to show only top-level modules, sub-modules nested under parents
 *   - Maps inventory sub-module keys to proper routes
 *   - Fixed issue where sub-modules were showing flat in sidebar
 *
 * v1.1.0 (2025-11-17):
 *   - Fixed duplicate dashboard appearing in sidebar
 *   - Added Module Management submenu to Admin Panel
 *   - Added Dashboard submenu to Inventory Management
 *   - Improved module filtering to exclude dashboard from dynamic list
 *
 * v1.0.0 (2025-11-17):
 *   - Initial dashboard layout with sidebar navigation
 *   - Dynamic module loading from API
 *   - Expandable/collapsible submenus
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
  const [allModules, setAllModules] = useState([]);
  const [expandedModules, setExpandedModules] = useState({});

  // Fetch user accessible modules
  useEffect(() => {
    const fetchModules = async () => {
      try {
        const data = await dashboardAPI.getUserModules();
        setAllModules(data.modules || []);
      } catch (error) {
        console.error('Failed to fetch modules:', error);
      }
    };

    fetchModules();
  }, []);

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
    } else {
      // Navigate to module's default route
      navigate(`/${moduleKey}`);

      // Also toggle expand for modules with sub-menus
      if (hasSubModules) {
        setExpandedModules((prev) => ({
          ...prev,
          [moduleKey]: !prev[moduleKey],
        }));
      }
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

  // Map sub-module keys to routes
  const getSubModuleRoute = (parentModuleKey, subModuleKey) => {
    // Admin sub-modules (hardcoded for now)
    const adminRoutes = {
      admin_users: '/admin/users',
      admin_modules: '/admin/modules',
      admin_activity: '/admin/activity',
    };

    // Inventory sub-modules
    const inventoryRoutes = {
      inventory_dashboard: '/inventory',
      inventory_current_stock: '/inventory/current-stock',
      inventory_add_stock: '/inventory/stock',
      inventory_adjustments: '/inventory/adjustments',
      inventory_purchase_orders: '/inventory/purchase-orders',
      inventory_alerts: '/inventory/alerts',
      inventory_history: '/inventory/history',
      inventory_items: '/inventory/items',
      inventory_categories: '/inventory/categories',
      inventory_suppliers: '/inventory/suppliers',
      inventory_analytics: '/inventory/analytics',
    };

    // Biofloc sub-modules
    const bioflocRoutes = {
      biofloc_dashboard: '/biofloc',
      biofloc_tanks: '/biofloc/tanks',
      biofloc_batches: '/biofloc/batches',
      biofloc_feeding: '/biofloc/feeding',
      biofloc_sampling: '/biofloc/sampling',
      biofloc_mortality: '/biofloc/mortality',
      biofloc_water_tests: '/biofloc/water-tests',
      biofloc_harvests: '/biofloc/harvests',
    };

    if (parentModuleKey === 'admin') {
      return adminRoutes[subModuleKey] || `/admin/${subModuleKey.replace('admin_', '')}`;
    } else if (parentModuleKey === 'inventory') {
      return inventoryRoutes[subModuleKey] || `/inventory/${subModuleKey.replace('inventory_', '')}`;
    } else if (parentModuleKey === 'biofloc') {
      return bioflocRoutes[subModuleKey] || `/biofloc/${subModuleKey.replace('biofloc_', '')}`;
    }

    // Default: construct route from keys
    return `/${parentModuleKey}/${subModuleKey.replace(`${parentModuleKey}_`, '')}`;
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
