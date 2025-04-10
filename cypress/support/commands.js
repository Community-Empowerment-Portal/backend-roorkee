// Add timeout configurations
const DEFAULT_TIMEOUT = 10000;

// Helper function to get user configuration
const getUserConfig = (userType) => {
  return cy.fixture('admin-test-users.json').then(data => data.users[userType]);
};

// Login command with enhanced error handling
Cypress.Commands.add('admin_login', (username, password) => {
  cy.visit('/login/');
  cy.get('input[name="username"]', { timeout: DEFAULT_TIMEOUT })
    .should('exist')
    .clear()
    .type(username);
  cy.get('input[name="password"]', { timeout: DEFAULT_TIMEOUT })
    .should('exist')
    .clear()
    .type(password);
  cy.get('input[type="submit"]').click();
  
  // Verify login success with enhanced checks
  cy.get('#user-tools', { timeout: DEFAULT_TIMEOUT })
    .should('exist')
    .and('contain', username);
  
  // Additional verification based on user type
  if (username !== 'admin') {
    getUserConfig(username).then(config => {
      // Verify accessible sections
      config.expectedUi.accessibleSections.forEach(section => {
        cy.get('#content-main').should('contain', section);
      });
    });
  }
});

// Enhanced permission verification command
Cypress.Commands.add('verifyPermissions', (userType, modelType) => {
  getUserConfig(userType).then(config => {
    const permissions = config.permissions;
    const expectedUi = config.expectedUi;

    // Check add permission
    if (Array.isArray(permissions.canAdd)) {
      const canAdd = permissions.canAdd.includes(modelType) || permissions.canAdd.includes('*');
      cy.get('a.addlink').should(canAdd ? 'exist' : 'not.exist');
    }

    // Check change permission
    if (Array.isArray(permissions.canChange)) {
      const canChange = permissions.canChange.includes(modelType) || permissions.canChange.includes('*');
      cy.get('input[name="_save"]').should(canChange ? 'exist' : 'not.exist');
    }

    // Check delete permission
    if (Array.isArray(permissions.canDelete)) {
      const canDelete = permissions.canDelete.includes(modelType) || permissions.canDelete.includes('*');
      cy.get('a:contains("Delete")').should(canDelete ? 'exist' : 'not.exist');
    }

    // Check inline editing permissions
    if (typeof expectedUi.canEditInlineFields === 'object') {
      Object.entries(expectedUi.canEditInlineFields)
        .filter(([key]) => key.startsWith(modelType))
        .forEach(([key, canEdit]) => {
          const field = key.split('.')[1];
          cy.get(`input[name*="${field}"]`).should(canEdit ? 'not.be.disabled' : 'be.disabled');
        });
    }
  });
});

// Enhanced form filling command
Cypress.Commands.add('fillAdminForm', (fields, fieldType) => {
  Object.entries(fields).forEach(([selector, value]) => {
    cy.get('body').then($body => {
      const fieldSelector = `${fieldType}[name="${selector}"]`;
      if ($body.find(fieldSelector).length) {
        switch(fieldType) {
          case 'input':
          case 'textarea':
            cy.get(fieldSelector)
              .should('be.visible')
              .clear()
              .type(value, { delay: 50 });
            break;
          case 'select':
            cy.get(fieldSelector)
              .should('be.visible')
              .select(value);
            break;
          case 'checkbox':
            const checkbox = cy.get(`input[name="${selector}"][type="checkbox"]`);
            value ? checkbox.check() : checkbox.uncheck();
            break;
        }
      } else {
        cy.log(`Field ${selector} not found in form`);
      }
    });
  });
});

// Command to verify UI elements based on user role
Cypress.Commands.add('verifyUserInterface', (userType) => {
  getUserConfig(userType).then(config => {
    const expectedUi = config.expectedUi;

    // Check each UI element
    cy.get('body').then($body => {
      // Check add buttons
      if (typeof expectedUi.hasAddButtons === 'object') {
        Object.entries(expectedUi.hasAddButtons).forEach(([model, hasButton]) => {
          const addLink = $body.find(`a.addlink:contains("Add ${model}")`);
          expect(addLink.length > 0).to.equal(hasButton);
        });
      } else {
        cy.get('a.addlink').should(expectedUi.hasAddButtons ? 'exist' : 'not.exist');
      }

      // Check other UI elements
      cy.get('input[name="_save"]').should(expectedUi.hasSaveButtons ? 'exist' : 'not.exist');
      cy.get('a:contains("Delete")').should(expectedUi.hasDeleteButtons ? 'exist' : 'not.exist');
      cy.get('#changelist-filter').should(expectedUi.hasListFilters ? 'exist' : 'not.exist');
      cy.get('select[name="action"]').should(expectedUi.hasBulkActions ? 'exist' : 'not.exist');
    });
  });
});

