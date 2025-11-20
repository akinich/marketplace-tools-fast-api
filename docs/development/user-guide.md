# Development Planning Module - User Guide

**Version:** 1.0.1
**Audience:** Development Teams, Project Managers, Product Owners, All Team Members

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Feature Management](#feature-management)
4. [Implementation Steps](#implementation-steps)
5. [Team Collaboration](#team-collaboration)
6. [Workflows & Best Practices](#workflows--best-practices)
7. [Filtering & Search](#filtering--search)
8. [Tips & Tricks](#tips--tricks)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing the Module

1. Log in to the Farm Management System
2. Navigate to **Development Planning** from the main menu
3. You'll land on the Features List showing all planned work

### Navigation

**Main Views:**
- **Features List** - Overview of all features with filters
- **Feature Detail** - Detailed view of a single feature
- **Statistics** - Displayed at the top of Features List

**Key Actions:**
- **Add Feature** - Create new feature (admin only)
- **View Feature** - Click on any feature to see details
- **Filter** - Use status/priority filters to find features
- **Comment** - All users can add comments to features

### User Roles

**👑 Admin Users Can:**
- Create, edit, and delete features
- Manage implementation steps
- Change feature status and priority
- Set target dates
- Delete any comments
- All regular user capabilities

**👤 Regular Users Can:**
- View all features and details
- Add comments to features
- View progress and statistics
- Track development work
- Delete their own comments

---

## Dashboard Overview

The statistics dashboard at the top of the Features List provides a quick overview of your development pipeline.

### Key Metrics Cards

**Planned:** 📋 Features in planning stage, not yet started

**In Development:** 🔨 Features currently being implemented

**Testing:** 🧪 Features in QA/testing phase

**Completed:** ✅ Finished features

**Total Features:** 📊 Total number of features in the system

### Understanding the Numbers

- **Green numbers** indicate healthy progress
- High **Planned** count may indicate need to prioritize
- High **In Development** count may indicate work in progress limits
- High **Completed** count shows productivity

---

## Feature Management

### Viewing Features

**Features List View:**
- Features are displayed in a table
- Sorted by priority (critical → low) and creation date
- Shows status badge, priority badge, progress bar
- Displays target date if set
- Click **View** icon to see details

**Feature Detail View:**
- Full description
- Created by information
- Status and priority badges
- Target completion date
- All implementation steps
- Comment thread
- Edit button (admin only)

### Creating a Feature (Admin Only)

1. Click **+ Add Feature** button
2. Fill in the form:
   - **Title:** Brief, descriptive name (required)
   - **Description:** Detailed explanation, requirements, acceptance criteria
   - **Priority:** Select low, medium, high, or critical
   - **Target Date:** Optional deadline
3. Click **Create**
4. Feature is created with status "Planned"

**Best Practices:**
- Use clear, action-oriented titles (e.g., "Add user authentication", not "Authentication")
- Include acceptance criteria in description
- Set realistic target dates
- Start with appropriate priority

**Example Feature:**
```
Title: Add password reset functionality
Description:
Users should be able to reset their password via email link.

Requirements:
- Generate secure reset token
- Send email with reset link
- Reset link expires after 24 hours
- Validate new password strength

Acceptance Criteria:
- User receives email within 1 minute
- Link works only once
- Password is updated successfully
Priority: High
Target Date: 2025-12-15
```

### Editing a Feature (Admin Only)

1. Open the feature detail view
2. Click **Edit** button
3. Modify any fields:
   - Title
   - Description
   - Status (planned → in_development → testing → completed)
   - Priority
   - Target date
4. Click **Save**

**When to Change Status:**
- **planned → in_development:** Work has started
- **in_development → testing:** Implementation complete, ready for QA
- **testing → completed:** All tests passed, feature deployed
- **Any → on_hold:** Blocked or deprioritized
- **on_hold → Any:** Resuming work

### Deleting a Feature (Admin Only)

1. Open feature detail view
2. Click **Delete** button
3. Confirm deletion
4. **Warning:** This permanently deletes the feature, all steps, and all comments

---

## Implementation Steps

Implementation steps are the actionable tasks needed to complete a feature. They work like a checklist.

### Viewing Steps

Steps are displayed in the feature detail view:
- Checkbox shows completion status
- Title and description
- Ordered list (top to bottom = priority)
- Progress bar shows percentage complete

### Adding Steps (Admin Only)

1. In feature detail view, click **Add Step**
2. Fill in:
   - **Title:** Short task description (required)
   - **Description:** Additional details (optional)
3. Click **Add**
4. Step is added with status "todo"

**Example Steps for "Add password reset functionality":**
1. Create reset token generation function
2. Set up email template for reset link
3. Create reset password API endpoint
4. Add frontend reset password form
5. Add token expiration validation
6. Write unit tests
7. Write integration tests

### Marking Steps Complete (Admin Only)

1. Click the **checkbox** next to a step
2. Step status changes from "todo" to "done"
3. Progress bar updates automatically
4. Click again to unmark

**Tip:** Mark steps as done immediately upon completion to keep progress accurate.

### Reordering Steps (Admin Only)

1. Steps can be reordered if needed (feature may require development)
2. Current version: Delete and recreate in desired order
3. Future version: Drag-and-drop reordering

### Deleting Steps (Admin Only)

1. Click **Delete** icon next to step
2. Confirm deletion
3. Progress bar updates automatically

---

## Team Collaboration

### Adding Comments

All users can add comments to features:

1. Open feature detail view
2. Scroll to **Comments** section
3. Type your comment in the text field
4. Click **Send** button
5. Comment appears with your name and timestamp

**Good Uses for Comments:**
- Progress updates ("Completed database migration")
- Questions ("Should this work for mobile devices?")
- Blockers ("Waiting for API credentials")
- Design decisions ("Using JWT for authentication")
- Test results ("All tests passing")
- Links to related resources

**Example Comments:**
```
"Started implementation. Created database schema for reset tokens."

"Question: Should the reset link work on mobile app or web only?"

"Blocked: Need approval for email service provider."

"Update: Email service configured. Moving forward with implementation."

"Testing complete. Found one edge case - handling expired tokens. 
Will fix tomorrow."

"Deployed to staging. Ready for QA review."
```

### Viewing Comment History

- Comments are displayed in chronological order (oldest first)
- Each comment shows:
  - User name and avatar
  - Comment text
  - Timestamp
- Full conversation thread visible

### Deleting Comments

- **Your own comments:** Click delete icon
- **Others' comments:** Admin only
- Deleted comments are permanently removed

**Best Practice:** Edit by adding a new comment rather than deleting, to preserve conversation history.

---

## Workflows & Best Practices

### Feature Planning Workflow

**Step 1: Create Feature**
- Admin creates feature with clear title and description
- Sets appropriate priority
- Status: "Planned"

**Step 2: Break Down Into Steps**
- Admin adds implementation steps
- Each step is a specific, actionable task
- Steps ordered by logical sequence

**Step 3: Start Development**
- Admin changes status to "In Development"
- Team members add comments with updates
- Steps are marked as completed

**Step 4: Testing**
- When implementation done, change status to "Testing"
- QA team tests the feature
- Issues are discussed in comments
- Failed tests → back to "In Development"

**Step 5: Completion**
- All tests pass
- Feature deployed to production
- Status changed to "Completed"
- Final comment added with deployment notes

### Priority Management

**Use Critical (🔴) For:**
- Security vulnerabilities
- Production bugs affecting users
- System outages
- Blockers preventing other work

**Use High (🟠) For:**
- Important features with near-term deadlines
- Customer commitments
- Performance improvements
- Major enhancements

**Use Medium (🟡) For:**
- Standard features in backlog
- Regular improvements
- Refactoring work
- Tech debt

**Use Low (🟢) For:**
- Nice-to-have enhancements
- UI polish
- Documentation
- Future optimizations

### Status Best Practices

**Planned:**
- Feature is defined but work hasn't started
- All requirements documented
- Steps may or may not be defined yet

**In Development:**
- Active work in progress
- At least one step completed or in progress
- Regular comment updates recommended

**Testing:**
- Implementation complete
- QA/testing in progress
- No new development unless bugs found

**Completed:**
- All steps done
- All tests passed
- Deployed to production
- Feature working as expected

**On Hold:**
- Work paused for any reason
- Could be: blocked, deprioritized, waiting for dependencies
- Should have a comment explaining why
- Can resume to any status later

### Communication Best Practices

**Daily Updates:**
- Add comment when starting work on feature
- Update when completing significant steps
- Note any blockers immediately

**Weekly Reviews:**
- Review all "In Development" features
- Update status as needed
- Address any stalled features

**Team Coordination:**
- Use comments to ask questions
- Tag blockers clearly
- Share design decisions
- Link to relevant documents or PRs

---

## Filtering & Search

### Filter by Status

1. Click **Status** dropdown in filters section
2. Select status (planned, in_development, testing, completed, on_hold)
3. Table updates to show only matching features
4. Select "All Status" to clear filter

**Common Filters:**
- **In Development** - What's actively being worked on
- **Testing** - What needs QA attention
- **Completed** - Recent accomplishments

### Filter by Priority

1. Click **Priority** dropdown
2. Select priority level
3. Table updates to show only matching features
4. Select "All Priorities" to clear filter

**Common Filters:**
- **Critical** - Urgent items requiring immediate attention
- **High** - Near-term priorities

### Combine Filters

You can combine status and priority filters:
- Example: "In Development" + "High" = Active high-priority work
- Example: "Planned" + "Critical" = Urgent work not yet started

### Pagination

- Default: 10 features per page
- Change rows per page: 5, 10, 25, or 50
- Use page navigation to browse

---

## Tips & Tricks

### For Project Managers

1. **Review Dashboard Daily:** Check status distribution
2. **Monitor Progress Bars:** Identify stalled features
3. **Use Filters:** Focus on critical/high priority items
4. **Check Target Dates:** Identify upcoming deadlines
5. **Read Comments:** Stay informed on blockers

### For Developers

1. **Check "Planned" Features:** See upcoming work
2. **Mark Steps as Done:** Keep progress visible
3. **Add Comments:** Share implementation notes
4. **Ask Questions:** Use comments to clarify requirements
5. **Link to PRs:** Add GitHub/GitLab PR links in comments

### For QA/Testers

1. **Filter by "Testing":** Find features ready for QA
2. **Add Test Results:** Comment with findings
3. **Report Bugs:** Comment with reproduction steps
4. **Approve Features:** Add comment when tests pass

### For Product Owners

1. **Create Clear Features:** Include all requirements
2. **Set Priorities:** Help team focus on what matters
3. **Set Target Dates:** Communicate deadlines
4. **Review Completed:** See what was delivered

---

## Troubleshooting

### I can't create features

**Cause:** You're not an admin user
**Solution:** Only admins can create features. Request admin access or ask an admin to create the feature for you.

### I can't see the module

**Cause:** You don't have access to the Development Planning module
**Solution:** Contact your system administrator to grant you access.

### Features list is empty

**Cause:** No features created yet, or filters are too restrictive
**Solution:** 
1. Clear all filters (select "All Status" and "All Priorities")
2. If still empty, no features exist - admin needs to create some

### Progress bar not updating

**Cause:** Browser cache issue
**Solution:** Refresh the page (F5 or Ctrl+R)

### Can't delete my comment

**Cause:** Comment was created by someone else
**Solution:** You can only delete your own comments. Contact an admin to delete others' comments.

### Target date not showing

**Cause:** No target date was set
**Solution:** Target dates are optional. Admin can edit feature to add one.

### Email not showing for comment author

**Cause:** System issue (should be fixed in v1.0.1)
**Solution:** Update to latest version of the system.

---

## Keyboard Shortcuts

Currently no keyboard shortcuts are implemented. This may be added in future versions.

---

## Mobile Access

The Development Planning module is responsive and works on mobile devices:
- View features and details
- Read comments
- Add comments
- Admin functions (creating features, managing steps) work best on desktop

---

## Getting Help

**Documentation:**
- [README](./README.md) - Module overview and quick start
- [Technical Guide](./technical-guide.md) - For developers

**Support:**
- Contact your system administrator
- Check the main system documentation
- Review training materials

---

## Future Enhancements

Planned improvements for future versions:
- Drag-and-drop step reordering
- File attachments for features
- @mentions in comments
- Email notifications
- Advanced search
- Export features to CSV/PDF
- Time tracking per feature
- Burndown charts
- Sprint planning integration

---

**Document Version:** 1.0.1
**Last Updated:** 2025-11-20
**Feedback:** Report issues or suggestions to your system administrator
