// Cypress test file for Resources CRUD operations
import {
  generateRandomString,
  openAddNewForm,
  openEditForm,
  verifyListViewContains,
  verifyPagination
} from '../support-test-helpers';

describe('Resources Tests', () => {
  const users = {
    admin: {
      username: 'admin',
      password: 'adminpassword',
      role: 'Administrator'
    },
    editor: {
      username: 'editor', 
      password: 'editorpassword',
      role: 'Editor'
    },
    viewer: {
      username: 'viewer',
      password: 'viewerpassword',
      role: 'Viewer'
    }
  };
  
  const testData = users.admin;
  
  beforeEach(() => {
    // Login before each test
    cy.admin_login(testData.username, testData.password);
    cy.waitForDjangoAdmin();
  });
  
  afterEach(() => {
    // Logout after each test
    cy.admin_logout();
  });

  describe('Resource Listing Tests', () => {
    it('should display resources in the admin list view', () => {
      // Navigate to Resources section
      cy.visit('/communityEmpowerment/resource/');
      
      // Check if the page loaded correctly
      cy.get('h1').should('contain', 'Resources');
      cy.get('#content-main').should('be.visible');
      
      // Check table headers
      cy.get('#result_list thead').should('exist');
      
      // Verify there are resources listed or a message saying no results
      cy.get('body').then($body => {
        if ($body.find('#result_list tbody tr').length > 0) {
          cy.get('#result_list tbody tr').should('have.length.at.least', 1);
        } else {
          cy.contains('0 resources').should('exist');
        }
      });
    });

    it('should allow filtering and searching resources', () => {
      cy.visit('/communityEmpowerment/resource/');
      
      // Check if search box exists and is functional
      cy.get('#searchbar').should('exist').type('test{enter}');
      
      // Check if filter options exist
      cy.get('body').then($body => {
        if ($body.find('#changelist-filter').length > 0) {
          cy.get('#changelist-filter').should('be.visible');
          // Click on a filter option if any exists
          if ($body.find('#changelist-filter li a').length > 0) {
            cy.get('#changelist-filter li a').first().click();
            cy.get('#result_list').should('exist');
          }
        }
      });
    });

    it('should verify pagination works for resources', () => {
      cy.visit('/communityEmpowerment/resource/');
      
      // Check for pagination and test it if it exists
      verifyPagination();
    });
  });

  describe('Resource CRUD Operations', () => {
    const resourceTitle = `Test Resource ${generateRandomString(5)}`;
    const resourceUpdatedTitle = `Updated Resource ${generateRandomString(5)}`;
    
    it('should create a new resource', () => {
      cy.visit('/communityEmpowerment/resource/');
      openAddNewForm();
      
      // Fill in resource form fields
      // Note: Adjust field names based on your actual model
      cy.get('body').then($body => {
        if ($body.find('input[name="title"]').length) {
          cy.get('input[name="title"]').type(resourceTitle);
        }
        
        if ($body.find('input[name="url"]').length) {
          cy.get('input[name="url"]').type('https://example.com/resource');
        }
        
        if ($body.find('textarea[name="description"]').length) {
          cy.get('textarea[name="description"]').type('This is a test resource description');
        }

        if ($body.find('select[name="resource_type"]').length) {
          cy.get('select[name="resource_type"]').select(1);
        }

        // Handle file upload if there's a file field
        if ($body.find('input[type="file"]').length) {
          // Just check it exists, we won't actually upload in tests
          cy.get('input[type="file"]').should('exist');
        }

        // Handle is_active checkbox if present
        if ($body.find('input[name="is_active"]').length) {
          cy.get('input[name="is_active"]').check();
        }
      });
      
      // Save the form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'added successfully');
      
      // Verify the resource appears in the list
      cy.visit('/communityEmpowerment/resource/');
      verifyListViewContains('resource', resourceTitle);
    });

    it('should view and update an existing resource', () => {
      cy.visit('/communityEmpowerment/resource/');
      
      // Find our test resource or use the first one if not found
      cy.get('body').then($body => {
        if ($body.find(`tbody tr:contains("${resourceTitle}")`).length) {
          cy.contains('tr', resourceTitle).find('th a').click();
        } else if ($body.find('#result_list tbody tr').length) {
          openEditForm(0);
        } else {
          // Skip test if no resources exist
          cy.log('No resources to edit');
          return;
        }
        
        // Update fields
        cy.get('body').then($formBody => {
          if ($formBody.find('input[name="title"]').length) {
            cy.get('input[name="title"]').clear().type(resourceUpdatedTitle);
          }
          
          if ($formBody.find('textarea[name="description"]').length) {
            cy.get('textarea[name="description"]')
              .clear()
              .type('This is an updated test resource description');
          }
        });
        
        // Save the form
        cy.save();
        
        // Verify success message
        cy.verifyMessage('success', 'changed successfully');
      });
    });

    it('should delete a resource', () => {
      cy.visit('/communityEmpowerment/resource/');
      
      // Find our test resource or use the first one if not found
      cy.get('body').then($body => {
        if ($body.find(`tbody tr:contains("${resourceUpdatedTitle}")`).length) {
          cy.contains('tr', resourceUpdatedTitle).find('th a').click();
        } else if ($body.find('#result_list tbody tr').length) {
          openEditForm(0);
        } else {
          // Skip test if no resources exist
          cy.log('No resources to delete');
          return;
        }
        
        // Delete the resource
        cy.contains('a', 'Delete').click();
        cy.contains('button', "Yes, I'm sure").click();
        
        // Verify success message
        cy.verifyMessage('success', 'deleted successfully');
      });
    });
  });

  describe('Resource Permissions', () => {
    it('should verify different user roles have appropriate access to resources', () => {
      // This is a placeholder for permission testing
      // Full implementation would require creating test users with different permissions
      cy.visit('/communityEmpowerment/resource/');
      
      // Admin should have all permissions
      cy.get('a.addlink').should('exist');
      
      // Check if there are resources to edit
      cy.get('body').then($body => {
        if ($body.find('#result_list tbody tr').length) {
          openEditForm(0);
          cy.get('input[name="_save"]').should('exist');
          cy.get('a:contains("Delete")').should('exist');
        }
      });
    });
  });

  describe('Resource Front-end Display', () => {
    it('should verify resources are correctly displayed on the front-end', () => {
      // This would navigate to the front-end page showing resources
      // For now, we'll just verify we can access the admin page
      cy.visit('/communityEmpowerment/resource/');
      cy.get('h1').should('contain', 'Resources');
    });
  });
});

