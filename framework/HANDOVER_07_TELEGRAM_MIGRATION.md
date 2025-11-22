# HANDOVER MESSAGE #7: Telegram Module Migration & Navigation Updates

## 📋 MISSION
Migrate the existing **Telegram module** under the Communication parent module and update all frontend navigation to reflect the new Communication module structure.

## 🎯 WHAT TO DO

1. **Update database references** (already done in Handover #1)
2. **Update frontend routes** to new paths
3. **Update navigation menu** to show Communication parent with children
4. **Update permissions** checks for new module keys
5. **Test all Communication modules** accessible from UI

---

## PART 1: FRONTEND ROUTE UPDATES

### File 1: Update `frontend/src/App.jsx`

Update Telegram route:

```javascript
// OLD:
<Route path="/telegram" element={<TelegramSettingsPage />} />

// NEW:
<Route path="/communication/telegram" element={<TelegramSettingsPage />} />

// ADD new Communication module routes:
<Route path="/communication/smtp" element={<EmailManagementPage />} />
<Route path="/communication/webhooks" element={<WebhooksPage />} />
<Route path="/communication/api-keys" element={<APIKeysPage />} />
<Route path="/communication/websockets" element={<WebSocketSettingsPage />} />
```

---

## PART 2: NAVIGATION MENU UPDATES

### File 2: Update `frontend/src/components/DashboardLayout.jsx`

Update sidebar navigation to show hierarchical Communication menu:

```javascript
import {
  Communication as CommunicationIcon,
  Telegram as TelegramIcon,
  Email as EmailIcon,
  Webhook as WebhookIcon,
  VpnKey as VpnKeyIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';

// Update navigation items structure
const navigationItems = [
  // ... existing items

  // Communication parent module
  {
    key: 'communication',
    title: 'Communication',
    icon: <CommunicationIcon />,
    path: null, // Parent item, no direct path
    children: [
      {
        key: 'com_telegram',
        title: 'Telegram',
        icon: <TelegramIcon />,
        path: '/communication/telegram'
      },
      {
        key: 'com_smtp',
        title: 'Email (SMTP)',
        icon: <EmailIcon />,
        path: '/communication/smtp'
      },
      {
        key: 'com_webhooks',
        title: 'Webhooks',
        icon: <WebhookIcon />,
        path: '/communication/webhooks'
      },
      {
        key: 'com_api_keys',
        title: 'API Keys',
        icon: <VpnKeyIcon />,
        path: '/communication/api-keys'
      },
      {
        key: 'com_websockets',
        title: 'Real-time',
        icon: <NotificationsIcon />,
        path: '/communication/websockets'
      }
    ]
  }
];

// Update rendering logic to support nested items
function NavigationMenu({ modules }) {
  const [expandedItems, setExpandedItems] = useState({});

  const toggleExpanded = (key) => {
    setExpandedItems(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const hasAccess = (moduleKey) => {
    return modules.some(m => m.module_key === moduleKey && m.is_active);
  };

  const renderNavItem = (item, depth = 0) => {
    if (!hasAccess(item.key)) return null;

    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems[item.key];

    return (
      <React.Fragment key={item.key}>
        <ListItem
          button
          onClick={() => {
            if (hasChildren) {
              toggleExpanded(item.key);
            } else if (item.path) {
              navigate(item.path);
            }
          }}
          sx={{ pl: 2 + depth * 2 }}
        >
          <ListItemIcon>{item.icon}</ListItemIcon>
          <ListItemText primary={item.title} />
          {hasChildren && (
            isExpanded ? <ExpandLess /> : <ExpandMore />
          )}
        </ListItem>

        {/* Render children */}
        {hasChildren && isExpanded && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children.map(child => renderNavItem(child, depth + 1))}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    );
  };

  return (
    <List>
      {navigationItems.map(item => renderNavItem(item))}
    </List>
  );
}
```

---

## PART 3: UPDATE EXISTING TELEGRAM REFERENCES

### File 3: Search and update module key references

Run a global search and replace in frontend:

```bash
# Find all references to 'telegram' module key
grep -r "module_key.*telegram" frontend/src/

# Update to 'com_telegram'
```

Example files that may need updates:
- `frontend/src/pages/TelegramSettingsPage.jsx`
- Any permission checks
- Any API calls referencing the module

---

## PART 4: CREATE WEBSOCKET SETTINGS PAGE (Optional)

### File 4: `frontend/src/pages/WebSocketSettingsPage.jsx`

```javascript
import React from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Chip,
  Alert
} from '@mui/material';
import { CheckCircle as CheckIcon } from '@mui/icons-material';

function WebSocketSettingsPage() {
  const [isConnected, setIsConnected] = React.useState(false);

  React.useEffect(() => {
    // Check WebSocket connection status
    import('../services/websocket').then(module => {
      const ws = module.default;
      setIsConnected(ws.ws && ws.ws.readyState === WebSocket.OPEN);
    });
  }, []);

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Real-time Notifications
        </Typography>

        <Box display="flex" alignItems="center" gap={2} mb={3}>
          <Typography variant="body1">Status:</Typography>
          <Chip
            icon={isConnected ? <CheckIcon /> : null}
            label={isConnected ? 'Connected' : 'Disconnected'}
            color={isConnected ? 'success' : 'default'}
          />
        </Box>

        <Alert severity="info">
          WebSocket connection enables real-time updates for:
          <ul>
            <li>Dashboard statistics</li>
            <li>Ticket notifications</li>
            <li>Low stock alerts</li>
            <li>User presence indicators</li>
          </ul>
          The connection is established automatically when you log in.
        </Alert>
      </Paper>
    </Container>
  );
}

export default WebSocketSettingsPage;
```

---

## PART 5: UPDATE MODULE PERMISSIONS UI

### File 5: Update `frontend/src/pages/AdminPanel.jsx`

When displaying/editing user permissions, show Communication modules hierarchically:

```javascript
// When rendering module permissions
function ModulePermissionsTree({ modules, userPermissions, onChange }) {
  const grouped = modules.reduce((acc, module) => {
    if (module.parent_module_id) {
      // Child module
      const parent = modules.find(m => m.id === module.parent_module_id);
      if (parent) {
        if (!acc[parent.module_key]) {
          acc[parent.module_key] = { parent, children: [] };
        }
        acc[parent.module_key].children.push(module);
      }
    } else {
      // Parent module
      if (!acc[module.module_key]) {
        acc[module.module_key] = { parent: module, children: [] };
      }
    }
    return acc;
  }, {});

  return (
    <Box>
      {Object.entries(grouped).map(([key, { parent, children }]) => (
        <Box key={key} mb={2}>
          <FormControlLabel
            control={
              <Checkbox
                checked={userPermissions.includes(parent.id)}
                onChange={(e) => onChange(parent.id, e.target.checked)}
              />
            }
            label={<Typography fontWeight="bold">{parent.name}</Typography>}
          />

          {children.length > 0 && (
            <Box ml={4}>
              {children.map(child => (
                <FormControlLabel
                  key={child.id}
                  control={
                    <Checkbox
                      checked={userPermissions.includes(child.id)}
                      onChange={(e) => onChange(child.id, e.target.checked)}
                    />
                  }
                  label={child.name}
                />
              ))}
            </Box>
          )}
        </Box>
      ))}
    </Box>
  );
}
```

---

## PART 6: UPDATE API ENDPOINTS (if needed)

Most API endpoints don't need changes, but verify these still work:

```javascript
// OLD endpoint paths (should still work):
/api/v1/telegram/settings
/api/v1/telegram/status
/api/v1/telegram/link/create

// These don't need to change - module_key is used internally for permissions,
// not in API paths
```

---

## 🧪 TESTING STEPS

1. **Login as admin**
2. **Check sidebar navigation:**
   - Should see "Communication" parent item
   - Click to expand
   - Should see 5 children: Telegram, Email (SMTP), Webhooks, API Keys, Real-time
3. **Click each child item:**
   - Telegram → Should navigate to `/communication/telegram`
   - Email → Should navigate to `/communication/smtp`
   - Webhooks → Should navigate to `/communication/webhooks`
   - API Keys → Should navigate to `/communication/api-keys`
   - Real-time → Should navigate to `/communication/websockets`
4. **Verify permissions:**
   - Go to Admin Panel → Users → Edit User → Permissions
   - Should see Communication as parent with expandable children
   - Grant/revoke permissions - verify they work
5. **Test with non-admin user:**
   - Create user with only "com_smtp" permission
   - Login as that user
   - Should see Communication in sidebar
   - Should only see "Email (SMTP)" child (others hidden)
   - Should be able to access `/communication/smtp`
   - Should NOT be able to access `/communication/telegram` (403 or redirect)

---

## ✅ VERIFICATION CHECKLIST

- [ ] Communication parent shows in navigation
- [ ] All 5 child modules show when expanded
- [ ] Clicking each module navigates to correct page
- [ ] Permission checks work for each module
- [ ] Non-admin users only see modules they have access to
- [ ] Old `/telegram` route redirects to `/communication/telegram`
- [ ] All existing Telegram functionality still works

---

## 🔄 ROLLBACK PLAN

If issues occur:

1. **Frontend:** Revert route changes, restore old navigation
2. **Database:** Already has backward compatibility (old `telegram` key updated to `com_telegram`)
3. **Permissions:** User permissions auto-updated in migration

---

**READY FOR HANDOVER #8: Final Integration & Complete Documentation**
