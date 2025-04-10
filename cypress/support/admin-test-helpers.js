// Admin Test Helpers
// Utility functions for managing test users and permissions in admin tests

/**
 * Load the admin test users configuration
 * @returns {Object} The test users configuration
 */
function loadTestUsersConfig() {
  return cy.fixture('admin-test-users.json').then(config => {
    return config;
  });
}

/**
 * Setup a test user with the specified role
 * @param {String} role - The role of the user (admin, editor, viewer)
 * @returns {Object} The user configuration for the specified role
 */
function setupTestUser(role) {
  return loadTestUsersConfig().then(config => {
    const userConfig = config.users[role];
    const permissionsConfig = config.permissions[role];
    
    // Check if the user exists, if not create it
    cy.request({
      method: 'POST',
      url: '/api/auth/check-user-exists/',
      body: { username: userConfig.username },
      failOnStatusCode: false
    }).then(response => {
      if (response.status === 404 || response.body.exists === false) {
        cy.log(`Test user ${userConfig.username} does not exist, creating...`);
        
        // Admin logs in to create the user
        cy.admin_login(config.users.admin.username, config.users.admin.password);
        
        // Create the user
        cy.visit('/admin/communityEmpowerment/customuser/add/');
        cy.fillAdminForm({ 'username': userConfig.username }, 'input');
        cy.fillAdminForm({ 'email': userConfig.email }, 'input');
        cy.fillAdminForm({ 'first_name': userConfig.firstName }, 'input');
        cy.fillAdminForm({ 'last_name': userConfig.lastName }, 'input');
        cy.fillAdminForm({ 'password1': userConfig.password }, 'input');
        cy.fillAdminForm({ 'password2': userConfig.password }, 'input');
        
        // Set staff status
        cy.fillAdminForm({ 'is_staff': permissionsConfig.isStaff }, 'checkbox');
        
        // Set superuser status
        cy.fillAdminForm({ 'is_superuser': permissionsConfig.isSuperuser }, 'checkbox');
        
        // Set active status
        cy.fillAdminForm({ 'is_active': permissionsConfig.isActive }, 'checkbox');
        
        // Save the user
        cy.save();
        
        // If the user needs specific permissions or groups, assign them
        if (permissionsConfig.groups.length > 0 || permissionsConfig.userPermissions.length > 0) {
          cy.contains('tr', userConfig.username).find('th a').click();
          
          // Assign groups if specified
          if (permissionsConfig.groups.length > 0) {
            permissionsConfig.groups.forEach(group => {
              cy.get('#id_groups_from option').contains(group).then($option => {
                if ($option.length) {
                  cy.wrap($option).click();
                  cy.get('#id_groups_add_link').click();
                }
              });
            });
          }
          
          // Assign individual permissions if specified
          if (permissionsConfig.userPermissions.length > 0) {
            permissionsConfig.userPermissions.forEach(permission => {
              cy.get('#id_user_permissions_from option').contains(permission).then($option => {
                if ($option.length) {
                  cy.wrap($option).click();
                  cy.get('#id_user_permissions_add_link').click();
                }
              });
            });
          }
          
          // Save changes
          cy.save();
        }
        
        // Logout admin
        cy.admin_logout();
      } else {
        cy.log(`Test user ${userConfig.username} already exists`);
      }
    });
    
    return { userConfig, permissionsConfig };
  });
}

/**
 * Verify user permissions against expected UI elements
 * @param {String} role - The role of the user (admin, editor, viewer)
 * @param {String} modelName - The name of the model being checked
 */
