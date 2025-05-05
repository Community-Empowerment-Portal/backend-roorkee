describe('Scheme Management - Essential Tests', () => {
  
  // Simple test data structures
  const testData = {
    state: `Test State`,
    department: `Test Department`,
    scheme: `Test Scheme`,
    updatedScheme: `Updated Scheme`
  };
  
  // Store created record IDs for cleanup
  const createdIds = {};
  
  // User credentials
  const users = {
    admin: { username: 'admin', password: 'adminpassword' },
    editor: { username: 'editor', password: 'editorpassword' },
    viewer: { username: 'viewer', password: 'viewerpassword' }
  };

  // Helper function to create prerequisites
  const createPrerequisites = () => {
    cy.visit('/communityEmpowerment/state/add/');
    cy.fillAdminForm({ 'state_name': testData.state }, 'input');
    cy.save();
    cy.wait(2000)
    cy.visit('/communityEmpowerment/state/');
      
    // Verify the scheme appears in the list
    cy.get('#result_list').should('contain', testData.state);
    
    // Visit the scheme detail page
    cy.contains(testData.state).click();
    
    cy.url().then(url => {
      const parts = url.split('/').filter(Boolean);
      createdIds.state = parts[parts.length - 2];
    });
  
    cy.visit('/communityEmpowerment/department/add/');
    cy.fillAdminForm({ 'department_name': testData.department }, 'input');
  
    cy.get('select[name="state"]').select(testData.state); 
    cy.save();
    cy.url().then(url => {
      const parts = url.split('/').filter(Boolean);
      createdIds.department = parts[parts.length - 2];
    });
  };
  

  // Login as admin before tests
  before(() => {
    cy.clearCookies();
    cy.admin_login(users.admin.username, users.admin.password);
    createPrerequisites();
  });
  
  beforeEach(() => {
    cy.session('admin-session', () => {
      cy.admin_login(users.admin.username, users.admin.password);
    });
  });

  // Logout after all tests
  after(() => {
    // Clean up created test data
    cleanupTestData();
    cy.admin_logout();
  });

  // Helper function to clean up test data
  const cleanupTestData = () => {
    if (createdIds.state) {
      cy.visit(`/communityEmpowerment/state/${createdIds.state}/delete/`);
      cy.get('input[type="submit"][value="Yes, I’m sure"]').click();
    }
  };

  // 1. BASIC CRUD OPERATIONS
  context('1. Basic CRUD Operations', () => {
    it('should create a new scheme', () => {
      cy.visit('/communityEmpowerment/scheme/add/');
      
      // Fill basic scheme information
      cy.fillAdminForm({ 'title': testData.scheme }, 'textarea');
      cy.fillAdminForm({ 'description': 'Test scheme description' }, 'textarea');
      
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
        
      });
      // Save the new scheme
      cy.save();
      cy.verifyMessage('success', 'added successfully');
    });
    
    it('should read and verify scheme details', () => {
      // Visit the scheme list
      cy.visit('/communityEmpowerment/scheme/');
      
      // Verify the scheme appears in the list
      cy.get('#result_list').should('contain', testData.scheme);
      
      // Visit the scheme detail page
      cy.contains(testData.scheme).click();
      
      // Store the scheme ID for later use
      cy.url().then(url => {
        const parts = url.split('/').filter(Boolean);
      createdIds.scheme = parts[parts.length - 2];
      });
      // Verify scheme details
      cy.get('textarea[name="title"]').should('have.value', testData.scheme);
      cy.get('textarea[name="description"]').should('have.value', 'Test scheme description');
    });
    
    it('should update scheme details', () => {
      // Visit the scheme edit page
      cy.visit(`/communityEmpowerment/scheme/${createdIds.scheme}/change/`);
      
      // Update the name
      cy.fillAdminForm({ 'title': testData.updatedScheme }, 'textarea');
      cy.fillAdminForm({ 'description': 'Updated description' }, 'textarea');
      
      // Save changes
      cy.save();
      cy.verifyMessage('success', 'changed successfully');
      
      // Verify changes in list view
      cy.visit('/communityEmpowerment/scheme/');
      cy.get('#result_list').should('contain', testData.updatedScheme);
    });
    
    it('should delete a scheme', () => {
      // Create a scheme specifically for deletion
      cy.visit('/communityEmpowerment/scheme/add/');
      const deleteScheme = `Delete Test`;
      
      // Fill minimal required fields
      cy.fillAdminForm({ 'title': deleteScheme }, 'textarea');
      cy.fillAdminForm({ 'description': 'To be deleted' }, 'textarea');
      
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
      cy.verifyMessage('success', 'added successfully');
      cy.wait(2000)
      cy.get('#result_list').should('contain', deleteScheme);
      
      // Visit the scheme detail page
      cy.contains(deleteScheme).click();

      // Get the ID and delete it
      cy.url().then(url => {
        const parts = url.split('/').filter(Boolean);
        deleteId = parts[parts.length - 2];
        
        // Visit delete page
        cy.visit(`/communityEmpowerment/scheme/${deleteId}/delete/`);
        cy.get('input[type="submit"][value="Yes, I’m sure"]').click();
        
        // Verify deletion
        cy.verifyMessage('success', 'deleted successfully');
        cy.get('#result_list').should('not.contain', deleteScheme);
      });
    });
  });


  // 2. SEARCH AND FILTER
  context('2. Search and Filter Functionality', () => {
    it('should search for schemes by name', () => {
      // Visit scheme list
      cy.visit('/communityEmpowerment/scheme/');
      
      // Search for the updated scheme name
      cy.get('#searchbar').type(testData.updatedScheme);
      cy.get('input[type="submit"]').first().click();
      
      // Verify search results
      cy.get('#result_list').should('contain', testData.updatedScheme);
      
      // Clear search
      cy.visit('/communityEmpowerment/scheme/');
    });
    
    it('should filter schemes by department or state', () => {
      // Visit scheme list
      cy.visit('/communityEmpowerment/scheme/');
      
      // Check for filter options
      cy.get('#changelist-filter').then($filter => {
        // Try to filter by department if available
        if ($filter.find('summary:contains("By department")').length) {
          cy.contains('By department').click();
          cy.contains(testData.department).click();
          cy.get('#result_list').should('contain', testData.updatedScheme);
        } 
        // Otherwise try to filter by state
        else if ($filter.find('summary:contains("By state")').length) {
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
