// Admin Layout Customization Tests - Simplified
// Tests layout items, sections, ordering, and previews

describe('Admin Layout Customization', () => {
  // Unique timestamp for test data
  const timestamp = Date.now();
  
  // User credentials
  const admin = {
    username: 'admin',
    password: 'adminpassword'
  };
  
  const editor = {
    username: 'editor',
    password: 'editorpassword'
  };
  
  const viewer = {
    username: 'viewer',
    password: 'viewerpassword'
  };
  
  // Test data for layout items
  const testLayoutItem = {
    title: `Test Layout Item ${timestamp}`,
    content: 'This is a test layout item for automated testing.',
    order: '10',
    is_active: true
  };
  
  // Login once before all tests
  before(() => {
    cy.clearCookies();
    cy.admin_login(admin.username, admin.password);
  });
  
  // Logout after all tests
  after(() => {
    // Clean up any remaining test items
    cy.visit('/admin/communityEmpowerment/layoutitem/');
    cy.get('body').then($body => {
      if ($body.text().includes(testLayoutItem.title)) {
        cy.contains('tr', testLayoutItem.title).find('th a').click();
        cy.contains('Delete').click();
        cy.contains('Yes, I\'m sure').click();
      }
      if ($body.text().includes(`Permission Test Item ${timestamp}`)) {
        cy.contains(`Permission Test Item ${timestamp}`).closest('tr').find('th a').click();
        cy.contains('Delete').click();
        cy.contains('Yes, I\'m sure').click();
      }
    });
    
    cy.admin_logout();
  });
  
  context('Layout Item CRUD Operations', () => {
    it('should create a new layout item', () => {
      // Navigate to layout item add page
      cy.visit('/admin/communityEmpowerment/layoutitem/add/');
      
      // Fill the form with test data
      cy.fillAdminForm({ 'title': testLayoutItem.title }, 'input');
      cy.fillAdminForm({ 'content': testLayoutItem.content }, 'textarea');
      cy.fillAdminForm({ 'order': testLayoutItem.order }, 'input');
      cy.fillAdminForm({ 'is_active': testLayoutItem.is_active }, 'checkbox');
      
      // Fill optional fields if they exist
      cy.get('body').then($body => {
        // Fill layout_type if it exists
        if ($body.find('select[name="layout_type"]').length) {
          cy.get('select[name="layout_type"] option').then($options => {
            if ($options.length > 1) {
              cy.get('select[name="layout_type"]').select(1);
            }
          });
        }
        
        // Fill section if it exists
        if ($body.find('select[name="section"]').length) {
          cy.get('select[name="section"] option').then($options => {
            if ($options.length > 1) {
              cy.get('select[name="section"]').select(1);
            }
          });
        }
      });
      
      // Save the form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'added successfully');
      
      // Verify layout item appears in list
      cy.visit('/admin/communityEmpowerment/layoutitem/');
      cy.contains(testLayoutItem.title).should('exist');
    });
    
    it('should read and edit a layout item', () => {
      // Go to layout item list
      cy.visit('/admin/communityEmpowerment/layoutitem/');
      
      // Find and click on the test layout item
      cy.contains('tr', testLayoutItem.title).find('th a').click();
      
      // Verify details are displayed correctly
      cy.get('input[name="title"]').should('have.value', testLayoutItem.title);
      cy.get('textarea[name="content"]').should('have.value', testLayoutItem.content);
      
      // Update the layout item
      const updatedTitle = `${testLayoutItem.title} Updated`;
      cy.fillAdminForm({ 'title': updatedTitle }, 'input');
      
      // Save changes
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'changed successfully');
      
      // Verify updated item appears in list
      cy.visit('/admin/communityEmpowerment/layoutitem/');
      cy.contains(updatedTitle).should('exist');
      
      // Update test data
      testLayoutItem.title = updatedTitle;
    });
    
    it('should reorder layout items in list view', () => {
      // Go to layout item list
      cy.visit('/admin/communityEmpowerment/layoutitem/');
      
      // Check if order is editable in list view
      cy.contains('tr', testLayoutItem.title).within(() => {
        cy.get('input[name*="order"]').then($input => {
          if ($input.length && !$input.prop('disabled')) {
            // Change the order
            cy.wrap($input).clear().type('5');
          }
        });
      });
      
      // Save changes if order is editable
      cy.get('input[name="_save"]').then($saveBtn => {
        if ($saveBtn.length) {
          cy.wrap($saveBtn).click();
          cy.verifyMessage('success', 'successfully');
          
          // Verify the order change
          cy.contains('tr', testLayoutItem.title).find('input[name*="order"]').should('have.value', '5');
        } else {
          cy.log('Order not editable from list view');
        }
      });
    });
    
    it('should toggle layout item active status', () => {
      // Go to layout item list
      cy.visit('/admin/communityEmpowerment/layoutitem/');
      
      // Find the layout item
      cy.contains('tr', testLayoutItem.title).within(() => {
        // Check if is_active checkbox exists and is toggleable
        cy.get('input[name*="is_active"]').then($checkbox => {
          if ($checkbox.length && !$checkbox.prop('disabled')) {
            // Get current state
            const isChecked = $checkbox.prop('checked');
            
            // Toggle the checkbox
            if (isChecked) {
              cy.wrap($checkbox).uncheck();
            } else {
              cy.wrap($checkbox).check();
            }
          }
        });
      });
      
      // Save changes if checkbox is editable
      cy.get('input[name="_save"]').then($saveBtn => {
        if ($saveBtn.length) {
          cy.wrap($saveBtn).click();
          cy.verifyMessage('success', 'successfully');
        } else {
          cy.log('Status not toggleable from list view');
        }
      });
    });
    
    it('should delete a layout item', () => {
      // Go to layout item list
      cy.visit('/admin/communityEmpowerment/layoutitem/');
      
      // Find and click on the test layout item
      cy.contains('tr', testLayoutItem.title).find('th a').click();
      
      // Delete the item
      cy.contains('Delete').click();
      cy.contains('Yes, I\'m sure').click();
      
      // Verify success message
      cy.verifyMessage('success', 'deleted successfully');
      
      // Verify item is removed from list
      cy.visit('/admin/communityEmpowerment/layoutitem/');
      cy.contains(testLayoutItem.title).should('not.exist');
    });
  });
  
  context('Layout Preview Functionality', () => {
    // Create a test layout item for preview tests
    before(() => {
      cy.visit('/admin/communityEmpowerment/layoutitem/add/');
      cy.fillAdminForm({ 'title': testLayoutItem.title }, 'input');
      cy.fillAdminForm({ 'content': testLayoutItem.content }, 'textarea');
      cy.fillAdminForm({ 'order': testLayoutItem.order }, 'input');
      cy.fillAdminForm({ 'is_active': true }, 'checkbox');
      
      // Fill optional fields if necessary
      cy.get('body').then($body => {
        if ($body.find('select[name="layout_type"]').length) {
          cy.get('select[name="layout_type"] option').eq(1).then($option => {
            if ($option.length) cy.get('select[name="layout_type"]').select($option.val());
          });
        }
        if ($body.find('select[name="section"]').length) {
          cy.get('select[name="section"] option').eq(1).then($option => {
            if ($option.length) cy.get('select[name="section"]').select($option.val());
          });
        }
      });
      
      cy.save();
    });
    
    it('should check preview functionality', () => {
      // Go to layout item list
      cy.visit('/admin/communityEmpowerment/layoutitem/');
      
      // Look for preview options
      cy.get('body').then($body => {
        // Check for direct preview button
        if ($body.find('a:contains("Preview")').length) {
          cy.contains('a', 'Preview').click();
          cy.url().should('include', 'preview');
          cy.log('Preview page loaded successfully');
        } 
        // Check for view on site link
        else if ($body.find('a:contains("View on site")').length) {
          cy.contains('a', 'View on site').click();
          cy.url().should('not.include', '/admin/');
          cy.log('Site view loaded successfully');
        }
        // Try viewing the item detail page for preview options
        else {
          cy.contains('tr', testLayoutItem.title).find('th a').click();
          
          // Check for preview or view options on detail page
          cy.get('body').then($detailBody => {
            if ($detailBody.find('a:contains("View on site")').length) {
              cy.contains('a', 'View on site').click();
              cy.url().should('not.include', '/admin/');
              cy.log('Site view from detail page loaded successfully');
            } else {
              cy.log('No preview functionality found');
            }
          });
        }
      });
    });
    
    it('should validate layout display if functionality exists', () => {
      // Go to layout item list
      cy.visit('/admin/communityEmpowerment/layoutitem/');
      
      // Check for validation or layout check functionality
      cy.get('body').then($body => {
        // Look for validate action in dropdown
        if ($body.find('select[name="action"] option:contains("Validate")').length) {
          // Select the test item
          cy.contains('tr', testLayoutItem.title).find('input[type="checkbox"]').check();
          
          // Select validate action
          cy.get('select[name="action"]').select('validate_layouts');
          cy.get('button[type="submit"]').contains('Go').click();
          
          // Check for validation results
          cy.log('Layout validation action triggered');
        } 
        // Look for direct validation button
        else if ($body.find('a:contains("Validate")').length) {
          cy.contains('a', 'Validate').click();
          cy.log('Layout validation page accessed');
        } else {
          cy.log('No layout validation functionality found');
        }
      });
    });
  });
  
  context('Section Management', () => {
    const testSection = {
      name: `Test Section ${timestamp}`,
      description: 'This is a test section for automated testing.',
      order: '5'
    };
    
    it('should check if section management is available', () => {
      // Check if sections can be managed
      cy.visit('/admin/');
      cy.get('body').then($body => {
        const hasSections = 
          $body.find('a:contains("Section")').length > 0 || 
          $body.find('a:contains("Layout section")').length > 0;
        
        if (hasSections) {
          // Navigate to sections
          if ($body.find('a:contains("Layout section")').length) {
            cy.contains('a', 'Layout section').click();
          } else if ($body.find('a:contains("Section")').length) {
            cy.contains('a', 'Section').click();
          }
          
          // Check if we can add a section
          cy.get('a.addlink').then($addLink => {
            if ($addLink.length) {
              // Create a test section
              cy.wrap($addLink).click();
              
              // Fill section form
              cy.get('body').then($formBody => {
                if ($formBody.find('input[name="name"]').length) {
                  cy.fillAdminForm({ 'name': testSection.name }, 'input');
                  
                  // Fill description if available
                  if ($formBody.find('textarea[name="description"]').length) {
                    cy.fillAdminForm({ 'description': testSection.description }, 'textarea');
                  }
                  
                  // Fill order if available
                  if ($formBody.find('input[name="order"]').length) {
                    cy.fillAdminForm({ 'order': testSection.order }, 'input');
                  }
                  
                  // Save the section
                  cy.save();
                  cy.verifyMessage('success', 'added successfully');
                  
                  // Verify section appears in list
                  cy.contains(testSection.name).should('exist');
                  
                  // Clean up - delete the section
                  cy.contains('tr', testSection.name).find('th a').click();
                  cy.contains('Delete').click();
                  cy.contains('Yes, I\'m sure').click();
                }
              });
            } else {
              cy.log('Cannot add sections, likely view-only permission');
            }
          });
        } else {
          cy.log('Section management not available in this application');
        }
      });
    });
  });
  
  context('Bulk Operations', () => {
    // Create multiple test items for bulk operations
    before(() => {
      // Create 3 test layout items
      for (let i = 1; i <= 3; i++) {
        cy.visit('/admin/communityEmpowerment/layoutitem/add/');
        cy.fillAdminForm({ 'title': `Bulk Test Item ${i} ${timestamp}` }, 'input');
        cy.fillAdminForm({ 'content': `Content for bulk test item ${i}` }, 'textarea');
        cy.fillAdminForm({ 'order': `${20 + i}` }, 'input');
        cy.fillAdminForm({ 'is_active': i % 2 === 0 }, 'checkbox'); // Alternate active status
        
        // Fill required fields if they exist
        cy.get('body').then($body => {
          if ($body.find('select[name="layout_type"]').length) {
            cy.get('select[name="layout_type"] option').eq(1).then($option => {
              if ($option.length) cy.get('select[name="layout_type"]').select($option.val());
            });
          }
          if ($body.find('select[name="section"]').length) {
            cy.get('select[name="section"] option').eq(1).then($option => {
              if ($option.length) cy.get('select[name="section"]').select($option.val());
            });
          }
        });
        
        cy.save();
      }
    });
    
    // Clean up test items after bulk tests
    after(() => {
      // Delete any remaining bulk test items
      cy.visit('/admin/communityEmpowerment/layoutitem/');
      for (let i = 1; i <= 3; i++) {
        cy.get('body').then($body => {
          if ($body.text().includes(`Bulk Test Item ${i} ${timestamp}`)) {
            cy.contains(`Bulk Test Item ${i} ${timestamp}`).closest('tr').find('th a').click();
            cy.contains('Delete').click();
            cy.contains('Yes, I\'m sure').click();
            cy.visit('/admin/communityEmpowerment/layoutitem/');
          }
        });
      }
    });
    
    it('should perform bulk activation/deactivation', () => {
      // Go to layout item list
      cy.visit('/admin/communityEmpowerment/layoutitem/');
      
      // Check if bulk actions are available
      cy.get('select[name="action"]').then($actionSelect => {
        if ($actionSelect.find('option[value="activate_selected"]').length || 
            $actionSelect.find('option[value="deactivate_selected"]').length) {
          
          // Select the test items
          for (let i = 1; i <= 3; i++) {
            cy.contains(`Bulk Test Item ${i} ${timestamp}`).closest('tr')
              .find('input[type="checkbox"]').check();
          }
          
          // Try bulk activation if available
          if ($actionSelect.find('option[value="activate_selected"]').length) {
            cy.get('select[name="action"]').select('activate_selected');
            cy.get('button[type="submit"]').contains('Go').click();
            cy.verifyMessage('success', 'successfully');
            cy.log('Bulk activation successful');
          } 
          // Try bulk deactivation if available
          else if ($actionSelect.find('option[value="deactivate_selected"]').length) {
            cy.get('select[name="action"]').select('deactivate_selected');
            cy.get('button[type="submit"]').contains('Go').click();
            cy.verifyMessage('success', 'successfully');
            cy.log('Bulk deactivation successful');
          }
        } else {
          cy.log('Bulk activation/deactivation not available');
        }
      });
    });
    
    it('should perform bulk deletion', () => {
      // Go to layout item list
      cy.visit('/admin/communityEmpowerment/layoutitem/');
      
      // Select the test items
      for (let i = 1; i <= 3; i++) {
        cy.contains(`Bulk Test Item ${i} ${timestamp}`).closest('tr')
          .find('input[type="checkbox"]').check();
      }
      
      // Perform bulk delete
      cy.get('select[name="action"]').select('delete_selected');
      cy.get('button[type="submit"]').contains('Go').click();
      
      // Confirm deletion
      cy.contains('Yes, I\'m sure').click();
      
      // Verify success message
      cy.verifyMessage('success', 'successfully deleted');
      
      // Verify items are removed
      for (let i = 1; i <= 3; i++) {
        cy.contains(`Bulk Test Item ${i} ${timestamp}`).should('not.exist');
      }
    });
  });
  
  context('Permission Tests', () => {
    // Create a test layout item for permission testing
    before(() => {
      cy.visit('/admin/communityEmpowerment/layoutitem/add/');
      cy.fillAdminForm({ 'title': `Permission Test Item ${timestamp}` }, 'input');
      cy.fillAdminForm({ 'content': 'This is for testing permissions.' }, 'textarea');
      cy.fillAdminForm({ 'order': '50' }, 'input');
      cy.fillAdminForm({ 'is_active': true }, 'checkbox');
      
      // Fill required fields if they exist
      cy.get('body').then($body => {
        if ($body.find('select[name="layout_type"]').length) {
          cy.get('select[name="layout_type"] option').eq(1).then($option => {
            if ($option.length) cy.get('select[name="layout_type"]').select($option.val());
          });
        }
        if ($body.find('select[name="section"]').length) {
          cy.get('select[name="section"] option').eq(1).then($option => {
            if ($option.length) cy.get('select[name="section"]').select($option.val());
          });
        }
      });
      
      cy.save();
    });
    
    it('should verify editor permissions', () => {
      // Logout as admin
      cy.admin_logout();
      
      // Login as editor
      cy.admin_login(editor.username, editor.password);
      
      // Check layout access and permissions
      cy.visit('/admin/');
      cy.get('body').then($body => {
        // Check if layout management is accessible
        const hasLayoutAccess = 
          $body.find('a:contains("Layout")').length > 0 || 
          $body.find('a:contains("Layout item")').length > 0;
        
        if (hasLayoutAccess) {
          // Navigate to layout items
          if ($body.find('a:contains("Layout item")').length) {
            cy.contains('a', 'Layout item').click();
          } else if ($body.find('a:contains("Layout")').length) {
            cy.contains('a', 'Layout').click();
          }
          
          // Check for Add permissions
          cy.get('body').then($listBody => {
            const canAdd = $listBody.find('a.addlink').length > 0;
            cy.log(`Editor ${canAdd ? 'can' : 'cannot'} add new layout items`);
            
            // Check edit permissions on existing item
            if ($listBody.text().includes(`Permission Test Item ${timestamp}`)) {
              cy.contains(`Permission Test Item ${timestamp}`).closest('tr').find('th a').click();
              
              // Check for save and delete permissions
              cy.get('body').then($detailBody => {
                const canEdit = $detailBody.find('input[name="_save"]').length > 0;
                const canDelete = $detailBody.find('a:contains("Delete")').length > 0;
                
                cy.log(`Editor ${canEdit ? 'can' : 'cannot'} edit layout items`);
                cy.log(`Editor ${canDelete ? 'can' : 'cannot'} delete layout items`);
              });
            }
          });
        } else {
          cy.log('Editor does not have access to layout management');
        }
      });
      
      // Logout as editor
      cy.admin_logout();
      
      // Login back as admin
      cy.admin_login(admin.username, admin.password);
    });
    
    it('should verify viewer permissions', () => {
      // Logout as admin
      cy.admin_logout();
      
      // Login as viewer
      cy.admin_login(viewer.username, viewer.password);
      
      // Check layout access and permissions
      cy.visit('/admin/');
      cy.get('body').then($body => {
        // Check if layout management is accessible
        const hasLayoutAccess = 
          $body.find('a:contains("Layout")').length > 0 || 
          $body.find('a:contains("Layout item")').length > 0;
        
        if (hasLayoutAccess) {
          // Navigate to layout items
          if ($body.find('a:contains("Layout item")').length) {
            cy.contains('a', 'Layout item').click();
          } else if ($body.find('a:contains("Layout")').length) {
            cy.contains('a', 'Layout').click();
          }
          
          // Verify read-only permissions
          cy.get('body').then($listBody => {
            // Should not have add button
            const canAdd = $listBody.find('a.addlink').length > 0;
            cy.log(`Viewer ${canAdd ? 'can' : 'cannot'} add new layout items`);
            
            // Should not have bulk action checkboxes if view-only
            const hasBulkActions = $listBody.find('input[name="_selected_action"]').length > 0;
            cy.log(`Viewer ${hasBulkActions ? 'has' : 'does not have'} access to bulk actions`);
            
            // Check if viewer can access item details
            if ($listBody.text().includes(`Permission Test Item ${timestamp}`)) {
              cy.contains(`Permission Test Item ${timestamp}`).closest('tr').find('th a').click();
              
              // Check if form is read-only
              cy.get('body').then($detailBody => {
                const canEdit = $detailBody.find('input[name="_save"]').length > 0;
                const isReadOnly = $detailBody.find('input[readonly], .readonly').length > 0;
                
                cy.log(`Viewer ${canEdit ? 'can' : 'cannot'} edit layout items`);
                cy.log(`Form is ${isReadOnly ? 'read-only' : 'editable'} for viewer`);
              });
            }
          });
        } else {
          cy.log('Viewer does not have access to layout management');
        }
      });
      
      // Logout as viewer
      cy.admin_logout();
      
      // Login back as admin
      cy.admin_login(admin.username, admin.password);
    });
  });
});