function verifyUserPermissions(role, modelName) {
  return loadTestUsersConfig().then(config => {
    const expectedUi = config.expectedUi[role];
    
    // Check if the user has access to add new items
    if (typeof expectedUi.hasAddButtons === 'object') {
      // Role has specific permissions per model
      const shouldHaveAddButton = expectedUi.hasAddButtons[modelName] || false;
      cy.checkPermission('a.addlink', shouldHaveAddButton, 
        `${role} ${shouldHaveAddButton ? 'should' : 'should not'} have "Add" button for ${modelName}`);
    } else {
      // Role has the same permission for all models
      cy.checkPermission('a.addlink', expectedUi.hasAddButtons, 
        `${role} ${expectedUi.hasAddButtons ? 'should' : 'should not'} have "Add" button for ${modelName}`);
    }
    
    // Check for any records to test edit/delete permissions
    cy.get('#result_list tbody tr:first-child th a').then($link => {
      if ($link.length) {
        cy.wrap($link).click();
        
        // Check if the user can save changes
        cy.checkPermission('input[name="_save"]', expectedUi.hasSaveButtons, 
          `${role} ${expectedUi.hasSaveButtons ? 'should' : 'should not'} be able to save ${modelName}`);
        
        // Check if the user can delete items
        cy.checkPermission('a:contains("Delete")', expectedUi.hasDeleteButtons, 
          `${role} ${expectedUi.hasDeleteButtons ? 'should' : 'should not'} be able to delete ${modelName}`);
        
        // Go back to list
        cy.visit(`/admin/communityEmpowerment/${modelName}/`);
      }
    });
    
    // Check if the user can use bulk actions
    cy.checkPermission('select[name="action"]', expectedUi.hasBulkActions, 
      `${role} ${expectedUi.hasBulkActions ? 'should' : 'should not'} have bulk actions for ${modelName}`);
    
    // Check inline editing if applicable
    if (expectedUi.canEditInlineFields) {
      cy.get('#result_list tbody tr:first-child').then($row => {
        if ($row.length) {
          if (typeof expectedUi.canEditInlineFields === 'object') {
            // Check specific field editability
            const fieldKey = `${modelName}.is_active`;
            const shouldBeEditable = expectedUi.canEditInlineFields[fieldKey] || false;
            
            cy.get('input[name*="is_active"]').then($input => {
              if ($input.length) {
                const isDisabled = $input.prop('disabled');
                cy.log(`${role} ${!isDisabled === shouldBeEditable ? 'correctly' : 'incorrectly'} ${shouldBeEditable ? 'can' : 'cannot'} edit ${fieldKey}`);
              }
            });
          } else {
            // All fields should be editable or non-editable
            cy.get('input[name*="is_active"], input[name*="order"]').then($inputs => {
              if ($inputs.length) {
                $inputs.each((i, el) => {
                  const isDisabled = Cypress.$(el).prop('disabled');
                  cy.log(`${role} ${!isDisabled === expectedUi.canEditInlineFields ? 'correctly' : 'incorrectly'} ${expectedUi.canEditInlineFields ? 'can' : 'cannot'} edit field`);
                });
              }
            });
          }
        }
      });
    }
  });
}

/**
 * Perform a comprehensive permission check for a given model
 * @param {String} modelName - The name of the model to check
 * @param {Array} roles - The roles to check (defaults to ['admin', 'editor', 'viewer'])
 */
function checkModelPermissions(modelName, roles = ['admin', 'editor', 'viewer']) {
  roles.forEach(role => {
    // Set up user and log in
    setupTestUser(role).then(({userConfig}) => {
      cy.admin_login(userConfig.username, userConfig.password);
      
      // Visit the model list page
      cy.visit(`/admin/communityEmpowerment/${modelName}/`);
      
      // Verify permissions for this role and model
      verifyUserPermissions(role, modelName);
      
      // Logout
      cy.admin_logout();
    });
  });
}

/**
 * Create a test record for a given model
 * @param {String} modelName - The model name
 * @param {Object} data - The data for the new record
 * @returns {String} The identifier of the created record
 */
