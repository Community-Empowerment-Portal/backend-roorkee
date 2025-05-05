// cypress/support/helpers.js

/**
 * Load test user configurations from fixture or use defaults
 */
export const loadTestUsersConfig = () => {
  return cy.fixture('admin-test-users.json').then(
    (userData) => userData,
    () => ({
      users: {
        admin: { username: 'admin', password: 'adminpassword' },
        editor: { username: 'editor', password: 'editorpassword' },
        viewer: { username: 'viewer', password: 'viewerpassword' }
      }
    })
  );
};

/**
 * Set up a test user with specific role
 */
export const setupTestUser = (role) => {
  return cy.fixture('admin-test-users.json').then(
    (userData) => ({
      userConfig: userData.users[role] || { username: role, password: `${role}password` }
    }),
    () => ({
      userConfig: { username: role, password: `${role}password` }
    })
  );
};

/**
 * Verify user permissions
 */
export const verifyUserPermissions = (selector, shouldExist, message) => {
  cy.checkPermission(selector, shouldExist, message);
};

/**
 * Check model permissions
 */
export const checkModelPermissions = () => {
  cy.get('body').then($body => {
    return {
      canAdd: $body.find('a.addlink').length > 0,
      canChange: $body.find('input[name="_save"]').length > 0,
      canDelete: $body.find('a:contains("Delete")').length > 0
    };
  });
};