// Admin logout command
Cypress.Commands.add('admin_logout', () => {
  cy.visit('/logout/');
  cy.url().should('include', '/login/');
  // Verify logout success
  cy.get('input[name="username"]').should('exist');
});

// Message verification command
Cypress.Commands.add('verifyMessage', (type, message) => {
  if (type === 'success') {
    cy.get('.messagelist', { timeout: DEFAULT_TIMEOUT })
      .should('exist')
      .and('contain', message);
  } else if (type === 'error') {
    cy.get('.errornote, .errorlist', { timeout: DEFAULT_TIMEOUT })
      .should('exist')
      .and('contain', message);
  }
});

// Command to check permissions
Cypress.Commands.add('checkPermission', (selector, shouldExist, message) => {
  cy.get('body').then($body => {
    const exists = $body.find(selector).length > 0;
    expect(exists).to.equal(shouldExist, message || `Expected ${selector} to ${shouldExist ? 'exist' : 'not exist'}`);
  });
});

// Command to verify item in list view
Cypress.Commands.add('verifyListView', (model, itemText) => {
  cy.visit(`/communityEmpowerment/${model}/`);
  cy.get('#result_list').should('contain', itemText);
});

// Command to save a form
Cypress.Commands.add('save', () => {
  cy.get('input[name="_save"]').click();
});

// Command to select items in admin many-to-many widget
Cypress.Commands.add('selectAdminManyToMany', (field, itemText) => {
  // Handle the Django admin filtered select widget
  cy.get(`.field-${field} .selector-available select option`).contains(itemText).then($option => {
    if ($option.length) {
      $option.prop('selected', true);
      cy.get(`.field-${field} .selector-add`).click();
    }
  });
});

// Wait for Django admin page to load
Cypress.Commands.add('waitForDjangoAdmin', () => {
  cy.get('#content', { timeout: DEFAULT_TIMEOUT }).should('exist');
  cy.get('body').should('not.have.class', 'loading');
});

// Setup test user
Cypress.Commands.add('setupTestUser', (role) => {
  return cy.fixture('admin-test-users.json').then(
    (userData) => ({
      userConfig: userData.users[role] || { username: role, password: `${role}password` }
    }),
    () => ({
      userConfig: { username: role, password: `${role}password` }
    })
  );
});

// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

// -- Admin Interface Commands --

/**
 * Admin login command
 * Logs in to the Django admin interface
 */
Cypress.Commands.add('admin_login', (username, password) => {
  cy.visit('/login/');
  cy.get('input[name="username"]').type(username);
  cy.get('input[name="password"]').type(password);
  cy.get('input[type="submit"]').click();
  cy.url().should('include', '/admin/');
});

/**
 * Admin logout command
 * Logs out of the Django admin interface
 */
Cypress.Commands.add('admin_logout',()=>{
    cy.contains('Log out').should('be.visible').click()
})

/**
 * Form filling helper
 * Fills form fields in Django admin based on field type
 */
Cypress.Commands.add('fillAdminForm', (fields, fieldType) => {
  Object.entries(fields).forEach(([selector, value]) => {
    if (fieldType === 'input') {
      cy.get(`input[name="${selector}"]`).clear().type(value);
    } else if (fieldType === 'textarea') {
      cy.get(`textarea[name="${selector}"]`).clear().type(value);
    } else if (fieldType === 'select') {
      cy.get(`select[name="${selector}"]`).select(value);
    } else if (fieldType === 'checkbox') {
      if (value) {
        cy.get(`input[name="${selector}"]`).check();
      } else {
        cy.get(`input[name="${selector}"]`).uncheck();
      }
    }
  });
});

/**
 * Save form helper
 * Clicks the save button in Django admin forms
 */
Cypress.Commands.add('save', () => {
  cy.get('input[name="_save"]').click();
});

/**
 * Message verification helper
 * Verifies success/error messages in Django admin
 */
Cypress.Commands.add('verifyMessage', (type, message) => {
  if (type === 'success') {
    cy.get('.messagelist .success').should('contain', message);
  } else if (type === 'error') {
    cy.get('.errornote').should('contain', message);
  }
});

