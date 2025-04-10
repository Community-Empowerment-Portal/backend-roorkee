// ***********************************************
// Custom Cypress Commands for Django Admin Testing
// ***********************************************

const DEFAULT_TIMEOUT = 10000;

/**
 * Helper: Fetch user configuration from fixture
 */
const getUserConfig = (userType) => {
  return cy.fixture('admin-test-users.json').then(data => data.users[userType]);
};

// ===============================
// Login / Logout Commands
// ===============================

/**
 * Logs in to the Django admin panel
 */
Cypress.Commands.add('admin_login', (username, password) => {
  cy.visit('/login/');
  cy.get('input[name="username"]', { timeout: DEFAULT_TIMEOUT }).should('exist').clear().type(username);
  cy.get('input[name="password"]', { timeout: DEFAULT_TIMEOUT }).should('exist').clear().type(password);
  cy.get('input[type="submit"]').click();
  cy.get('#user-tools', { timeout: DEFAULT_TIMEOUT }).should('contain', username);

  // Additional UI checks for non-admin users
  if (username !== 'admin') {
    getUserConfig(username).then(config => {
      config.expectedUi.accessibleSections.forEach(section => {
        cy.get('#content-main').should('contain', section);
      });
    });
  }
});

/**
 * Logs out of the Django admin panel
 */
Cypress.Commands.add('admin_logout', () => {
  cy.visit('/logout/');
  cy.url().should('include', '/login/');
  cy.get('input[name="username"]').should('exist');
});

// ===============================
// Form Commands
// ===============================

/**
 * Fills admin form fields (input, textarea, select, checkbox)
 */
Cypress.Commands.add('fillAdminForm', (fields, fieldType) => {
    cy.log(fields, fieldType)
  Object.entries(fields).forEach(([name, value]) => {
    cy.log(name, value)
    cy.get('body').then($body => {
      const selector = `${fieldType}[name="${name}"]`;
      if ($body.find(selector).length) {
        switch (fieldType) {
          case 'input':
          case 'textarea':
            cy.get(selector).should('be.visible').clear().type(value, { delay: 50 });
            break;
          case 'select':
            cy.get(selector).should('be.visible').select(value);
            break;
          case 'checkbox':
            value
              ? cy.get(`input[name="${name}"][type="checkbox"]`).check()
              : cy.get(`input[name="${name}"][type="checkbox"]`).uncheck();
            break;
        }
      } else {
        cy.log(`Field ${name} not found`);
      }
    });
  });
});

/**
 * Clicks the "Save" button in admin forms
 */
Cypress.Commands.add('save', () => {
  cy.get('input[name="_save"]').click();
});

// ===============================
// Verification Commands
// ===============================

/**
 * Verifies success or error messages in admin
 */
Cypress.Commands.add('verifyMessage', (type, message) => {
  if (type === 'success') {
    cy.get('.messagelist', { timeout: DEFAULT_TIMEOUT }).should('contain', message);
  } else if (type === 'error') {
    cy.get('.errornote, .errorlist', { timeout: DEFAULT_TIMEOUT }).should('contain', message);
  }
});

/**
 * Verifies a record exists (or not) in model list view
 */
Cypress.Commands.add('verifyListView', (model, itemText, shouldExist = true) => {
  cy.visit(`/communityEmpowerment/${model}/`);
  cy.get('#result_list').should(shouldExist ? 'contain' : 'not.contain', itemText);
});

/**
 * Checks if a specific selector exists or not
 */
Cypress.Commands.add('checkPermission', (selector, shouldExist, message) => {
  cy.get('body').then($body => {
    const exists = $body.find(selector).length > 0;
    expect(exists, message || `Expected ${selector} to ${shouldExist ? 'exist' : 'not exist'}`).to.equal(shouldExist);
  });
});

/**
 * Verifies UI elements based on user role
 */
Cypress.Commands.add('verifyUserInterface', (userType) => {
  getUserConfig(userType).then(config => {
    const ui = config.expectedUi;
    cy.get('body').then($body => {
      // Add buttons
      if (typeof ui.hasAddButtons === 'object') {
        Object.entries(ui.hasAddButtons).forEach(([model, hasBtn]) => {
          const addBtn = $body.find(`a.addlink:contains("Add ${model}")`);
          expect(addBtn.length > 0).to.equal(hasBtn);
        });
      } else {
        cy.get('a.addlink').should(ui.hasAddButtons ? 'exist' : 'not.exist');
      }

      // Other UI elements
      cy.get('input[name="_save"]').should(ui.hasSaveButtons ? 'exist' : 'not.exist');
      cy.get('a:contains("Delete")').should(ui.hasDeleteButtons ? 'exist' : 'not.exist');
      cy.get('#changelist-filter').should(ui.hasListFilters ? 'exist' : 'not.exist');
      cy.get('select[name="action"]').should(ui.hasBulkActions ? 'exist' : 'not.exist');
    });
  });
});

/**
 * Verifies permissions for add/change/delete/inline editing
 */
Cypress.Commands.add('verifyPermissions', (userType, modelType) => {
  getUserConfig(userType).then(config => {
    const { permissions, expectedUi } = config;

    // Add
    if (Array.isArray(permissions.canAdd)) {
      const canAdd = permissions.canAdd.includes(modelType) || permissions.canAdd.includes('*');
      cy.get('a.addlink').should(canAdd ? 'exist' : 'not.exist');
    }

    // Change
    if (Array.isArray(permissions.canChange)) {
      const canChange = permissions.canChange.includes(modelType) || permissions.canChange.includes('*');
      cy.get('input[name="_save"]').should(canChange ? 'exist' : 'not.exist');
    }

    // Delete
    if (Array.isArray(permissions.canDelete)) {
      const canDelete = permissions.canDelete.includes(modelType) || permissions.canDelete.includes('*');
      cy.get('a:contains("Delete")').should(canDelete ? 'exist' : 'not.exist');
    }

    // Inline editing
    if (typeof expectedUi.canEditInlineFields === 'object') {
      Object.entries(expectedUi.canEditInlineFields)
        .filter(([key]) => key.startsWith(modelType))
        .forEach(([key, editable]) => {
          const field = key.split('.')[1];
          cy.get(`input[name*="${field}"]`).should(editable ? 'not.be.disabled' : 'be.disabled');
        });
    }
  });
});

/**
 * Waits for Django Admin page to fully load
 */
Cypress.Commands.add('waitForDjangoAdmin', () => {
  cy.get('#content', { timeout: DEFAULT_TIMEOUT }).should('exist');
  cy.get('body').should('not.have.class', 'loading');
});

// ===============================
// Utilities
// ===============================

/**
 * Selects item from Django's many-to-many widget
 */
Cypress.Commands.add('selectAdminManyToMany', (field, itemText) => {
  cy.get(`.field-${field} .selector-available select option`).contains(itemText).then($option => {
    if ($option.length) {
      $option.prop('selected', true);
      cy.get(`.field-${field} .selector-add`).click();
    }
  });
});

/**
 * Setup test user based on fixture or fallback
 */
Cypress.Commands.add('setupTestUser', (role) => {
  return cy.fixture('admin-test-users.json').then(
    data => ({ userConfig: data.users[role] || { username: role, password: `${role}password` } }),
    () => ({ userConfig: { username: role, password: `${role}password` } })
  );
});
