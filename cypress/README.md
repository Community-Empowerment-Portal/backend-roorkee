# Cypress Test Suite Documentation

This document provides a detailed explanation of each Cypress test file, what it's testing, and how to effectively use and maintain these tests.

## Overview of Test Files

The Cypress test suite consists of the following main test files:

1. [admin_analytics.cy.js](#admin_analyticscy.js) - Tests analytics and reporting features
2. [admin_dashboard.cy.js](#admin_dashboardcyjs) - Tests dashboard UI and navigation 
3. [admin_layout_customization.cy.js](#admin_layout_customizationcyjs) - Tests layout management
4. [admin_rbac.cy.js](#admin_rbaccyjs) - Tests role-based access control
5. [admin_resource_management.cy.js](#admin_resource_managementcyjs) - Tests resource management
6. [admin_state_department.cy.js](#admin_state_departmentcyjs) - Tests state/department management
7. [admin_user_management.cy.js](#admin_user_managementcyjs) - Tests user management
8. [Allschemes.cy.js](#allschemescyjs) - Tests scheme management

## Detailed Test File Descriptions

### admin_analytics.cy.js

**Purpose:** Tests the analytics and reporting functionality in the admin interface.

**What it tests:**
- User event tracking and analysis
- Popular content analytics
- Report generation and export capabilities

**Key features tested:**
- Filtering user events by date and event type
- Viewing detailed analytics for user activities
- Exporting analytics data to CSV
- Testing report visualization elements

### admin_dashboard.cy.js

**Purpose:** Tests core admin dashboard functionality and UI elements.

**What it tests:**
- Site header and branding verification
- Navigation through custom app groups
- Model search functionality
- Quick actions and breadcrumb navigation
- Dashboard statistics and UI elements

**Key features tested:**
- Admin site header and title verification
- Navigation between different app sections
- Search functionality for users and schemes
- Recent actions sidebar functionality
- Breadcrumb navigation

### admin_layout_customization.cy.js

**Purpose:** Tests the layout management and customization capabilities.

**What it tests:**
- LayoutItem CRUD operations
- Item ordering and activation/deactivation
- Layout preview functionality
- Permission-based layout management

**Key features tested:**
- Creating, editing, and deleting layout items
- Changing layout item order directly in list view
- Toggling activation status of layout items
- Testing layout preview functionality
- Verifying permission restrictions for different user roles

### admin_rbac.cy.js

**Purpose:** Tests role-based access control and permission management.

**What it tests:**
- Group creation with view permissions
- User access with different permission levels
- Permission inheritance and validation

**Key features tested:**
- Creating groups with specific permissions
- Setting up users with different permission levels
- Verifying access restrictions for non-staff users
- Testing permission escalation
- Cleaning up test users and groups

### admin_resource_management.cy.js

**Purpose:** Tests management of various resources like FAQs, Banners, and Announcements.

**What it tests:**
- CRUD operations for FAQs, Banners, and Announcements
- Resource activation/deactivation
- Bulk operations on resources
- Common resource management functions

**Key features tested:**
- Creating, editing, and deleting resources
- Changing resource order and activation status
- Bulk actions on multiple resources
- Filtering resources by active status

### admin_state_department.cy.js

**Purpose:** Tests the management of states and departments.

**What it tests:**
- CRUD operations for states and departments
- Relationships between states and departments
- Permission-based access to state/department management

**Note:** This appears to be incomplete or a template for future tests.

### admin_user_management.cy.js

**Purpose:** Tests comprehensive user management features.

**What it tests:**
- User CRUD operations
- Group and permission assignments
- Profile field management
- User status management and actions
- Password management

**Key features tested:**
- Creating, viewing, editing, and deleting users
- Assigning users to groups and permissions
- Managing profile fields
- Activating/deactivating users
- Bulk user actions
- Password change functionality

### Allschemes.cy.js

**Purpose:** Tests scheme management functionality.

**What it tests:**
- Scheme creation and relationships
- Scheme status management and filtering
- Permission-based access control
- Export functionality

**Key features tested:**
- Creating supporting components (states, departments, documents)
- Creating and editing schemes with relationships
- Testing scheme status changes
- Scheme filtering and search
- Validation of scheme data
- Permission-based access control
- Export functionality

## Test Workflow Documentation

### Running the Tests

To run all tests:
```bash
npx cypress run
```

To run a specific test file:
```bash
npx cypress run --spec "cypress/e2e/admin_dashboard.cy.js"
```

To open Cypress Test Runner:
```bash
npx cypress open
```

### Common Issues and Troubleshooting

1. **Authentication Issues**
   - Make sure test users exist in the system
   - Check admin-test-users.json for correct credentials
   - Verify login/logout commands work properly

2. **Selector Issues**
   - Use more specific selectors when elements aren't found
   - Add proper waiting for dynamic elements
   - Consider using data-testid attributes for more stable selection

3. **Test Data Issues**
   - Ensure test data is properly initialized before tests
   - Clean up test data after tests complete
   - Use unique identifiers for test data to prevent collisions

4. **Permission Issues**
   - Verify user roles and permissions are properly set up
   - Check that permission tests account for different user types
   - Ensure proper cleanup of test users and permissions

### Maintenance Best Practices

1. **Adding New Tests**
   - Follow the existing pattern for similar functionality
   - Use the helper functions in support files
   - Add proper documentation and comments

2. **Updating Existing Tests**
   - Be cautious when changing selectors or test data
   - Test changes thoroughly before committing
   - Update documentation when behavior changes

3. **Test Support Files**
   - Reuse commands and helpers from support files
   - Add new common functionality to support files
   - Document new commands and helpers