/**
 * List view verification helper
 * Verifies if a record exists in a list view
 */
Cypress.Commands.add('verifyListView', (model, recordName, shouldExist = true) => {
  cy.visit(`/admin/communityEmpowerment/${model}/`);
  if (shouldExist) {
    cy.contains(recordName).should('exist');
  } else {
    cy.contains(recordName).should('not.exist');
  }
});

/**
 * Permission check helper
 * Verifies if a user has permission to access an element
 */
Cypress.Commands.add('checkPermission', (selector, shouldExist, message) => {
  cy.get('body').then($body => {
    const exists = $body.find(selector).length > 0;
    if (shouldExist) {
      expect(exists, message).to.be.true;
    } else {
      expect(exists, message).to.be.false;
    }
  });
});

/**
 * Select items in Django admin's many-to-many widget
 * Handles both standard admin filter_horizontal widget and custom widgets
 * @param {string} fieldName - The name of the many-to-many field
 * @param {string} itemName - The name of the item to select
 */
Cypress.Commands.add('selectAdminManyToMany', (fieldName, itemName) => {
  // Check if the field exists
  cy.get('body').then($body => {
    // Standard Django admin filter_horizontal widget
    if ($body.find(`.field-${fieldName} .selector-available select`).length) {
      // Find the item in the available list
      cy.get(`.field-${fieldName} .selector-available select option`).contains(itemName).then($option => {
        if ($option.length) {
          // Select the option
          cy.get(`.field-${fieldName} .selector-available select`).select($option.val());
          
          // Click the "Add" button to move it to chosen
          cy.get(`.field-${fieldName} .selector-add`).click();
          
          // Verify the item is now in the chosen list
          cy.get(`.field-${fieldName} .selector-chosen select option`).contains(itemName).should('exist');
        } else {
          cy.log(`Item "${itemName}" not found in available options for ${fieldName}`);
        }
      });
    } 
    // Alternative: Some Django admin may use regular select for M2M
    else if ($body.find(`select[name="${fieldName}"]`).length) {
      cy.get(`select[name="${fieldName}"] option`).contains(itemName).then($option => {
        if ($option.length) {
          cy.get(`select[name="${fieldName}"]`).select($option.val());
        } else {
          cy.log(`Item "${itemName}" not found in select options for ${fieldName}`);
        }
      });
    }
    // Alternative: Custom widgets may use checkboxes or other elements
    else if ($body.find(`input[name="${fieldName}"]`).length) {
      cy.contains(itemName).closest('tr').find('input[type="checkbox"]').check();
    }
    // Log if we can't find a matching widget
    else {
      cy.log(`Could not find a many-to-many widget for field ${fieldName}`);
    }
  });
});

/**
 * Verify selected items in Django admin's many-to-many widget
 * @param {string} fieldName - The name of the many-to-many field
 * @param {string} itemName - The name of the item to verify
 */
Cypress.Commands.add('verifyAdminManyToMany', (fieldName, itemName) => {
  cy.get('body').then($body => {
    // Standard Django admin filter_horizontal widget
    if ($body.find(`.field-${fieldName} .selector-chosen select`).length) {
      cy.get(`.field-${fieldName} .selector-chosen select option`).contains(itemName).should('exist');
    }
    // Regular multi-select
    else if ($body.find(`select[name="${fieldName}"]`).length) {
      cy.get(`select[name="${fieldName}"] option:selected`).contains(itemName).should('exist');
    }
    // Custom widget with checkboxes
    else if ($body.find(`input[name="${fieldName}"]`).length) {
      cy.contains(itemName).closest('tr').find('input[type="checkbox"]:checked').should('exist');
    }
    // Read-only display often used in detail views
    else if ($body.find(`.field-${fieldName} .readonly`).length) {
      cy.get(`.field-${fieldName} .readonly`).should('contain', itemName);
    }
    // Read-only display often used in detail views
    else if ($body.find(`.field-${fieldName} .readonly`).length) {
      cy.get(`.field-${fieldName} .readonly`).should('contain', itemName);
    }
    // If we can't find a matching widget
    else {
      cy.log(`Could not find a matching widget for field ${fieldName}`);
    }
  });
});

/**
 * Create a complete scheme with all associated components
 * @param {Object} schemeData - Basic scheme information
 * @param {Object} components - Components to associate with the scheme
 * @returns {Promise<string>} - Promise resolving to the created scheme ID
 */
