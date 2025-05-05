function loadTestUsersConfig() {
  return cy.fixture('admin-test-users.json').then(config => {
    return config;
  });
}

function setupTestUser (role) {
  return loadTestUsersConfig().then(config => {
    const userConfig = config.users[role];
    const permissionsConfig = config.permissions[role];

    cy.request({
      method: 'POST',
      url: '/api/auth/check-user-exists/',
      body: { username: userConfig.username },
      failOnStatusCode: false
    }).then(response => {
      if (response.status === 404 || response.body.exists === false) {
        cy.log(`Test user ${userConfig.username} does not exist, creating...`);

        cy.admin_login(config.users.admin.username, config.users.admin.password);
        cy.visit('/admin/communityEmpowerment/customuser/add/');
        cy.fillAdminForm({ 'username': userConfig.username }, 'input');
        cy.fillAdminForm({ 'email': userConfig.email }, 'input');
        cy.fillAdminForm({ 'first_name': userConfig.firstName }, 'input');
        cy.fillAdminForm({ 'last_name': userConfig.lastName }, 'input');
        cy.fillAdminForm({ 'password1': userConfig.password }, 'input');
        cy.fillAdminForm({ 'password2': userConfig.password }, 'input');
        cy.fillAdminForm({ 'is_staff': permissionsConfig.isStaff }, 'checkbox');
        cy.fillAdminForm({ 'is_superuser': permissionsConfig.isSuperuser }, 'checkbox');
        cy.fillAdminForm({ 'is_active': permissionsConfig.isActive }, 'checkbox');
        cy.save();

        if (permissionsConfig.groups.length > 0 || permissionsConfig.userPermissions.length > 0) {
          cy.contains('tr', userConfig.username).find('th a').click();

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

          cy.save();
        }

        cy.admin_logout();
      } else {
        cy.log(`Test user ${userConfig.username} already exists`);
      }
    });

    return { userConfig, permissionsConfig };
  });
}

