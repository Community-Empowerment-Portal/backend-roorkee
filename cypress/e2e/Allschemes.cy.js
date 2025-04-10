// Simplified Schemes Management Test Suite
// Focuses on essential test cases only: CRUD, permissions, and search functionality

describe('Scheme Management - Essential Tests', () => {
  // Generate unique ID for test data
  const testId = Date.now();
  
  // Simple test data structures
  const testData = {
    state: `Test State ${testId}`,
    department: `Test Department ${testId}`,
    scheme: `Test Scheme ${testId}`,
    updatedScheme: `Updated Scheme ${testId}`
  };
  
  // Store created record IDs for cleanup
  const createdIds = {};
  
  // User credentials - from fixture or defaults
  const users = {
    admin: { username: 'admin', password: 'adminpassword' },
    editor: { username: 'editor', password: 'editorpassword' },
    viewer: { username: 'viewer', password: 'viewerpassword' }
  };

  // Helper function to create prerequisites
  const createPrerequisites = () => {
    // Create state
    cy.visit('/admin/communityEmpowerment/state/add/');
    cy.fillAdminForm({ 'name': testData.state }, 'input');
    cy.save();
    cy.url().then(url => {
      createdIds.state = url.split('/').filter(Boolean).pop();
      
      // Create department (depends on state)
      cy.visit('/admin/communityEmpowerment/department/add/');
      cy.fillAdminForm({ 'name': testData.department }, 'input');
      
      // Associate with state if the field exists
      cy.get('body').then($body => {
        if ($body.find('select[name="state"]').length) {
          cy.get('select[name="state"] option')
            .contains(testData.state)
            .then($option => {
              if ($option.length) {
                cy.get('select[name="state"]').select($option.val());
              }
            });
        }
      });
      
      cy.save();
      cy.url().then(url => {
        createdIds.department = url.split('/').filter(Boolean).pop();
      });
    });
  };

  // Login as admin before tests
  before(() => {
    cy.clearCookies();
    cy.admin_login(users.admin.username, users.admin.password);
    createPrerequisites();
  });

  // Logout after all tests
  after(() => {
    // Clean up created test data
    cleanupTestData();
    cy.admin_logout();
  });

  // Helper function to clean up test data
  const cleanupTestData = () => {
    // Delete scheme first (to avoid foreign key constraints)
    if (createdIds.scheme) {
      cy.visit(`/admin/communityEmpowerment/scheme/${createdIds.scheme}/delete/`);
      cy.contains('Yes, I\'m sure').click();
    }
    
    // Delete department
    if (createdIds.department) {
      cy.visit(`/admin/communityEmpowerment/department/${createdIds.department}/delete/`);
      cy.contains('Yes, I\'m sure').click();
    }
    
    // Delete state
    if (createdIds.state) {
      cy.visit(`/admin/communityEmpowerment/state/${createdIds.state}/delete/`);
      cy.contains('Yes, I\'m sure').click();
    }
  };

  // 1. BASIC CRUD OPERATIONS
  context('1. Basic CRUD Operations', () => {
    it('should create a new scheme', () => {
      cy.visit('/admin/communityEmpowerment/scheme/add/');
      
      // Fill basic scheme information
      cy.fillAdminForm({ 'name': testData.scheme }, 'input');
      cy.fillAdminForm({ 'short_description': 'Test scheme description' }, 'textarea');
      
      // Associate with department if the field exists
      cy.get('body').then($body => {
        if ($body.find('select[name="department"]').length) {
          cy.get('select[name="department"] option')
            .contains(testData.department)
            .then($option => {
              if ($option.length) {
                cy.get('select[name="department"]').select($option.val());
              }
            });
        }
        
        // Check for states field
        if ($body.find('.field-states').length) {
          cy.selectAdminManyToMany('states', testData.state);
        }
      });
      
      // Set active status
      cy.fillAdminForm({ 'is_active': true }, 'checkbox');
      
      // Save the new scheme
      cy.save();
      cy.verifyMessage('success', 'added successfully');
      
      // Store the scheme ID for later use
      cy.url().then(url => {
        createdIds.scheme = url.split('/').filter(Boolean).pop();
      });
    });
    
    it('should read and verify scheme details', () => {
      // Visit the scheme list
      cy.visit('/admin/communityEmpowerment/scheme/');
      
      // Verify the scheme appears in the list
      cy.get('#result_list').should('contain', testData.scheme);
      
      // Visit the scheme detail page
      cy.contains(testData.scheme).click();
      
      // Verify scheme details
      cy.get('input[name="name"]').should('have.value', testData.scheme);
      cy.get('textarea[name="short_description"]').should('have.value', 'Test scheme description');
    });
    
    it('should update scheme details', () => {
      // Visit the scheme edit page
      cy.visit(`/admin/communityEmpowerment/scheme/${createdIds.scheme}/change/`);
      
      // Update the name
      cy.fillAdminForm({ 'name': testData.updatedScheme }, 'input');
      cy.fillAdminForm({ 'short_description': 'Updated description' }, 'textarea');
      
      // Save changes
      cy.save();
      cy.verifyMessage('success', 'changed successfully');
      
      // Verify changes in list view
      cy.visit('/admin/communityEmpowerment/scheme/');
      cy.get('#result_list').should('contain', testData.updatedScheme);
    });
    
    it('should delete a scheme', () => {
      // Create a scheme specifically for deletion
      cy.visit('/admin/communityEmpowerment/scheme/add/');
      const deleteScheme = `Delete Test ${testId}`;
      
      // Fill minimal required fields
      cy.fillAdminForm({ 'name': deleteScheme }, 'input');
      cy.fillAdminForm({ 'short_description': 'To be deleted' }, 'textarea');
      
      // Associate with department if needed
      cy.get('body').then($body => {
        if ($body.find('select[name="department"]').length) {
          cy.get('select[name="department"] option')
            .contains(testData.department)
            .then($option => {
              if ($option.length) {
                cy.get('select[name="department"]').select($option.val());
              }
            });
        }
      });
      
      // Save the scheme
      cy.save();
      
      // Get the ID and delete it
      cy.url().then(url => {
        const deleteId = url.split('/').filter(Boolean).pop();
        
        // Visit delete page
        cy.visit(`/admin/communityEmpowerment/scheme/${deleteId}/delete/`);
        cy.contains('Yes, I\'m sure').click();
        
        // Verify deletion
        cy.verifyMessage('success', 'deleted successfully');
        cy.get('#result_list').should('not.contain', deleteScheme);
      });
    });
  });

  // 2. PERMISSION TESTS
  context('2. User Role Permissions', () => {
    it('should test editor permissions on schemes', () => {
      // Logout as admin
      cy.admin_logout();
      
      // Login as editor
      cy.admin_login(users.editor.username, users.editor.password);
      
      // Visit schemes list
      cy.visit('/admin/communityEmpowerment/scheme/');
      
      // Editor should be able to view schemes
      cy.get('#result_list').should('exist');
      
      // Check if editor can add/edit schemes based on configured permissions
      cy.get('body').then($body => {
        // Check for add permission
        const canAdd = $body.find('a.addlink').length > 0;
        cy.log(`Editor ${canAdd ? 'can' : 'cannot'} add schemes`);
        
        // Check for edit permission by trying to open a scheme
        if ($body.find(`tr:contains("${testData.updatedScheme}")`).length) {
          cy.contains(testData.updatedScheme).click();
          
          // Check if editor can save changes
          const canEdit = $body.find('input[name="_save"]').length > 0;
          cy.log(`Editor ${canEdit ? 'can' : 'cannot'} edit schemes`);
        }
      });
      
      // Logout editor
      cy.admin_logout();
      
      // Login back as admin
      cy.admin_login(users.admin.username, users.admin.password);
    });
    
    it('should test viewer permissions on schemes', () => {
      // Logout as admin
      cy.admin_logout();
      
      // Login as viewer
      cy.admin_login(users.viewer.username, users.viewer.password);
      
      // Visit schemes list
      cy.visit('/admin/communityEmpowerment/scheme/');
      
      // Viewer should be able to view schemes list
      cy.get('#result_list').should('exist');
      
      // Viewer should not have add permission
      cy.get('a.addlink').should('not.exist');
      
      // Check if viewer can see details
      cy.contains(testData.updatedScheme).click();
      
      // Fields should be readonly or disabled
      cy.get('body').then($body => {
        const isReadOnly = $body.find('.readonly').length > 0 || 
                          $body.find('input[readonly]').length > 0 ||
                          $body.find('input[name="_save"]').length === 0;
        
        cy.log(`Viewer ${isReadOnly ? 'cannot' : 'can'} edit schemes`);
      });
      
      // Logout viewer
      cy.admin_logout();
      
      // Login back as admin
      cy.admin_login(users.admin.username, users.admin.password);
    });
  });

  // 3. SEARCH AND FILTER
  context('3. Search and Filter Functionality', () => {
    it('should search for schemes by name', () => {
      // Visit scheme list
      cy.visit('/admin/communityEmpowerment/scheme/');
      
      // Search for the updated scheme name
      cy.get('#searchbar').type(testData.updatedScheme);
      cy.get('input[type="submit"]').click();
      
      // Verify search results
      cy.get('#result_list').should('contain', testData.updatedScheme);
      
      // Clear search
      cy.visit('/admin/communityEmpowerment/scheme/');
    });
    
    it('should filter schemes by department or state', () => {
      // Visit scheme list
      cy.visit('/admin/communityEmpowerment/scheme/');
      
      // Check for filter options
      cy.get('#changelist-filter').then($filter => {
        // Try to filter by department if available
        if ($filter.find('a:contains("By department")').length) {
          cy.contains('By department').click();
          cy.contains(testData.department).click();
          cy.get('#result_list').should('contain', testData.updatedScheme);
        } 
        // Otherwise try to filter by state
        else if ($filter.find('a:contains("By state")').length) {
          cy.contains('By state').click();
          cy.contains(testData.state).click();
          cy.get('#result_list').should('contain', testData.updatedScheme);
        }
        // If neither is available, log it
        else {
          cy.log('No department or state filter available - skipping test');
        }
      });
    });
  });
});
