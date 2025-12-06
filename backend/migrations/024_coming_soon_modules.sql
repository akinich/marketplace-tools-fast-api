-- ============================================================================
-- Migration: Register Coming Soon Modules
-- ============================================================================
-- Description: Registers all pending ERP modules with Coming Soon pages
-- Created: 2024-12-07
-- Modules: Inventory children, Inward children, Outward (parent + children),
--          B2C Management children, Tickets children, Reporting (parent + children)
-- ============================================================================

-- ============================================================================
-- INVENTORY MODULE - Add Children
-- ============================================================================

-- Inventory Dashboard
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'inventory_dashboard', 
    'Dashboard',
    'Overview of inventory operations, stock levels, and analytics',
    'Dashboard',
    (SELECT id FROM modules WHERE module_key = 'inventory'),
    true,
    5
) ON CONFLICT (module_key) DO NOTHING;

-- Stock Management
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'stock_management', 
    'Stock Management',
    'Track stock levels across locations with batch-level granularity',
    'Inventory',
    (SELECT id FROM modules WHERE module_key = 'inventory'),
    true,
    15
) ON CONFLICT (module_key) DO NOTHING;

-- ============================================================================
-- INWARD OPERATIONS MODULE - Add Children
-- ============================================================================

-- Inward Dashboard
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'inward_dashboard', 
    'Dashboard',
    'Overview of inward activities, active POs, and pending GRNs',
    'Dashboard',
    (SELECT id FROM modules WHERE module_key = 'inward'),
    true,
    5
) ON CONFLICT (module_key) DO NOTHING;

-- Grading & Sorting
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'grading_sorting', 
    'Grading & Sorting',
    'Internal quality control and grading of received produce',
    'Grade',
    (SELECT id FROM modules WHERE module_key = 'inward'),
    true,
    30
) ON CONFLICT (module_key) DO NOTHING;

-- Packing & Labeling
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'packing_labeling', 
    'Packing & Labeling',
    'Pack products into retail units and generate labels with batch numbers',
    'Inventory2',
    (SELECT id FROM modules WHERE module_key = 'inward'),
    true,
    40
) ON CONFLICT (module_key) DO NOTHING;

-- ============================================================================
-- OUTWARD OPERATIONS MODULE - New Parent + Children
-- ============================================================================

-- Outward Operations Parent Module
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'outward', 
    'Outward Operations',
    'Sales orders, invoicing, allocation, and logistics',
    'Send',
    NULL,
    true,
    30
) ON CONFLICT (module_key) DO NOTHING;

-- Outward Dashboard
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'outward_dashboard', 
    'Dashboard',
    'Overview of outward activities, pending SOs, and delivery status',
    'Dashboard',
    (SELECT id FROM modules WHERE module_key = 'outward'),
    true,
    5
) ON CONFLICT (module_key) DO NOTHING;

-- Sales Orders
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'sales_orders', 
    'Sales Orders',
    'Create and manage sales orders for B2B and B2C customers',
    'ShoppingCart',
    (SELECT id FROM modules WHERE module_key = 'outward'),
    true,
    10
) ON CONFLICT (module_key) DO NOTHING;

-- Invoice Management
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'invoice_management', 
    'Invoice Management',
    'Generate customer invoices from sales orders',
    'Receipt',
    (SELECT id FROM modules WHERE module_key = 'outward'),
    true,
    20
) ON CONFLICT (module_key) DO NOTHING;

-- Order Allocation
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'order_allocation', 
    'Order Allocation',
    'Allocate inventory batches to sales orders using FIFO',
    'Assignment',
    (SELECT id FROM modules WHERE module_key = 'outward'),
    true,
    30
) ON CONFLICT (module_key) DO NOTHING;

-- Customer Pricing Lists
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'customer_pricing', 
    'Customer Pricing Lists',
    'Manage customer-specific pricing for B2B clients',
    'PriceCheck',
    (SELECT id FROM modules WHERE module_key = 'outward'),
    true,
    40
) ON CONFLICT (module_key) DO NOTHING;

-- ============================================================================
-- B2C MANAGEMENT MODULE - Add Children
-- ============================================================================

-- B2C Management Dashboard
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'b2c_dashboard', 
    'Dashboard',
    'Overview of B2C backend management and sync status',
    'Dashboard',
    (SELECT id FROM modules WHERE module_key = 'b2c_management'),
    true,
    5
) ON CONFLICT (module_key) DO NOTHING;

-- Subscription Management
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'subscription_management', 
    'Subscription Management',
    'Build and track recurring monthly subscription orders for D2C customers',
    'Subscriptions',
    (SELECT id FROM modules WHERE module_key = 'b2c_management'),
    true,
    40
) ON CONFLICT (module_key) DO NOTHING;

-- ============================================================================
-- TICKET MANAGEMENT MODULE - Add Children
-- ============================================================================

-- Tickets Dashboard
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'tickets_dashboard', 
    'Dashboard',
    'Overview of all ticket activity and status distribution',
    'Dashboard',
    (SELECT id FROM modules WHERE module_key = 'tickets'),
    true,
    5
) ON CONFLICT (module_key) DO NOTHING;