function verifyUserPermissions(role, modelName) {
  return loadTestUsersConfig().then(config => {
    const expectedUi = config.expectedUi[role];

    if (typeof expectedUi.hasAddButtons === 'object') {
      const shouldHaveAddButton = expectedUi.hasAddButtons[modelName] || false;
      cy.checkPermission('a.addlink', shouldHaveAddButton,
        `${role} ${shouldHaveAddButton ? 'should' : 'should not'} have "Add" button for ${modelName}`);
    } else {
      cy.checkPermission('a.addlink', expectedUi.hasAddButtons,
        `${role} ${expectedUi.hasAddButtons ? 'should' : 'should not'} have "Add" button for ${modelName}`);
    }

    cy.get('#result_list tbody tr:first-child th a').then($link => {
      if ($link.length) {
        cy.wrap($link).click();

        cy.checkPermission('input[name="_save"]', expectedUi.hasSaveButtons, 
          `${role} ${expectedUi.hasSaveButtons ? 'should' : 'should not'} be able to save ${modelName}`);
        
        cy.checkPermission('a:contains("Delete")', expectedUi.hasDeleteButtons, 
          `${role} ${expectedUi.hasDeleteButtons ? 'should' : 'should not'} be able to delete ${modelName}`);
        
        cy.visit(`/admin/communityEmpowerment/${modelName}/`);
      }
    });

    cy.checkPermission('select[name="action"]', expectedUi.hasBulkActions,
      `${role} ${expectedUi.hasBulkActions ? 'should' : 'should not'} have bulk actions for ${modelName}`);

    if (expectedUi.canEditInlineFields) {
      cy.get('#result_list tbody tr:first-child').then($row => {
        if ($row.length) {
          if (typeof expectedUi.canEditInlineFields === 'object') {
            const fieldKey = `${modelName}.is_active`;
            const shouldBeEditable = expectedUi.canEditInlineFields[fieldKey] || false;

            cy.get('input[name*="is_active"]').then($input => {
              if ($input.length) {
                const isDisabled = $input.prop('disabled');
                cy.log(`${role} ${!isDisabled === shouldBeEditable ? 'correctly' : 'incorrectly'} ${shouldBeEditable ? 'can' : 'cannot'} edit ${fieldKey}`);
              }
            });
          } else {
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

function checkModelPermissions(modelName, roles = ['admin', 'editor', 'viewer']) {
  roles.forEach(role => {
    setupTestUser (role).then(({ userConfig }) => {
      cy.admin_login(userConfig.username, userConfig.password);
      cy.visit(`/admin/communityEmpowerment/${modelName}/`);
      verifyUserPermissions(role, modelName);
      cy.admin_logout();
    });
  });
}

function createTestRecord(modelName, data = {}) {
  return loadTestUsersConfig().then(config => {
    cy.admin_login(config.users.admin.username, config.users.admin.password);
    const defaultKey = Object.keys(config.testDefaults).find(key => key.toLowerCase().includes(modelName.toLowerCase()));
    const defaultTitle = defaultKey ? config.testDefaults[defaultKey] : `Test ${modelName}`;
    const timestamp = Date.now();
    const title = data.title || `${defaultTitle} ${timestamp}`;

    cy.visit(`/admin/communityEmpowerment/${modelName}/add/`);

    switch (modelName) {
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

        cy.get('body').then($body => {
          if ($body.find('select[name="layout_type"]').length) {
            cy.fillAdminForm({ 'layout_type': data.layout_type || 'text' }, 'select');
          }
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
        if (data.title) cy.fillAdminForm({ 'title': title }, 'input');
        if (data.name) cy.fillAdminForm({ 'name': title }, 'input');
        if (data.description) cy.fillAdminForm({ 'description': data.description }, 'textarea');
        if ('is_active' in data) cy.fillAdminForm({ 'is_active': data.is_active }, 'checkbox');
    }

    cy.save();
    cy.admin_logout();

    return title;
  });
}

function deleteTestRecord(modelName, identifier) {
  return loadTestUsersConfig().then(config => {
    cy.admin_login(config.users.admin.username, config.users.admin.password);
    cy.visit(`/admin/communityEmpowerment/${modelName}/`);

    cy.get('body').then($body => {
      if ($body.text().includes(identifier)) {
        cy.contains('tr', identifier).find('th a').click();
        cy.contains('Delete').click();
        cy.contains("Yes, I'm sure").click();
      }
    });

    cy.admin_logout();
  });
}

export {
  loadTestUsersConfig,
  setupTestUser ,
  verifyUserPermissions,
  checkModelPermissions,
  createTestRecord,
  deleteTestRecord
};

export const generateRandomString = (length = 8) => {
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  return result;
};

export const getCurrentDate = () => {
  const date = new Date();
  return date.toISOString().split('T')[0];
};

export const createSchemeFeedbackTestData = () => {
  return {
    feedback: `Test feedback ${generateRandomString(5)}`,
    rating: Math.floor(Math.random() * 5) + 1,
  };
};

export const createWebsiteFeedbackTestData = () => {
  return {
    description: `Website feedback description ${generateRandomString(8)}`,
  };
};

export const navigateToAdminSection = (section) => {
  cy.contains('Feedback & Reports').click();
  cy.contains(section).click();
};

export const selectUser  = (username = 'admin') => {
  cy.get('#id_user').select(username);
};

export const selectScheme = (schemeTitle = 0) => {
  if (typeof schemeTitle === 'number') {
    cy.get('#id_scheme').find('option').then($options => {
      const optionIndex = schemeTitle + 1;
      if ($options.length > optionIndex) {
        cy.get('#id_scheme').select($options[optionIndex].value);
      } else {
        cy.log('Not enough scheme options');
      }
    });
  } else {
    cy.get('#id_scheme').select(schemeTitle);
  }
};

export const openAddNewForm = () => {
  cy.get('.addlink').click();
};

export const openEditForm = (index = 0) => {
  cy.get('#result_list tbody tr').eq(index).find('a').first().click();
};

export const fillSchemeFeedbackForm = (data) => {
  if (data.user) {
    selectUser (data.user);
  }
  if (data.scheme !== undefined) {
    selectScheme(data.scheme);
  }
  if (data.feedback) {
    cy.get('#id_feedback').clear().type(data.feedback);
  }
  if (data.rating) {
    cy.get('#id_rating').clear().type(data.rating);
  }
};

export const fillWebsiteFeedbackForm = (data) => {
  if (data.user) {
    selectUser (data.user);
  }
  if (data.description) {
    cy.get('#id_description').clear().type(data.description);
  }
};

export const filterByDate = (dateString = getCurrentDate()) => {
  cy.get('#changelist-filter')
    .should('exist')
    .contains('Today')
    .click();
};

export const verifyListViewContains = (model, fieldValue, shouldExist = true) => {
  if (shouldExist) {
    cy.get('#result_list').should('contain', fieldValue);
  } else {
    cy.get('#result_list').should('not.contain', fieldValue);
  }
};

export const verifyPagination = () => {
  cy.get('body').then($body => {
    if ($body.find('.paginator').length > 0) {
      cy.get('.paginator').should('be.visible');

      if ($body.find('.paginator a.next').length > 0) {
        cy.get('.paginator a.next').click();
        cy.get('#result_list').should('be.visible');
      }
    } else {
      cy.log('No pagination required - single page of results');
    }
  });
};

export const verifyAdminLink = (linkText, expectedUrl) => {
  cy.contains(linkText).should('have.attr', 'href').and('include', expectedUrl);
};