Cypress.Commands.add('createCompleteScheme', (schemeData, components = {}) => {
  cy.visit('/admin/communityEmpowerment/scheme/add/');
  
  // Fill basic scheme information
  cy.fillAdminForm({ 'name': schemeData.name }, 'input');
  cy.fillAdminForm({ 'short_description': schemeData.short_description }, 'textarea');
  
  if (schemeData.detailed_description) {
    cy.fillAdminForm({ 'detailed_description': schemeData.detailed_description }, 'textarea');
  }
  
  if (schemeData.objectives) {
    cy.fillAdminForm({ 'objectives': schemeData.objectives }, 'textarea');
  }
  
  // Set dates if provided
  if (schemeData.start_date) {
    cy.fillAdminForm({ 'start_date': schemeData.start_date }, 'input');
  }
  
  if (schemeData.application_deadline) {
    cy.fillAdminForm({ 'application_deadline': schemeData.application_deadline }, 'input');
  }
  
  // Set status
  if (schemeData.hasOwnProperty('is_active')) {
    cy.fillAdminForm({ 'is_active': schemeData.is_active }, 'checkbox');
  }
  
  // Add relationships using the handleSchemeRelations command
  cy.handleSchemeRelations(components);
  
  // Save the scheme
  cy.save();
  cy.verifyMessage('success', 'added successfully');
  
  // Return the created scheme ID
  return cy.url().then(url => {
    const schemeId = url.split('/').filter(Boolean).pop();
    return schemeId;
  });
});

/**
 * Verify all components of a scheme are correctly associated
 * @param {string} schemeId - The ID of the scheme to verify
 * @param {Object} components - Object containing expected component names for each relationship
 */
Cypress.Commands.add('verifySchemeComponents', (schemeId, components) => {
  cy.visit(`/admin/communityEmpowerment/scheme/${schemeId}/change/`);
  
  // Check each component type if provided
  if (components.benefits) {
    components.benefits.forEach(benefit => {
      cy.verifyAdminManyToMany('benefits', benefit);
    });
  }
  
  if (components.criteria) {
    components.criteria.forEach(criterion => {
      cy.verifyAdminManyToMany('criteria', criterion);
    });
  }
  
  if (components.documents) {
    components.documents.forEach(document => {
      cy.verifyAdminManyToMany('documents', document);
    });
  }
  
  if (components.tags) {
    components.tags.forEach(tag => {
      cy.verifyAdminManyToMany('tags', tag);
    });
  }
  
  if (components.procedures) {
    components.procedures.forEach(procedure => {
      cy.verifyAdminManyToMany('procedures', procedure);
    });
  }
  
  if (components.states) {
    components.states.forEach(state => {
      cy.verifyAdminManyToMany('states', state);
    });
  }
  
  if (components.departments) {
    components.departments.forEach(department => {
      cy.verifyAdminManyToMany('departments', department);
    });
  }
  
  if (components.organisations) {
    components.organisations.forEach(organisation => {
      cy.verifyAdminManyToMany('organisations', organisation);
    });
  }
  
  if (components.scheme_beneficiaries) {
    components.scheme_beneficiaries.forEach(beneficiary => {
      cy.verifyAdminManyToMany('scheme_beneficiaries', beneficiary);
    });
  }
  
  if (components.scheme_sponsors) {
    components.scheme_sponsors.forEach(sponsor => {
      cy.verifyAdminManyToMany('scheme_sponsors', sponsor);
    });
  }
  
  if (components.resources) {
    components.resources.forEach(resource => {
      cy.verifyAdminManyToMany('resources', resource);
    });
  }
});

/**
 * Check comprehensive scheme validation
 * @param {Object} schemeData - Basic scheme data to fill in form
 * @param {Object} validationTests - Types of validation to perform
 */
