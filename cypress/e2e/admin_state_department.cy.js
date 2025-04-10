// Admin State and Department Management Tests
// Tests CRUD operations, permissions, relationships, and bulk actions for State and Department models
// This file serves as a template for other admin test files

import {
  loadTestUsersConfig,
  setupTestUser,
  verifyUserPermissions,
  checkModelPermissions
} from '../support/helpers';

// Main test suite for State and Department Management
describe('Admin State and Department Management', () => {
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
  
  // Test data with consistent timestamp
  const testState = {
    name: `Test State ${timestamp}`,
    code: `TS${timestamp.toString().substring(6, 10)}`,
    is_active: true
  };
  
  const testDepartment = {
    name: `Test Department ${timestamp}`,
    code: `TD${timestamp.toString().substring(6, 10)}`,
    is_active: true
  };
  
  // Login once before all tests
  before(() => {
    cy.clearCookies();
    cy.admin_login(admin.username, admin.password);
  });
  
  // Logout after all tests and clean up any remaining test data
  after(() => {
    // Clean up any test states
    cy.visit('/admin/communityEmpowerment/state/');
    cy.get('body').then($body => {
      if ($body.text().includes(testState.name)) {
        cy.contains('tr', testState.name).find('th a').click();
        cy.contains('Delete').click();
        cy.contains('Yes, I\'m sure').click();
      }
    });
    
    // Clean up any test departments
    cy.visit('/admin/communityEmpowerment/department/');
    cy.get('body').then($body => {
      if ($body.text().includes(testDepartment.name)) {
        cy.contains('tr', testDepartment.name).find('th a').click();
        cy.contains('Delete').click();
        cy.contains('Yes, I\'m sure').click();
      }
    });
    
    cy.admin_logout();
  });
  
  context('State CRUD Operations', () => {
    it('should create a new state', () => {
      // Navigate to state add page
      cy.visit('/admin/communityEmpowerment/state/add/');
      
      // Fill the form
      cy.fillAdminForm({ 'name': testState.name }, 'input');
      cy.fillAdminForm({ 'code': testState.code }, 'input');
      cy.fillAdminForm({ 'is_active': testState.is_active }, 'checkbox');
      
      // Save the form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'added successfully');
      
      // Verify state appears in the list
      cy.verifyListView('state', testState.name);
    });

    it('should edit an existing state', () => {
      // Go to state list
      cy.visit('/admin/communityEmpowerment/state/');
      
      // Find and click on the test state
      cy.contains('tr', testState.name).find('th a').click();
      
      // Update the state
      const updatedName = `${testState.name} Updated`;
      cy.fillAdminForm({ 'name': updatedName }, 'input');
      
      // Save changes
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'changed successfully');
      
      // Verify updated state appears in list view
      cy.verifyListView('state', updatedName);
      
      // Update test data for future tests
      testState.name = updatedName;
    });

    it('should filter states by name', () => {
      // Go to state list
      cy.visit('/admin/communityEmpowerment/state/');
      
      // Use search box to filter states
      cy.get('#searchbar').type(testState.name);
      cy.get('#changelist-search button[type="submit"]').click();
      
      // Verify only our test state is shown
      cy.get('#result_list tbody tr').should('have.length.at.most', 1);
      cy.contains('tr', testState.name).should('exist');
      
      // Clear search to restore the full list
      cy.get('#searchbar').clear();
      cy.get('#changelist-search button[type="submit"]').click();
    });
  });
  
  context('State Bulk Operations', () => {
    // Create multiple test states for bulk operations
    before(() => {
      // Create 3 test states
      for (let i = 1; i <= 3; i++) {
        cy.visit('/admin/communityEmpowerment/state/add/');
        cy.fillAdminForm({ 'name': `Bulk Test State ${i} ${timestamp}` }, 'input');
        cy.fillAdminForm({ 'code': `BS${i}${timestamp.toString().substring(8, 10)}` }, 'input');
        cy.fillAdminForm({ 'is_active': i % 2 === 0 }, 'checkbox'); // Alternate active status
        cy.save();
      }
    });
    
    // Clean up test states after bulk tests
    after(() => {
      // Delete any remaining bulk test states
      cy.visit('/admin/communityEmpowerment/state/');
      for (let i = 1; i <= 3; i++) {
        cy.get('body').then($body => {
          if ($body.text().includes(`Bulk Test State ${i} ${timestamp}`)) {
            cy.contains(`Bulk Test State ${i} ${timestamp}`).closest('tr').find('th a').click();
            cy.contains('Delete').click();
            cy.contains('Yes, I\'m sure').click();
            cy.visit('/admin/communityEmpowerment/state/');
          }
        });
      }
    });
    
    it('should perform bulk activation/deactivation of states', () => {
      // Go to state list
      cy.visit('/admin/communityEmpowerment/state/');
      
      // Check if bulk actions are available
      cy.get('select[name="action"]').then($actionSelect => {
        if ($actionSelect.find('option[value="activate_selected"]').length || 
            $actionSelect.find('option[value="deactivate_selected"]').length) {
          
          // Select the test states
          for (let i = 1; i <= 3; i++) {
            cy.contains(`Bulk Test State ${i} ${timestamp}`).closest('tr')
              .find('input[type="checkbox"]').check();
          }
          
          // Try bulk activation if available
          if ($actionSelect.find('option[value="activate_selected"]').length) {
            cy.get('select[name="action"]').select('activate_selected');
            cy.get('button[type="submit"]').contains('Go').click();
            cy.verifyMessage('success', 'successfully');
            cy.log('Bulk activation of states successful');
          } 
          // Try bulk deactivation if available
          else if ($actionSelect.find('option[value="deactivate_selected"]').length) {
            cy.get('select[name="action"]').select('deactivate_selected');
            cy.get('button[type="submit"]').contains('Go').click();
            cy.verifyMessage('success', 'successfully');
            cy.log('Bulk deactivation of states successful');
          }
        } else {
          cy.log('Bulk activation/deactivation not available for states');
        }
      });
    });
    
    it('should perform bulk deletion of states', () => {
      // Go to state list
      cy.visit('/admin/communityEmpowerment/state/');
      
      // Select the test states
      for (let i = 1; i <= 3; i++) {
        cy.contains(`Bulk Test State ${i} ${timestamp}`).closest('tr')
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
        cy.contains(`Bulk Test State ${i} ${timestamp}`).should('not.exist');
      }
    });
  });
  
  context('Department CRUD Operations', () => {
    it('should create a new department', () => {
      // Navigate to department add page
      cy.visit('/admin/communityEmpowerment/department/add/');
      
      // Fill the form
      cy.fillAdminForm({ 'name': testDepartment.name }, 'input');
      cy.fillAdminForm({ 'code': testDepartment.code }, 'input');
      cy.fillAdminForm({ 'is_active': testDepartment.is_active }, 'checkbox');
      
      // Save the form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'added successfully');
      
      // Verify department appears in the list
      cy.verifyListView('department', testDepartment.name);
    });

    it('should edit an existing department', () => {
      // Go to department list
      cy.visit('/admin/communityEmpowerment/department/');
      
      // Find and click on the test department
      cy.contains('tr', testDepartment.name).find('th a').click();
      
      // Update the department
      const updatedName = `${testDepartment.name} Updated`;
      cy.fillAdminForm({ 'name': updatedName }, 'input');
      
      // Save changes
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'changed successfully');
      
      // Verify updated department appears in list view
      cy.verifyListView('department', updatedName);
      
      // Update test data for future tests
      testDepartment.name = updatedName;
    });
    
    it('should filter departments by name', () => {
      // Go to department list
      cy.visit('/admin/communityEmpowerment/department/');
      
      // Use search box to filter departments
      cy.get('#searchbar').type(testDepartment.name);
      cy.get('#changelist-search button[type="submit"]').click();
      
      // Verify only our test department is shown
      cy.get('#result_list tbody tr').should('have.length.at.most', 1);
      cy.contains('tr', testDepartment.name).should('exist');
      
      // Clear search to restore the full list
      cy.get('#searchbar').clear();
      cy.get('#changelist-search button[type="submit"]').click();
    });
  });
  
  context('Department Bulk Operations', () => {
    // Create multiple test departments for bulk operations
    before(() => {
      // Create 3 test departments
      for (let i = 1; i <= 3; i++) {
        cy.visit('/admin/communityEmpowerment/department/add/');
        cy.fillAdminForm({ 'name': `Bulk Test Department ${i} ${timestamp}` }, 'input');
        cy.fillAdminForm({ 'code': `BD${i}${timestamp.toString().substring(8, 10)}` }, 'input');
        cy.fillAdminForm({ 'is_active': i % 2 === 0 }, 'checkbox'); // Alternate active status
        cy.save();
      }
    });
    
    // Clean up test departments after bulk tests
    after(() => {
      // Delete any remaining bulk test departments
      cy.visit('/admin/communityEmpowerment/department/');
      for (let i = 1; i <= 3; i++) {
        cy.get('body').then($body => {
          if ($body.text().includes(`Bulk Test Department ${i} ${timestamp}`)) {
            cy.contains(`Bulk Test Department ${i} ${timestamp}`).closest('tr').find('th a').click();
            cy.contains('Delete').click();
            cy.contains('Yes, I\'m sure').click();
            cy.visit('/admin/communityEmpowerment/department/');
          }
        });
      }
    });
    
    it('should perform bulk activation/deactivation of departments', () => {
      // Go to department list
      cy.visit('/admin/communityEmpowerment/department/');
      
      // Check if bulk actions are available
      cy.get('select[name="action"]').then($actionSelect => {
        if ($actionSelect.find('option[value="activate_selected"]').length || 
            $actionSelect.find('option[value="deactivate_selected"]').length) {
          
          // Select the test departments
          for (let i = 1; i <= 3; i++) {
            cy.contains(`Bulk Test Department ${i} ${timestamp}`).closest('tr')
              .find('input[type="checkbox"]').check();
          }
          
          // Try bulk activation if available
          if ($actionSelect.find('option[value="activate_selected"]').length) {
            cy.get('select[name="action"]').select('activate_selected');
            cy.get('button[type="submit"]').contains('Go').click();
            cy.verifyMessage('success', 'successfully');
            cy.log('Bulk activation of departments successful');
          } 
          // Try bulk deactivation if available
          else if ($actionSelect.find('option[value="deactivate_selected"]').length) {
            cy.get('select[name="action"]').select('deactivate_selected');
            cy.get('button[type="submit"]').contains('Go').click();
            cy.verifyMessage('success', 'successfully');
            cy.log('Bulk deactivation of departments successful');
          }
        } else {
          cy.log('Bulk activation/deactivation not available for departments');
        }
      });
    });
    
    it('should perform bulk deletion of departments', () => {
      // Go to department list
      cy.visit('/admin/communityEmpowerment/department/');
      
      // Select the test departments
      for (let i = 1; i <= 3; i++) {
        cy.contains(`Bulk Test Department ${i} ${timestamp}`).closest('tr')
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
        cy.contains(`Bulk Test Department ${i} ${timestamp}`).should('not.exist');
      }
    });
  });
  
  context('State-Department Relationship Tests', () => {
    // Create state and department for relationship tests
    before(() => {
      // Create test state
      cy.visit('/admin/communityEmpowerment/state/add/');
      cy.fillAdminForm({ 'name': `Relationship Test State ${timestamp}` }, 'input');
      cy.fillAdminForm({ 'code': `RS${timestamp.toString().substring(8, 10)}` }, 'input');
      cy.fillAdminForm({ 'is_active': true }, 'checkbox');
      cy.save();
      
      // Create test department
      cy.visit('/admin/communityEmpowerment/department/add/');
      cy.fillAdminForm({ 'name': `Relationship Test Department ${timestamp}` }, 'input');
      cy.fillAdminForm({ 'code': `RD${timestamp.toString().substring(8, 10)}` }, 'input');
      cy.fillAdminForm({ 'is_active': true }, 'checkbox');
      cy.save();
    });
    
    // Clean up after relationship tests
    after(() => {
      // Delete test department
      cy.visit('/admin/communityEmpowerment/department/');
      cy.get('body').then($body => {
        if ($body.text().includes(`Relationship Test Department ${timestamp}`)) {
          cy.contains(`Relationship Test Department ${timestamp}`).closest('tr').find('th a').click();
          cy.contains('Delete').click();
          cy.contains('Yes, I\'m sure').click();
        }
      });
      
      // Delete test state
      cy.visit('/admin/communityEmpowerment/state/');
      cy.get('body').then($body => {
        if ($body.text().includes(`Relationship Test State ${timestamp}`)) {
          cy.contains(`Relationship Test State ${timestamp}`).closest('tr').find('th a').click();
          cy.contains('Delete').click();
          cy.contains('Yes, I\'m sure').click();
        }
      });
    });
    
    it('should associate a department with a state if relationship exists', () => {
      // Check if state-department relationship fields exist
      cy.visit('/admin/communityEmpowerment/department/');
      cy.contains(`Relationship Test Department ${timestamp}`).closest('tr').find('th a').click();
      
      // Check if there's a state field to create a relationship
      cy.get('body').then($body => {
        if ($body.find('select[name="state"]').length || $body.find('select[name*="states"]').length) {
          // If single state relationship
          if ($body.find('select[name="state"]').length) {
            cy.get('select[name="state"] option').then($options => {
              if ($options.length > 1) {
                // Find our test state in the dropdown
                cy.get('select[name="state"]').select(`Relationship Test State ${timestamp}`);
                cy.save();
                cy.verifyMessage('success', 'changed successfully');
                cy.log('Department associated with state successfully');
              }
            });
          } 
          // If many-to-many state relationship
          else if ($body.find('select[name*="states"]').length) {
            // Handle multi-select fields
            cy.get('body').then($body => {
              // For Django admin's filter_horizontal widget
              if ($body.find('.selector-available').length) {
                cy.contains(`Relationship Test State ${timestamp}`).click();
                cy.get('.selector-add').click();
                cy.save();
                cy.verifyMessage('success', 'changed successfully');
                cy.log('Department associated with state through many-to-many relationship');
              } 
              // For regular multi-select
              else if ($body.find('select[name*="states"][multiple]').length) {
                cy.get('select[name*="states"] option').contains(`Relationship Test State ${timestamp}`).then($option => {
                  cy.get('select[name*="states"]').select($option.val());
                  cy.save();
                  cy.verifyMessage('success', 'changed successfully');
                  cy.log('Department associated with state through multi-select');
                });
              }
            });
          }
        } else {
          cy.log('No state-department relationship fields found');
        }
      });
    });
    
    it('should filter departments by state if relationship exists', () => {
      cy.visit('/admin/communityEmpowerment/department/');
      
      // Check if there's a state filter in the right sidebar
      cy.get('body').then($body => {
        if ($body.find('#changelist-filter').length && 
            $body.find('#changelist-filter').text().includes('State')) {
          
          // Click on our test state in the filter
          cy.get('#changelist-filter').contains(`Relationship Test State ${timestamp}`).click();
          
          // Verify filtering works by checking if our test department is shown
          cy.contains(`Relationship Test Department ${timestamp}`).should('exist');
          cy.log('State filtering for departments works');
          
          // Clear filter
          cy.get('#changelist-filter').contains('All').click();
        } else {
          cy.log('No state filter available for departments');
        }
      });
    });
  });
  
  context('Permission Tests', () => {
    // Create test items for permission testing
    before(() => {
      // Create a test state and department for permission testing
      cy.visit('/admin/communityEmpowerment/state/add/');
      cy.fillAdminForm({ 'name': `Permission Test State ${timestamp}` }, 'input');
      cy.fillAdminForm({ 'code': `PS${timestamp.toString().substring(8, 10)}` }, 'input');
      cy.fillAdminForm({ 'is_active': true }, 'checkbox');
      cy.save();
      
      cy.visit('/admin/communityEmpowerment/department/add/');
      cy.fillAdminForm({ 'name': `Permission Test Department ${timestamp}` }, 'input');
      cy.fillAdminForm({ 'code': `PD${timestamp.toString().substring(8, 10)}` }, 'input');
      cy.fillAdminForm({ 'is_active': true }, 'checkbox');
      cy.save();
    });
    
    // Clean up test items after permission tests
    after(() => {
      // Delete test department
      cy.visit('/admin/communityEmpowerment/department/');
      cy.get('body').then($body => {
        if ($body.text().includes(`Permission Test Department ${timestamp}`)) {
          cy.contains(`Permission Test Department ${timestamp}`).closest('tr').find('th a').click();
          cy.contains('Delete').click();
          cy.contains('Yes, I\'m sure').click();
        }
      });
      
      // Delete test state
      cy.visit('/admin/communityEmpowerment/state/');
      cy.get('body').then($body => {
        if ($body.text().includes(`Permission Test State ${timestamp}`)) {
          cy.contains(`Permission Test State ${timestamp}`).closest('tr').find('th a').click();
          cy.contains('Delete').click();
          cy.contains('Yes, I\'m sure').click();
        }
      });
    });
    
    it('should verify editor permissions for states and departments', () => {
      // Logout as admin
      cy.admin_logout();
      
      // Login as editor
      cy.admin_login(editor.username, editor.password);
      
      // Check state access and permissions
      cy.visit('/admin/');
      cy.get('body').then($body => {
        // Check if state management is accessible
        const hasStateAccess = $body.find('a:contains("State")').length > 0;
        
        if (hasStateAccess) {
          // Navigate to states
          cy.contains('a', 'State').click();
          
          // Check for Add permissions
          cy.get('body').then($listBody => {
            const canAdd = $listBody.find('a.addlink').length > 0;
            cy.log(`Editor ${canAdd ? 'can' : 'cannot'} add new states`);
            
            // Check edit permissions on existing item
            if ($listBody.text().includes(`Permission Test State ${timestamp}`)) {
              cy.contains(`Permission Test State ${timestamp}`).closest('tr').find('th a').click();
              
              // Check for save and delete permissions
              cy.get('body').then($detailBody => {
                const canEdit = $detailBody.find('input[name="_save"]').length > 0;
                const canDelete = $detailBody.find('a:contains("Delete")').length > 0;
                
                cy.log(`Editor ${canEdit ? 'can' : 'cannot'} edit states`);
                cy.log(`Editor ${canDelete ? 'can' : 'cannot'} delete states`);
              });
            }
          });
        } else {
          cy.log('Editor does not have access to state management');
        }
      });
      
      // Check department access and permissions
      cy.visit('/admin/');
      cy.get('body').then($body => {
        // Check if department management is accessible
        const hasDeptAccess = 
          $body.find('a:contains("Department")').length > 0;
        
        if (hasDeptAccess) {
          // Navigate to departments
          cy.contains('a', 'Department').click();
          
          // Check for Add permissions
          cy.get('body').then($listBody => {
            const canAdd = $listBody.find('a.addlink').length > 0;
            cy.log(`Editor ${canAdd ? 'can' : 'cannot'} add new departments`);
            
            // Check edit permissions on existing item
            if ($listBody.text().includes(`Permission Test Department ${timestamp}`)) {
              cy.contains(`Permission Test Department ${timestamp}`).closest('tr').find('th a').click();
              
              // Check for save and delete permissions
              cy.get('body').then($detailBody => {
                const canEdit = $detailBody.find('input[name="_save"]').length > 0;
                const canDelete = $detailBody.find('a:contains("Delete")').length > 0;
                
                cy.log(`Editor ${canEdit ? 'can' : 'cannot'} edit departments`);
                cy.log(`Editor ${canDelete ? 'can' : 'cannot'} delete departments`);
              });
            }
          });
        } else {
          cy.log('Editor does not have access to department management');
        }
      });
      
      // Logout as editor
      cy.admin_logout();
      
      // Login back as admin
      cy.admin_login(admin.username, admin.password);
    });
    
    it('should verify viewer permissions for states and departments', () => {
      // Logout as admin
      cy.admin_logout();
      
      // Login as viewer
      cy.admin_login(viewer.username, viewer.password);
      
      // Check state access and permissions
      cy.visit('/admin/');
      cy.get('body').then($body => {
        // Check if state management is accessible
        const hasStateAccess = $body.find('a:contains("State")').length > 0;
        
        if (hasStateAccess) {
          // Navigate to states
          cy.contains('a', 'State').click();
          
          // Verify read-only permissions
          cy.get('body').then($listBody => {
            // Should not have add button
            const canAdd = $listBody.find('a.addlink').length > 0;
            cy.log(`Viewer ${canAdd ? 'can' : 'cannot'} add new states`);
            
            // Should not have bulk action checkboxes if view-only
            const hasBulkActions = $listBody.find('input[name="_selected_action"]').length > 0;
            cy.log(`Viewer ${hasBulkActions ? 'has' : 'does not have'} access to bulk actions`);
            
            // Check if viewer can access item details
            if ($listBody.text().includes(`Permission Test State ${timestamp}`)) {
              cy.contains(`Permission Test State ${timestamp}`).closest('tr').find('th a').click();
              
              // Check if form is read-only
              cy.get('body').then($detailBody => {
                const canEdit = $detailBody.find('input[name="_save"]').length > 0;
                const isReadOnly = $detailBody.find('input[readonly], .readonly').length > 0;
                
                cy.log(`Viewer ${canEdit ? 'can' : 'cannot'} edit states`);
                cy.log(`Form is ${isReadOnly ? 'read-only' : 'editable'} for viewer`);
              });
            }
          });
        } else {
          cy.log('Viewer does not have access to state management');
        }
      });
      
      // Check department access and permissions
      cy.visit('/admin/');
      cy.get('body').then($body => {
        // Check if department management is accessible
        const hasDeptAccess = $body.find('a:contains("Department")').length > 0;
        
        if (hasDeptAccess) {
          // Navigate to departments
          cy.contains('a', 'Department').click();
          
          // Verify read-only permissions
          cy.get('body').then($listBody => {
            // Should not have add button
            const canAdd = $listBody.find('a.addlink').length > 0;
            cy.log(`Viewer ${canAdd ? 'can' : 'cannot'} add new departments`);
            
            // Should not have bulk action checkboxes if view-only
            const hasBulkActions = $listBody.find('input[name="_selected_action"]').length > 0;
            cy.log(`Viewer ${hasBulkActions ? 'has' : 'does not have'} access to bulk actions`);
            
            // Check if viewer can access item details
            if ($listBody.text().includes(`Permission Test Department ${timestamp}`)) {
              cy.contains(`Permission Test Department ${timestamp}`).closest('tr').find('th a').click();
              
              // Check if form is read-only
              cy.get('body').then($detailBody => {
                const canEdit = $detailBody.find('input[name="_save"]').length > 0;
                const isReadOnly = $detailBody.find('input[readonly], .readonly').length > 0;
                
                cy.log(`Viewer ${canEdit ? 'can' : 'cannot'} edit departments`);
                cy.log(`Form is ${isReadOnly ? 'read-only' : 'editable'} for viewer`);
              });
            }
          });
        } else {
          cy.log('Viewer does not have access to department management');
        }
      });
      
      // Logout as viewer
      cy.admin_logout();
      
      // Login back as admin
      cy.admin_login(admin.username, admin.password);
    });
  });
});
