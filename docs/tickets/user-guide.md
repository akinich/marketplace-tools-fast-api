# Ticket System Module - User Guide

**Version:** 1.0.1
**Audience:** Farm Operators, Staff Members, System Users

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating a Ticket](#creating-a-ticket)
3. [Viewing Tickets](#viewing-tickets)
4. [Managing Your Tickets](#managing-your-tickets)
5. [Working with Comments](#working-with-comments)
6. [Understanding Ticket Status](#understanding-ticket-status)
7. [Understanding Priority Levels](#understanding-priority-levels)
8. [Admin Functions](#admin-functions)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing the Ticket System

1. Log in to the Marketplace ERP Tools
2. Navigate to **Tickets** from the main menu
3. You'll see the "All Tickets" view showing all system tickets

### What Can You Do?

**All Users:**
- ✅ Create tickets for issues, feature requests, or upgrade suggestions
- ✅ View all tickets in the system
- ✅ View your own tickets
- ✅ Add comments to open tickets
- ✅ Update your own tickets (before they're closed)
- ✅ Edit/delete your own comments

**Admins:**
- ✅ Everything above, plus:
- ✅ Set/change ticket priority
- ✅ Update ticket status
- ✅ Close tickets
- ✅ Modify any ticket or comment

---

## Creating a Ticket

### When to Create a Ticket

**Issue Tickets:**
- Something isn't working correctly
- You encounter an error
- System behaving unexpectedly
- Equipment or module malfunction

**Feature Request Tickets:**
- You have an idea for new functionality
- You want a new report or view
- You need integration with another system
- You want to automate a manual process

**Upgrade Tickets:**
- Existing feature could work better
- UI could be more user-friendly
- Process could be more efficient
- Performance improvements needed

**Other Tickets:**
- General feedback
- Questions
- Documentation requests
- Anything not fitting other categories

### Step-by-Step: Creating a Ticket

1. **Click "Create Ticket" button**
   - Located at the top of the tickets page

2. **Fill in the form:**

   **Title** (required)
   - Keep it brief but descriptive
   - Max 200 characters
   - Good: "Feed dispenser stuck in Tank 3"
   - Bad: "Problem with tank"

   **Description** (required)
   - Provide detailed information
   - Include relevant context
   - For issues: steps to reproduce
   - For requests: desired outcome

   **Ticket Type** (required)
   - Issue
   - Feature Request
   - Upgrade
   - Others

3. **Click "Submit"**
   - Your ticket is created with "Open" status
   - You'll be redirected to the ticket detail page
   - Admins will be notified

### Example: Creating an Issue Ticket

```
Title: Water quality sensor not recording data in Biofloc Tank 5

Description:
Since this morning (Nov 20, 9:00 AM), the water quality sensor in
Biofloc Tank 5 is not recording any data. The last successful reading
was at 8:45 AM showing pH 7.2, DO 6.5 mg/L, Temperature 28°C.

Steps that were already tried:
- Refreshed the dashboard
- Checked sensor power connection
- Verified tank is active in system

Impact: Unable to monitor water parameters for this tank.
Tank ID: bf-tank-005
Batch: BF-2025-003
```

---

## Viewing Tickets

### All Tickets View

**Default View:**
- Shows all tickets in the system
- 10 tickets per page
- Most recent first
- Color-coded status indicators

**Filtering Options:**

**By Type:**
- Issue
- Feature Request
- Upgrade
- Others
- (Clear filter to see all)

**By Status:**
- Open - Not yet started
- In Progress - Being worked on
- Resolved - Fixed/implemented
- Closed - Complete
- (Clear filter to see all)

**By Priority:**
- Critical - Urgent, system-critical
- High - Important, significant impact
- Medium - Standard priority
- Low - Minor, nice-to-have
- (Clear filter to see all)

**Navigation:**
- Use "Previous" and "Next" buttons
- Shows "Page X of Y"
- Click any ticket to view details

### Ticket Information Displayed

Each ticket in the list shows:
- **ID Number** - Unique identifier (#42)
- **Title** - Brief description
- **Type** - Issue, Feature Request, etc.
- **Status** - Current state (color-coded chip)
- **Priority** - If assigned by admin
- **Created By** - User name and email
- **Created Date** - When submitted
- **Comment Count** - Number of comments

**Status Color Coding:**
- 🔵 Blue = Open
- 🟡 Yellow = In Progress
- 🟢 Green = Resolved
- ⚫ Gray = Closed

---

## Managing Your Tickets

### Viewing Only Your Tickets

1. Click **"My Tickets"** tab
2. See only tickets you created
3. Use same filters as All Tickets view
4. Track status of your submissions

### Updating Your Ticket

**Before Ticket is Closed:**

1. Open your ticket
2. Click **"Edit Ticket"** button (if available)
3. Update:
   - Title
   - Description
   - Type
4. Click "Save"

**Note:** You cannot change:
- Status (admin only)
- Priority (admin only)
- Created date
- Ticket ID

**After Ticket is Closed:**
- Cannot be modified
- Cannot add comments
- Read-only view

### When to Update a Ticket

- Provide additional information discovered
- Correct mistakes in description
- Clarify requirements
- Change ticket type if miscategorized
- Add context that was missed

---

## Working with Comments

### Viewing Comments

1. Click on any ticket to view details
2. Scroll down to "Comments" section
3. Comments show in chronological order (oldest first)
4. Each comment displays:
   - Commenter name and email
   - Comment text
   - Timestamp

### Adding a Comment

**Requirements:**
- Ticket must be open (not closed)
- You must be authenticated

**Steps:**
1. Open the ticket detail page
2. Scroll to "Add Comment" section
3. Type your comment in the text box
4. Click "Add Comment"
5. Comment appears immediately

**When to Comment:**
- Answer admin questions
- Provide additional details
- Share updates about the issue
- Confirm you tested the fix
- Report related observations

**Example Comments:**
```
"I tested the fix in Tank 5 and it's working perfectly now. Thanks!"

"This also affects Tank 7, not just Tank 5. Same symptoms."

"The issue started after we updated the feeding schedule yesterday."

"Can confirm this feature would save us about 2 hours per week."
```

### Editing Your Comment

1. Find your comment in the thread
2. Click **"Edit"** icon (pencil)
3. Modify the text
4. Click "Save"

**Note:**
- You can only edit your own comments
- Cannot edit after ticket is closed
- Admins can edit any comment

### Deleting Your Comment

1. Find your comment in the thread
2. Click **"Delete"** icon (trash)
3. Confirm deletion
4. Comment is permanently removed

**Note:**
- You can only delete your own comments
- Cannot delete after ticket is closed
- Admins can delete any comment

---

## Understanding Ticket Status

### Status Definitions

**Open (Blue)**
- Ticket has been created
- Waiting for admin review
- Not yet being worked on
- Default status for new tickets

**What this means for you:**
- Wait for admin response
- Check back periodically
- May be asked for more information

---

**In Progress (Yellow)**
- Admin is actively working on the issue
- Investigation underway
- Development in progress
- Testing may be happening

**What this means for you:**
- Resolution is being worked on
- Monitor comments for updates
- Be ready to answer questions
- May be asked to test fix

---

**Resolved (Green)**
- Issue has been fixed
- Feature has been implemented
- Problem is addressed
- Waiting for your confirmation

**What this means for you:**
- Test the fix/feature
- Confirm it works
- Comment if still having issues
- Admin may close if confirmed

---

**Closed (Gray)**
- Ticket is complete
- Final status
- No further action needed
- Cannot be modified

**What this means for you:**
- Issue is resolved
- Feature is delivered
- Can be referenced later
- Create new ticket if issue returns

### Status Workflow

```
┌──────┐
│ OPEN │ ← Ticket created
└──┬───┘
   ↓
┌───────────────┐
│ IN PROGRESS   │ ← Admin working on it
└───────┬───────┘
        ↓
┌──────────┐
│ RESOLVED │ ← Fix implemented
└────┬─────┘
     ↓
┌────────┐
│ CLOSED │ ← Confirmed complete
└────────┘

Note: Admins can close tickets at any stage
```

---

## Understanding Priority Levels

### What Priority Means

Priority indicates **urgency and importance**, set by administrators based on:
- Impact on operations
- Number of users affected
- Safety or revenue implications
- Workaround availability

### Priority Levels

**Critical (Red)**
- System is down or unusable
- Major functionality broken
- Revenue loss occurring
- Safety issue
- Immediate action required

**Example:** "Entire biofloc module not accessible"

---

**High (Orange)**
- Significant functionality impaired
- Multiple users affected
- Operations hindered but not stopped
- Workaround may exist

**Example:** "Cannot add new feeding sessions in Tank 5"

---

**Medium (Yellow)**
- Moderate impact
- Single user or minor feature
- Standard priority
- Scheduled for normal processing

**Example:** "Report export to Excel formatting issue"

---

**Low (Green)**
- Minor issue
- Cosmetic problems
- Nice-to-have features
- Minimal impact

**Example:** "Button text color could be darker for better visibility"

---

**Unassigned (No Color)**
- Not yet reviewed by admin
- Priority to be determined
- All new tickets start here

---

## Admin Functions

**Note:** These features are only available to users with Admin role.

### Setting Priority

1. Open any ticket
2. Find "Admin Controls" section
3. Click "Set Priority" button
4. Select priority level:
   - Low
   - Medium
   - High
   - Critical
5. Click "Update"
6. Priority is saved and displayed

**When to Set Priority:**
- After reviewing new ticket
- When situation changes
- Based on impact assessment
- To communicate urgency

---

### Updating Status

1. Open any ticket
2. Find "Admin Controls" section
3. Click "Update Status" button
4. Select new status:
   - Open
   - In Progress
   - Resolved
   - (Use "Close Ticket" for closing)
5. Click "Update"
6. Status is saved and displayed

**Status Update Guidelines:**
- Set to "In Progress" when you start work
- Set to "Resolved" when fix is ready
- Let user confirm before closing
- Document status changes in comments

---

### Closing a Ticket

1. Open any ticket
2. Find "Admin Controls" section
3. Click "Close Ticket" button
4. Optionally add closing comment:
   - Explain resolution
   - Provide reference numbers
   - Document final outcome
5. Click "Close"
6. Ticket status becomes "Closed"
7. Ticket becomes read-only

**When to Close:**
- Issue is fully resolved
- Feature is implemented and tested
- User has confirmed fix
- Ticket is duplicate or invalid
- Request is withdrawn

**Closing Comment Examples:**
```
"Fixed sensor connection in Tank 5. Readings now displaying correctly.
Verified at 2:15 PM on Nov 20."

"Feature implemented in v1.5.0 release. Available in production."

"Duplicate of ticket #38. Closing this one."

"Unable to reproduce issue after multiple attempts. Closing, but please
create new ticket if problem recurs."
```

---

## Best Practices

### Creating Effective Tickets

**DO:**
- ✅ Use clear, descriptive titles
- ✅ Provide complete context
- ✅ Include steps to reproduce (issues)
- ✅ Specify desired outcome (requests)
- ✅ Include relevant IDs (tanks, batches, etc.)
- ✅ Attach screenshots if helpful
- ✅ Choose correct ticket type

**DON'T:**
- ❌ Use vague titles like "It's broken"
- ❌ Skip important details
- ❌ Assume admin knows the context
- ❌ Create duplicate tickets
- ❌ Use all caps or excessive punctuation
- ❌ Include sensitive passwords

### Managing Your Tickets

**DO:**
- ✅ Check for updates regularly
- ✅ Respond promptly to questions
- ✅ Test fixes when asked
- ✅ Confirm when resolved
- ✅ Provide requested information
- ✅ Keep ticket updated with new info

**DON'T:**
- ❌ Ignore admin comments
- ❌ Create new ticket for same issue
- ❌ Expect instant resolution
- ❌ Reopen closed tickets unnecessarily
- ❌ Spam comments

### Using Comments Effectively

**DO:**
- ✅ Be specific and concise
- ✅ Stay on topic
- ✅ Be professional and respectful
- ✅ Provide requested details
- ✅ Update on status changes
- ✅ Share relevant findings

**DON'T:**
- ❌ Go off-topic
- ❌ Use comments for new issues
- ❌ Be rude or demanding
- ❌ Post duplicate information
- ❌ Include unrelated requests

### For Admins

**DO:**
- ✅ Review new tickets daily
- ✅ Set priority promptly
- ✅ Update status as work progresses
- ✅ Ask clarifying questions
- ✅ Keep users informed
- ✅ Document resolutions
- ✅ Add closing comments

**DON'T:**
- ❌ Let tickets go stale
- ❌ Close without resolution
- ❌ Ignore user questions
- ❌ Skip status updates
- ❌ Provide vague responses

---

## Troubleshooting

### "Cannot Create Ticket"

**Possible Causes:**
- Not logged in
- Session expired
- Missing required fields
- Server connection issue

**Solutions:**
1. Verify you're logged in
2. Refresh the page
3. Fill in all required fields (title, description, type)
4. Check internet connection
5. Contact admin if persists

---

### "Cannot Add Comment"

**Possible Causes:**
- Ticket is closed
- Not logged in
- Empty comment field
- Permission issue

**Solutions:**
1. Check ticket status (closed tickets are read-only)
2. Verify you're logged in
3. Ensure comment has content
4. Refresh page and try again

---

### "Cannot See My Tickets"

**Possible Causes:**
- No tickets created yet
- Wrong filter applied
- Display issue
- Database connection

**Solutions:**
1. Verify you've created tickets
2. Clear all filters
3. Refresh the page
4. Check "All Tickets" to confirm they exist

---

### "Ticket Not Updating"

**Possible Causes:**
- Cache not refreshed
- Permission issue (can't update others' tickets)
- Ticket is closed
- Validation error

**Solutions:**
1. Refresh the browser
2. Verify it's your ticket
3. Check if ticket is closed
4. Ensure all fields are valid
5. Clear browser cache

---

### "Priority/Status Not Showing"

**Possible Causes:**
- Not yet assigned by admin
- Display issue
- Data not loaded

**Solutions:**
1. Refresh the page
2. Priority may not be set yet (normal for new tickets)
3. Check back later
4. Contact admin if urgent

---

### Getting Help

**If you encounter issues with the ticket system:**

1. **Check this guide** - Common solutions above
2. **Ask an admin** - They can check logs
3. **Create a ticket** - Report issue with ticket system itself
   - Type: Issue
   - Title: "Ticket system: [describe problem]"
   - Describe what you were trying to do
4. **Check system status** - May be maintenance

**Include in your report:**
- What you were trying to do
- What happened instead
- Any error messages
- Browser and device info
- Screenshot if applicable

---

## Quick Reference

### Ticket Lifecycle

```
1. User creates ticket → Status: Open, Priority: Unassigned
2. Admin reviews → Sets priority
3. Admin starts work → Status: In Progress
4. Admin implements fix → Status: Resolved
5. User confirms → Admin closes → Status: Closed
```

### Permission Matrix

| Action | Regular User | Admin |
|--------|-------------|-------|
| Create ticket | ✅ | ✅ |
| View tickets | ✅ | ✅ |
| Update own ticket | ✅ | ✅ |
| Update any ticket | ❌ | ✅ |
| Set priority | ❌ | ✅ |
| Change status | ❌ | ✅ |
| Close ticket | ❌ | ✅ |
| Add comment | ✅ | ✅ |
| Edit own comment | ✅ | ✅ |
| Edit any comment | ❌ | ✅ |
| Delete own comment | ✅ | ✅ |
| Delete any comment | ❌ | ✅ |

### Status Colors

- 🔵 **Open** - New, awaiting review
- 🟡 **In Progress** - Being worked on
- 🟢 **Resolved** - Fixed, awaiting confirmation
- ⚫ **Closed** - Complete, finalized

### Priority Colors

- 🔴 **Critical** - Urgent, immediate action
- 🟠 **High** - Important, priority processing
- 🟡 **Medium** - Standard, normal queue
- 🟢 **Low** - Minor, when time permits

---

**Need more help?** Contact your system administrator or create a ticket!
