// Admin Resource Management Tests - Simplified
// Uses shared test framework for FAQ, Banner, and Announcement management

describe('Admin Resource Management', () => {
  // Admin credentials
  const admin = {
    username: 'admin',
    password: 'adminpassword'
  };
  
  // Editor credentials (for permission tests)
  const editor = {
    username: 'editor',
    password: 'editorpassword'
  };
  
  // Timestamp to make test data unique
  const timestamp = Date.now();
  
  // Test data for each resource type
  const testData = {
    faq: {
      model: 'faq',
      nameField: 'question',
      titleText: `Test FAQ ${timestamp}`,
      fields: {
        question: `Test FAQ ${timestamp}`,
        answer: 'This is a test FAQ answer for automated testing.',
        order: '10',
        is_active: true
      },
      updatedTitle: `Updated FAQ ${timestamp}`
    },
    
    banner: {
      model: 'banner',
      nameField: 'title',
      titleText: `Test Banner ${timestamp}`,
      fields: {
        title: `Test Banner ${timestamp}`,
        description: 'This is a test banner for automated testing.',
        is_active: true
      },
      updatedTitle: `Updated Banner ${timestamp}`
    },
    
    announcement: {
      model: 'announcement',
      nameField: 'title',
      titleText: `Test Announcement ${timestamp}`,
      fields: {
        title: `Test Announcement ${timestamp}`,
        description: 'This is a test announcement for automated testing.',
        is_active: true
      },
      updatedTitle: `Updated Announcement ${timestamp}`
    }
  };
  
  // Login once before all tests
  before(() => {
    cy.clearCookies();
    cy.admin_login(admin.username, admin.password);
  });
  
  // Logout after all tests
  after(() => {
    cy.admin_logout();
  });
  
  // Shared test functions for different resource types
  const runResourceTests = (resourceType) => {
    const resource = testData[resourceType];
    
    context(`${resourceType.charAt(0).toUpperCase() + resourceType.slice(1)} Management`, () => {
      // 1. Create the resource
      it(`should create a new ${resourceType}`, () => {
        // Visit the add page
        cy.visit(`/admin/communityEmpowerment/${resource.model}/add/`);
        
        // Fill the form with the resource fields
        Object.entries(resource.fields).forEach(([field, value]) => {
          const fieldType = field === 'answer' || field === 'description' ? 'textarea' : 
                           field === 'is_active' ? 'checkbox' : 'input';
          cy.fillAdminForm({ [field]: value }, fieldType);
        });
        
        // Save the form
        cy.save();
        
        // Verify success message
        cy.verifyMessage('success', 'added successfully');
        
        // Verify resource appears in the list
        cy.verifyListView(resource.model, resource.titleText);
      });
      
      // 2. Edit the resource
      it(`should edit an existing ${resourceType}`, () => {
        // Go to resource list
        cy.visit(`/admin/communityEmpowerment/${resource.model}/`);
        
        // Find and click on the test resource
        cy.contains('tr', resource.titleText).find('th a').click();
        
        // Update the resource title field
        cy.fillAdminForm({ [resource.nameField]: resource.updatedTitle }, 'input');
        
        // Save changes
        cy.save();
        
        // Verify success message
        cy.verifyMessage('success', 'changed successfully');
        
        // Verify updated resource appears in list view
        cy.verifyListView(resource.model, resource.updatedTitle);
        
        // Update test data with new title
        resource.titleText = resource.updatedTitle;
      });
      
      // 3. Toggle resource status (active/inactive)
      it(`should toggle ${resourceType} active status`, () => {
        // Go to resource list
        cy.visit(`/admin/communityEmpowerment/${resource.model}/`);
        
        // Find the test resource row
        cy.contains('tr', resource.titleText).within(() => {
          // Toggle the status checkbox
          const checkbox = cy.get('input[name*="is_active"]');
          checkbox.invoke('prop', 'checked').then(checked => {
            if (checked) {
              checkbox.uncheck();
            } else {
              checkbox.check();
            }
          });
        });
        
        // Save the list
        cy.get('input[name="_save"]').click();
        
        // Verify success message
        cy.verifyMessage('success', 'successfully');
      });
      
      // 4. Delete the resource
      it(`should delete a ${resourceType}`, () => {
        // Go to resource list
        cy.visit(`/admin/communityEmpowerment/${resource.model}/`);
        
        // Find and click on the test resource
        cy.contains('tr', resource.titleText).find('th a').click();
        
        // Delete the resource
        cy.contains('Delete').click();
        cy.contains('Yes, I\'m sure').click();
        
        // Verify success message
        cy.verifyMessage('success', 'deleted successfully');
        
        // Verify resource no longer appears in list view
        cy.verifyListView(resource.model, resource.titleText, false);
      });
    });
  };
  
  // Run tests for each resource type
  runResourceTests('faq');
  runResourceTests('banner');
  runResourceTests('announcement');
  
  // Permission tests - using FAQs as an example
  context('Permission Tests', () => {
    // Create a test FAQ for permission tests
    before(() => {
      // Create a test FAQ
      cy.visit('/admin/communityEmpowerment/faq/add/');
      cy.fillAdminForm({ 'question': `Permission Test FAQ ${timestamp}` }, 'input');
      cy.fillAdminForm({ 'answer': 'This is for testing permissions.' }, 'textarea');
      cy.fillAdminForm({ 'is_active': true }, 'checkbox');
      cy.save();
    });
    
    // Clean up after tests
    after(() => {
      // Delete the test FAQ if it exists
      cy.visit('/admin/communityEmpowerment/faq/');
      cy.get('body').then($body => {
        if ($body.find(`tr:contains("Permission Test FAQ ${timestamp}")`).length) {
          cy.contains(`Permission Test FAQ ${timestamp}`).closest('tr').find('th a').click();
          cy.contains('Delete').click();
          cy.contains('Yes, I\'m sure').click();
        }
      });
    });
    
    it('should test editor permissions on resources', () => {
      // Logout as admin
      cy.admin_logout();
      
      // Login as editor
      cy.admin_login(editor.username, editor.password);
      
      // Visit FAQs list
      cy.visit('/admin/communityEmpowerment/faq/');
      
      // Editor should be able to view FAQs
      cy.get('#result_list').should('exist');
      
      // Check edit permissions based on role configuration
      cy.get('body').then($body => {
        // Can editor add new FAQs?
        const canAdd = $body.find('a.addlink').length > 0;
        cy.log(`Editor ${canAdd ? 'can' : 'cannot'} add FAQs`);
        
        // Can editor edit FAQs?
        if ($body.find(`tr:contains("Permission Test FAQ ${timestamp}")`).length) {
          cy.contains(`Permission Test FAQ ${timestamp}`).closest('tr').find('th a').click();
          
          // Check if editor can save changes
          const canEdit = $body.find('input[name="_save"]').length > 0;
          cy.log(`Editor ${canEdit ? 'can' : 'cannot'} edit FAQs`);
        }
      });
      
      // Logout editor and login back as admin
      cy.admin_logout();
      cy.admin_login(admin.username, admin.password);
    });
  });
  
  // Tests for bulk operations and filtering
  context('Bulk Operations and Filtering', () => {
    // Test data for bulk operations
    const bulkFAQs = [];
    
    before(() => {
      // Create 3 test FAQs for bulk operations
      for (let i = 1; i <= 3; i++) {
        bulkFAQs.push({
          question: `Bulk FAQ ${i} - ${timestamp}`,
          answer: `This is bulk test FAQ ${i}`,
          is_active: i % 2 === 0 // Alternate active/inactive
        });
        
        // Create the FAQ
        cy.visit('/admin/communityEmpowerment/faq/add/');
        cy.fillAdminForm({ 'question': bulkFAQs[i-1].question }, 'input');
        cy.fillAdminForm({ 'answer': bulkFAQs[i-1].answer }, 'textarea');
        cy.fillAdminForm({ 'is_active': bulkFAQs[i-1].is_active }, 'checkbox');
        cy.save();
      }
    });
    
    it('should filter resources by active status', () => {
      // Go to FAQ list
      cy.visit('/admin/communityEmpowerment/faq/');
      
      // Filter by active status
      cy.get('#changelist-filter').contains('Active').click();
      cy.get('#changelist-filter').contains('Yes').click();
      
      // Verify inactive FAQs are hidden
      bulkFAQs.forEach(faq => {
        if (faq.is_active) {
          cy.contains(faq.question).should('exist');
        } else {
          cy.contains(faq.question).should('not.exist');
        }
      });
      
      // Reset filter
      cy.visit('/admin/communityEmpowerment/faq/');
    });
    
    it('should perform bulk delete operation', () => {
      // Go to FAQ list
      cy.visit('/admin/communityEmpowerment/faq/');
      
      // Select all test FAQs
      bulkFAQs.forEach(faq => {
        cy.contains('tr', faq.question).find('input[type="checkbox"]').check();
      });
      
      // Perform bulk delete
      cy.get('select[name="action"]').select('delete_selected');
      cy.get('button[type="submit"]').contains('Go').click();
      
      // Confirm deletion
      cy.contains('Yes, I\'m sure').click();
      
      // Verify success message
      cy.verifyMessage('success', 'successfully deleted');
      
      // Verify FAQs are removed
      bulkFAQs.forEach(faq => {
        cy.contains(faq.question).should('not.exist');
      });
    });
  });
});
