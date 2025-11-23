-- ============================================================================
-- Migration 009: SMTP Email Service
-- ============================================================================

-- Email templates table
CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    template_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    subject VARCHAR(500) NOT NULL,
    html_body TEXT NOT NULL,
    plain_body TEXT NOT NULL,
    variables JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_email_templates_key ON email_templates(template_key);

-- Email queue table
CREATE TABLE IF NOT EXISTS email_queue (
    id SERIAL PRIMARY KEY,
    to_email VARCHAR(255) NOT NULL,
    cc_emails TEXT[],
    bcc_emails TEXT[],
    subject VARCHAR(500) NOT NULL,
    html_body TEXT,
    plain_body TEXT NOT NULL,
    template_key VARCHAR(100),
    template_variables JSONB,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sending', 'sent', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    error_message TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_email_queue_status ON email_queue(status);
CREATE INDEX idx_email_queue_scheduled ON email_queue(scheduled_at);
CREATE INDEX idx_email_queue_to_email ON email_queue(to_email);

-- Email recipients configuration (for notification emails)
CREATE TABLE IF NOT EXISTS email_recipients (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(100) NOT NULL,
    recipient_emails TEXT[] NOT NULL,
    is_active BOOLEAN DEFAULT true,
    description TEXT,
    created_by UUID REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(notification_type)
);

CREATE INDEX idx_email_recipients_type ON email_recipients(notification_type);

-- Email send log (for tracking)
CREATE TABLE IF NOT EXISTS email_send_log (
    id SERIAL PRIMARY KEY,
    email_queue_id INTEGER REFERENCES email_queue(id) ON DELETE CASCADE,
    to_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_email_send_log_queue_id ON email_send_log(email_queue_id);
CREATE INDEX idx_email_send_log_status ON email_send_log(status);

-- Triggers for updated_at
CREATE TRIGGER trigger_update_email_templates_updated_at
    BEFORE UPDATE ON email_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_email_queue_updated_at
    BEFORE UPDATE ON email_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_email_recipients_updated_at
    BEFORE UPDATE ON email_recipients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default email templates
INSERT INTO email_templates (template_key, name, description, subject, html_body, plain_body, variables) VALUES

-- Welcome email
('welcome', 'Welcome Email', 'Sent when a new user account is created',
'Welcome to {{app_name}}',
'<!DOCTYPE html>
<html>
<head><style>body{font-family:Arial,sans-serif;line-height:1.6;}</style></head>
<body>
<h2>Welcome to {{app_name}}!</h2>
<p>Hi {{user_name}},</p>
<p>Your account has been created successfully. Here are your login details:</p>
<ul>
<li><strong>Email:</strong> {{user_email}}</li>
<li><strong>Temporary Password:</strong> {{temp_password}}</li>
</ul>
<p>Please log in and change your password immediately.</p>
<p><a href="{{login_url}}" style="background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;display:inline-block;">Login Now</a></p>
<p>If you have any questions, contact us at {{support_email}}.</p>
<p>Best regards,<br>{{app_name}} Team</p>
</body>
</html>',
'Welcome to {{app_name}}!

Hi {{user_name}},

Your account has been created successfully. Here are your login details:

Email: {{user_email}}
Temporary Password: {{temp_password}}

Please log in and change your password immediately.

Login at: {{login_url}}

If you have any questions, contact us at {{support_email}}.

Best regards,
{{app_name}} Team',
'["app_name", "user_name", "user_email", "temp_password", "login_url", "support_email"]'::jsonb),

-- Ticket created
('ticket_created', 'Ticket Created', 'Sent when a new ticket is created',
'New Ticket Created: {{ticket_title}}',
'<!DOCTYPE html>
<html>
<head><style>body{font-family:Arial,sans-serif;line-height:1.6;}.priority-high{color:#dc3545;} .priority-medium{color:#ffc107;} .priority-low{color:#28a745;}</style></head>
<body>
<h2>New Ticket Created</h2>
<p><strong>Title:</strong> {{ticket_title}}</p>
<p><strong>Priority:</strong> <span class="priority-{{priority}}">{{priority}}</span></p>
<p><strong>Type:</strong> {{ticket_type}}</p>
<p><strong>Created by:</strong> {{created_by}}</p>
<p><strong>Description:</strong></p>
<p>{{description}}</p>
<p><a href="{{ticket_url}}" style="background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;display:inline-block;">View Ticket</a></p>
</body>
</html>',
'New Ticket Created

Title: {{ticket_title}}
Priority: {{priority}}
Type: {{ticket_type}}
Created by: {{created_by}}

Description:
{{description}}

View ticket at: {{ticket_url}}',
'["ticket_title", "priority", "ticket_type", "created_by", "description", "ticket_url"]'::jsonb),

-- Low stock alert
('low_stock_alert', 'Low Stock Alert', 'Sent when items are below reorder level',
'Low Stock Alert: {{item_count}} items need attention',
'<!DOCTYPE html>
<html>
<head><style>body{font-family:Arial,sans-serif;line-height:1.6;}table{border-collapse:collapse;width:100%;}th,td{border:1px solid #ddd;padding:8px;text-align:left;}th{background:#f2f2f2;}</style></head>
<body>
<h2>Low Stock Alert</h2>
<p>The following items are below their reorder levels:</p>
<table>
<tr><th>Item</th><th>Current Stock</th><th>Reorder Level</th></tr>
{{#items}}
<tr><td>{{name}}</td><td>{{current_quantity}}</td><td>{{reorder_level}}</td></tr>
{{/items}}
</table>
<p><a href="{{inventory_url}}" style="background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;display:inline-block;">View Inventory</a></p>
</body>
</html>',
'Low Stock Alert

The following items are below their reorder levels:

{{#items}}
- {{name}}: {{current_quantity}} (reorder at {{reorder_level}})
{{/items}}

View inventory at: {{inventory_url}}',
'["item_count", "items", "inventory_url"]'::jsonb)

ON CONFLICT (template_key) DO NOTHING;

-- Insert default email recipients
INSERT INTO email_recipients (notification_type, recipient_emails, description) VALUES
('tickets_critical', ARRAY[]::TEXT[], 'Recipients for critical priority tickets'),
('tickets_all', ARRAY[]::TEXT[], 'Recipients for all ticket notifications'),
('low_stock', ARRAY[]::TEXT[], 'Recipients for low stock alerts'),
('user_created', ARRAY[]::TEXT[], 'Recipients notified when new users are created')
ON CONFLICT (notification_type) DO NOTHING;

-- Verify migration
SELECT 'Email templates created:' as info, COUNT(*) as count FROM email_templates;
SELECT 'Email recipients created:' as info, COUNT(*) as count FROM email_recipients;