-- B2B Tickets
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'b2b_tickets', 
    'B2B Tickets',
    'Manage customer issues for B2B clients (hotels and restaurants)',
    'Business',
    (SELECT id FROM modules WHERE module_key = 'tickets'),
    true,
    10
) ON CONFLICT (module_key) DO NOTHING;

-- B2C Tickets
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'b2c_tickets', 
    'B2C Tickets',
    'Manage customer issues for B2C customers (direct-to-home)',
    'Home',
    (SELECT id FROM modules WHERE module_key = 'tickets'),
    true,
    20
) ON CONFLICT (module_key) DO NOTHING;

-- Internal Tickets (move existing tickets to child)
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'internal_tickets', 
    'Internal Tickets',
    'Track ERP system issues, bugs, and feature requests',
    'BugReport',
    (SELECT id FROM modules WHERE module_key = 'tickets'),
    true,
    30
) ON CONFLICT (module_key) DO NOTHING;

-- ============================================================================
-- REPORTING MODULE - New Parent + Children
-- ============================================================================

-- Reporting Parent Module
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'reporting', 
    'Reporting',
    'Business intelligence reports and analytics across all modules',
    'Assessment',
    NULL,
    true,
    40
) ON CONFLICT (module_key) DO NOTHING;

-- Reporting Dashboard
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'reporting_dashboard', 
    'Dashboard',
    'Quick access to frequently run reports and scheduled reports',
    'Dashboard',
    (SELECT id FROM modules WHERE module_key = 'reporting'),
    true,
    5
) ON CONFLICT (module_key) DO NOTHING;

-- Purchase Analysis Reports
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'purchase_reports', 
    'Purchase Analysis',
    'Analyze procurement from farms, vendor performance, and pricing trends',
    'ShoppingBag',
    (SELECT id FROM modules WHERE module_key = 'reporting'),
    true,
    10
) ON CONFLICT (module_key) DO NOTHING;

-- Wastage Reports
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'wastage_reports', 
    'Wastage Reports',
    'Track wastage across all stages and identify cost impact',
    'DeleteSweep',
    (SELECT id FROM modules WHERE module_key = 'reporting'),
    true,
    20
) ON CONFLICT (module_key) DO NOTHING;

-- Inventory Reports
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'inventory_reports', 
    'Inventory Reports',
    'Track stock levels, turnover, aging, and valuation',
    'Inventory',
    (SELECT id FROM modules WHERE module_key = 'reporting'),
    true,
    30
) ON CONFLICT (module_key) DO NOTHING;

-- Sales Reports
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'sales_reports', 
    'Sales Reports',
    'Analyze B2B and B2C sales, customer performance, and product trends',
    'TrendingUp',
    (SELECT id FROM modules WHERE module_key = 'reporting'),
    true,
    40
) ON CONFLICT (module_key) DO NOTHING;

-- Operational Reports
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'operational_reports', 
    'Operational Reports',
    'Evaluate operational efficiency, fulfillment, and process performance',
    'Speed',
    (SELECT id FROM modules WHERE module_key = 'reporting'),
    true,
    50
) ON CONFLICT (module_key) DO NOTHING;

-- Financial Reports
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'financial_reports', 
    'Financial Reports',
    'Export data formatted for Zoho Books and analyze profitability',
    'AccountBalance',
    (SELECT id FROM modules WHERE module_key = 'reporting'),
    true,
    60
) ON CONFLICT (module_key) DO NOTHING;

-- Batch Traceability Reports
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'traceability_reports', 
    'Batch Traceability',
    'Complete traceability from farm to customer with batch history',
    'Timeline',
    (SELECT id FROM modules WHERE module_key = 'reporting'),
    true,
    70
) ON CONFLICT (module_key) DO NOTHING;

-- Logistics Reports
INSERT INTO modules (
    module_key, 
    module_name, 
    description,
    icon,
    parent_module_id, 
    is_active, 
    display_order
) VALUES (
    'logistics_reports', 
    'Logistics Reports',
    'Route efficiency, delivery performance, and vehicle utilization',
    'LocalShipping',
    (SELECT id FROM modules WHERE module_key = 'reporting'),
    true,
    80
) ON CONFLICT (module_key) DO NOTHING;

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- Run this to verify all modules were registered successfully

SELECT
    m.id,
    m.module_key,
    m.module_name,
    p.module_name as parent_module,
    m.is_active,
    m.display_order
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
WHERE m.module_key IN (
    -- Inventory children
    'inventory_dashboard', 'stock_management',
    -- Inward children
    'inward_dashboard', 'grading_sorting', 'packing_labeling',
    -- Outward parent + children
    'outward', 'outward_dashboard', 'sales_orders', 'invoice_management', 
    'order_allocation', 'customer_pricing',
    -- B2C Management children
    'b2c_dashboard', 'subscription_management',
    -- Tickets children
    'tickets_dashboard', 'b2b_tickets', 'b2c_tickets', 'internal_tickets',
    -- Reporting parent + children
    'reporting', 'reporting_dashboard', 'purchase_reports', 'wastage_reports',
    'inventory_reports', 'sales_reports', 'operational_reports', 'financial_reports',
    'traceability_reports', 'logistics_reports'
)
ORDER BY 
    COALESCE(p.display_order, m.display_order),
    m.display_order;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