function createTestRecord(modelName, data = {}) {
  return loadTestUsersConfig().then(config => {
    // Login as admin
    cy.admin_login(config.users.admin.username, config.users.admin.password);
    
    // Get default test data for this model if available
    const defaultKey = Object.keys(config.testDefaults).find(key => key.toLowerCase().includes(modelName.toLowerCase()));
    const defaultTitle = defaultKey ? config.testDefaults[defaultKey] : `Test ${modelName}`;
    
    // Generate a unique identifier
    const timestamp = Date.now();
    const title = data.title || `${defaultTitle} ${timestamp}`;
    
    // Visit the add page
    cy.visit(`/admin/communityEmpowerment/${modelName}/add/`);
    
    // Fill form based on model type
    switch(modelName) {
      case 'faq':
        cy.fillAdminForm({ 'question': title }, 'input');
        cy.fillAdminForm({ 'answer': data.answer || 'Test answer' }, 'textarea');
        cy.fillAdminForm({ 'order': data.order || '10' }, 'input');
        cy.fillAdminForm({ 'is_active': 'is_active' in data ? data.is_active : true }, 'checkbox');
        break;
        
      case 'banner':
      case 'announcement':
        cy.fillAdminForm({ 'title': title }, 'input');
        cy.fillAdminForm({ 'description': data.description || 'Test description' }, 'textarea');
        cy.fillAdminForm({ 'is_active': 'is_active' in data ? data.is_active : true }, 'checkbox');
        break;
        
      case 'layoutitem':
        cy.fillAdminForm({ 'title': title }, 'input');
        cy.fillAdminForm({ 'content': data.content || 'Test content' }, 'textarea');
        cy.fillAdminForm({ 'order': data.order || '10' }, 'input');
        cy.fillAdminForm({ 'is_active': 'is_active' in data ? data.is_active : true }, 'checkbox');
        
        // Check if there's a layout_type field and fill it if present
        cy.get('body').then($body => {
          if ($body.find('select[name="layout_type"]').length) {
            cy.fillAdminForm({ 'layout_type': data.layout_type || 'text' }, 'select');
          }
          
          // Check if there's a section field and fill it if present
          if ($body.find('select[name="section"]').length) {
            cy.get('select[name="section"] option').then($options => {
              if ($options.length > 1) {
                cy.get('select[name="section"]').select(1);
              }
            });
          }
        });
        break;
        
      case 'state':
        cy.fillAdminForm({ 'name': title }, 'input');
        break;
        
      case 'department':
        cy.fillAdminForm({ 'name': title }, 'input');
        // Select a state if required
        cy.get('select[name="state"]').then($select => {
          if ($select.length) {
            cy.get('select[name="state"] option').then($options => {
              if ($options.length > 1) {
                cy.get('select[name="state"]').select(1);
              }
            });
          }
        });
        break;
        
      default:
        // For other models, try to fill in common fields
        if (data.title) cy.fillAdminForm({ 'title': title }, 'input');
        if (data.name) cy.fillAdminForm({ 'name': title }, 'input');
        if (data.description) cy.fillAdminForm({ 'description': data.description }, 'textarea');
        if ('is_active' in data) cy.fillAdminForm({ 'is_active': data.is_active }, 'checkbox');
    }
    
    // Save the record
    cy.save();
    
    // Logout admin
    cy.admin_logout();
    
    return title;
  });
}

/**
 * Delete a test record
 * @param {String} modelName - The model name
 * @param {String} identifier - The identifier of the record to delete
 */
function deleteTestRecord(modelName, identifier) {
  return loadTestUsersConfig().then(config => {
    // Login as admin
    cy.admin_login(config.users.admin.username, config.users.admin.password);
    
    // Go to the model list
    cy.visit(`/admin/communityEmpowerment/${modelName}/`);
    
    // Find and delete the record
    cy.get('body').then($body => {
      if ($body.text().includes(identifier)) {
        cy.contains('tr', identifier).find('th a').click();
        cy.contains('Delete').click();
        cy.contains("Yes, I'm sure").click();
      }
    });
    
    // Logout admin
    cy.admin_logout();
  });
}

// Export helper functions
export {
  loadTestUsersConfig,
  setupTestUser,
  verifyUserPermissions,
  checkModelPermissions,
  createTestRecord,
  deleteTestRecord
};

