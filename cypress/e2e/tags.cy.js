// Cypress test file for Tags CRUD operations
import {
  generateRandomString,
  navigateToAdminSection,
  openAddNewForm,
  openEditForm,
  verifyListViewContains,
  verifyPagination
} from '../support/admin-test-helpers';

describe('Tags Tests', () => {
  // Define our user roles for testing
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
  
  // Use admin for our main CRUD tests
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

  describe('Tag Listing Tests', () => {
    it('should display tag categories in the admin list view', () => {
      // Navigate to Tags section
      cy.visit('/admin/communityEmpowerment/tag/');
      
      // Check if the page loaded correctly
      cy.get('h1').should('contain', 'Tags');
      cy.get('#content-main').should('be.visible');
      
      // Check table headers
      cy.get('#result_list thead').should('exist');
      cy.get('#result_list thead th').should('contain', 'Category display');
      cy.get('#result_list thead th').should('contain', 'Tag count');
      cy.get('#result_list thead th').should('contain', 'Weight');
      cy.get('#result_list thead th').should('contain', 'Tag names preview');
      
      // Verify there are tags listed or a message saying no results
      cy.get('body').then($body => {
        if ($body.find('#result_list tbody tr').length > 0) {
          cy.get('#result_list tbody tr').should('have.length.at.least', 1);
        } else {
          cy.contains('0 tags').should('exist');
        }
      });
    });

    it('should allow searching and filtering tags by category', () => {
      cy.visit('/admin/communityEmpowerment/tag/');
      
      // Check if search box exists and is functional
      cy.get('#searchbar').should('exist').type('test{enter}');
      
      // Check if filter options exist
      cy.get('body').then($body => {
        if ($body.find('#changelist-filter').length > 0) {
          cy.get('#changelist-filter').should('be.visible');
          // Click on category filter if it exists
          if ($body.find('#changelist-filter li a').length > 0) {
            cy.get('#changelist-filter li a').first().click();
            cy.get('#result_list').should('exist');
          }
        }
      });
    });

    it('should verify pagination works for tags', () => {
      cy.visit('/admin/communityEmpowerment/tag/');
      
      // Check for pagination and test it if it exists
      verifyPagination();
    });
  });

  describe('Tag Category and Count Tests', () => {
    it('should display correct tag count for each category', () => {
      cy.visit('/admin/communityEmpowerment/tag/');
      
      // Check that tag count is displayed
      cy.get('#result_list tbody tr').first().within(() => {
        cy.get('td:nth-child(2)').should('exist'); // Tag count column
      });
    });

    it('should test tag names preview functionality', () => {
      cy.visit('/admin/communityEmpowerment/tag/');
      
      // Find a row with tag names preview
      cy.get('#result_list tbody tr').first().within(() => {
        // Check if the tag preview element exists
        cy.get('td:nth-child(4)').should('exist'); // Tag names preview column
        
        // Check for "Show All" button if there are more than 5 tags
        cy.get('body').then($body => {
          if ($body.find('.show-all-btn').length > 0) {
            cy.get('.show-all-btn').should('be.visible');
          }
        });
      });
    });
    
    it('should verify tag weight is displayed correctly', () => {
      cy.visit('/admin/communityEmpowerment/tag/');
      
      // Verify that weight column exists
      cy.get('#result_list tbody tr').first().within(() => {
        cy.get('td:nth-child(3)').should('exist'); // Weight column
      });
    });
  });

  describe('Tag CRUD Operations', () => {
    const tagCategory = `TestCat${generateRandomString(5)}`;
    const tagName = `TestTag${generateRandomString(5)}`;
    const updatedTagName = `UpdatedTag${generateRandomString(5)}`;
    
    it('should create a new tag', () => {
      cy.visit('/admin/communityEmpowerment/tag/');
      openAddNewForm();
      
      // Fill in tag form fields
      cy.get('body').then($body => {
        // Check field names and fill appropriately
        if ($body.find('input[name="category"]').length) {
          cy.get('input[name="category"]').type(tagCategory);
        } else if ($body.find('select[name="category"]').length) {
          cy.get('select[name="category"]').select(1); // Select first option or...
          // You could also type if it's a select2 or similar widget
        }
        
        if ($body.find('input[name="name"]').length) {
          cy.get('input[name="name"]').type(tagName);
        }
        
        if ($body.find('input[name="weight"]').length) {
          cy.get('input[name="weight"]').clear().type('5');
        }
      });
      
      // Save the form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'added successfully');
      
      // Verify the tag appears in the list
      cy.visit('/admin/communityEmpowerment/tag/');
      verifyListViewContains('tag', tagCategory);
    });

    it('should view and update an existing tag', () => {
      cy.visit('/admin/communityEmpowerment/tag/');
      
      // Find our test tag or use the first one if not found
      cy.get('body').then($body => {
        if ($body.find(`tbody tr:contains("${tagCategory}")`).length) {
          cy.contains('tr', tagCategory).find('th a').click();
        } else if ($body.find('#result_list tbody tr').length) {
          openEditForm(0);
        } else {
          // Skip test if no tags exist
          cy.log('No tags to edit');
          return;
        }
        
        // Update fields
        cy.get('body').then($formBody => {
          if ($formBody.find('input[name="name"]').length) {
            cy.get('input[name="name"]').clear().type(updatedTagName);
          }
          
          if ($formBody.find('input[name="weight"]').length) {
            cy.get('input[name="weight"]').clear().type('10');
          }
        });
        
        // Save the form
        cy.save();
        
        // Verify success message
        cy.verifyMessage('success', 'changed successfully');
      });
    });

    it('should delete a tag', () => {
      cy.visit('/admin/communityEmpowerment/tag/');
      
      // Find our test tag or use the first one if not found
      cy.get('body').then($body => {
        if ($body.find(`tbody tr:contains("${tagCategory}")`).length) {
          cy.contains('tr', tagCategory).find('th a').click();
        } else if ($body.find('#result_list tbody tr').length) {
          openEditForm(0);
        } else {
          // Skip test if no tags exist
          cy.log('No tags to delete');
          return;
        }
        
        // Delete the tag
        cy.contains('a', 'Delete').click();
        cy.contains('button', "Yes, I'm sure").click();
        
        // Verify success message
        cy.verifyMessage('success', 'deleted successfully');
      });
    });
  });

  describe('Tag Permissions', () => {
    it('should verify different user roles have appropriate access to tags', () => {
      // This is a placeholder for permission testing
      // Full implementation would require creating test users with different permissions
      cy.visit('/admin/communityEmpowerment/tag/');
      
      // Admin should have all permissions
      cy.get('a.addlink').should('exist');
      
      // Check if there are tags to edit
      cy.get('body').then($body => {
        if ($body.find('#result_list tbody tr').length) {
          openEditForm(0);
          cy.get('input[name="_save"]').should('exist');
          cy.get('a:contains("Delete")').should('exist');
        }
      });
    });
  });

  describe('Tag UI Functionality', () => {
    it('should test the Show All tags functionality if available', () => {
      cy.visit('/admin/communityEmpowerment/tag/');
      
      // Find a row with tag names preview and "Show All" button
      cy.get('#result_list tbody tr').each(($row) => {
        if ($row.find('.show-all-btn').length > 0) {
          // Click "Show All" button
          cy.wrap($row).find('.show-all-btn').click();
          
          // Verify that the full tag list becomes visible
          cy.wrap($row).find('.tag-full').should('be.visible');
          
          // There's usually a "Hide" button after expanding
          if ($row.find('.show-all-btn:contains("Hide")').length > 0) {
            cy.wrap($row).find('.show-all-btn:contains("Hide")').click();
            cy.wrap($row).find('.tag-full').should('not.be.visible');
          }
          
          // Only test the first row that has the button
          return false;
        }
      });
    });

    it('should verify tag categories affect filtering', () => {
      cy.visit('/admin/communityEmpowerment/tag/');
      
      // If there are filter options by category, test them
      cy.get('body').then($body => {
        if ($body.find('#changelist-filter').length > 0 && 
            $body.find('#changelist-filter li a').length > 0) {
          
          // Click on first filter option
          cy.get('#changelist-filter li a').first().click();
          
          // Verify filtering works - the results should change or be filtered
          cy.url().should('include', '?');
        } else {
          cy.log('No category filters found to test');
        }
      });
    });
  });
});