Cypress.Commands.add('checkSchemeValidation', (schemeData, validationTests) => {
  cy.visit('/admin/communityEmpowerment/scheme/add/');
  
  // Test required fields
  if (validationTests.requiredFields) {
    // Try to save without entering any data
    cy.save();
    cy.get('.errornote').should('exist');
    cy.get('.field-name .errorlist').should('exist');
  }
  
  // Test duplicate name
  if (validationTests.uniqueName) {
    cy.fillAdminForm({ 'name': validationTests.uniqueName }, 'input');
    cy.save();
    cy.get('.errornote').should('exist');
    cy.get('.field-name .errorlist').should('exist');
  }
  
  // Test required relationships
  if (validationTests.requiredRelationships) {
    // Fill basic fields but not relationships
    cy.fillAdminForm({ 'name': schemeData.name }, 'input');
    cy.fillAdminForm({ 'short_description': schemeData.short_description }, 'textarea');
    cy.fillAdminForm({ 'detailed_description': schemeData.detailed_description }, 'textarea');
    cy.save();
    
    // Check for relationship validation errors
    cy.get('.errornote').should('exist');
    
    // Verify specific relationship field errors
    validationTests.requiredRelationships.forEach(relationshipField => {
      cy.get(`.field-${relationshipField} .errorlist`).should('exist');
    });
  }
  
  // Test date validation if needed
  if (validationTests.dateValidation) {
    // Fill basic fields
    cy.fillAdminForm({ 'name': schemeData.name }, 'input');
    cy.fillAdminForm({ 'short_description': schemeData.short_description }, 'textarea');
    
    // Test invalid dates
    if (validationTests.dateValidation.invalidStartDate) {
      cy.fillAdminForm({ 'start_date': validationTests.dateValidation.invalidStartDate }, 'input');
      cy.save();
      cy.get('.field-start_date .errorlist').should('exist');
    }
    
    if (validationTests.dateValidation.invalidEndDate) {
      cy.fillAdminForm({ 'start_date': schemeData.start_date }, 'input');
      cy.fillAdminForm({ 'application_deadline': validationTests.dateValidation.invalidEndDate }, 'input');
      cy.save();
      cy.get('.field-application_deadline .errorlist').should('exist');
    }
    
    // Test end date before start date if model validates this
    if (validationTests.dateValidation.endBeforeStart) {
      cy.fillAdminForm({ 'start_date': '2025-12-31' }, 'input');
      cy.fillAdminForm({ 'application_deadline': '2025-01-01' }, 'input');
      cy.save();
      cy.get('.errornote').should('exist');
    }
  }
});

/**
 * Handle scheme relationships in a single command
 * @param {Object} relationships - Object with relationship types and values to set
 */
Cypress.Commands.add('handleSchemeRelations', (relationships) => {
  // Handle each relationship type
  Object.entries(relationships).forEach(([relationshipType, items]) => {
    // If items is an array, add each item
    if (Array.isArray(items)) {
      items.forEach(item => {
        cy.selectAdminManyToMany(relationshipType, item);
      });
    } 
    // If it's a single string, just add that one
    else if (typeof items === 'string') {
      cy.selectAdminManyToMany(relationshipType, items);
    }
  });
});

/**
 * Clean up test data created for scheme testing
 * @param {Object} records - Object with record IDs for each model type
 */
Cypress.Commands.add('cleanupSchemeData', (records) => {
  cy.log('Cleaning up scheme test data');
  
  // Ensure admin is logged in for cleanup
  cy.get('body').then($body => {
    if (!$body.find('a:contains("Log out")').length) {
      // Need to log in first
      cy.task('getAdminCredentials').then(credentials => {
        cy.admin_login(credentials.username, credentials.password);
      });
    }
  });
  
  // Delete scheme first (to preserve foreign key integrity)
  if (records.scheme) {
    cy.visit(`/admin/communityEmpowerment/scheme/${records.scheme}/delete/`);
    cy.contains('Yes, I\'m sure').click();
    cy.verifyMessage('success', 'deleted successfully');
  }
  
  // Define deletion order to respect dependencies
  const deleteOrder = [
    'resource',
    'schemesponsor',
    'schemebeneficiary',
    'procedure',
    'criteria',
    'benefit',
    'document',
    'tag',
    'organisation',
    'department',
    'state',
    'companymeta'
  ];
  
  // Delete each record type if it exists
  deleteOrder.forEach(recordType => {
    if (records[recordType]) {
      cy.visit(`/admin/communityEmpowerment/${recordType}/${records[recordType]}/delete/`);
      cy.contains('Yes, I\'m sure').click();
      
      // Check if deletion was successful
      cy.get('body').then($body => {
        if ($body.find('.messagelist .success:contains("deleted successfully")').length) {
          cy.log(`Successfully deleted ${recordType} record`);
        } else if ($body.find('.errornote').length) {
          cy.log(`Error deleting ${recordType}: ${$body.find('.errornote').text()}`);
          
          // Check for protected foreign key errors
          if ($body.find('.errornote:contains("protected")').length) {
            cy.log(`Foreign key constraint prevented deletion of ${recordType}`);
          }
        }
      });
    }
  });
});
