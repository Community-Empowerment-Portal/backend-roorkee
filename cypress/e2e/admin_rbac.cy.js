const users = {
  admin: { username: 'admin', password: 'adminpassword' },
  editor: { username: 'editor', password: 'editorpassword' },
  viewer: { username: 'viewer', password: 'viewerpassword' }
};

describe('Django Admin RBAC with Groups', () => {
  beforeEach(() => {
    // Log in as admin before each test
    cy.clearCookies();
    cy.clearLocalStorage();
    cy.admin_login(users.admin.username, users.admin.password);
  });

  it('Deletes existing Viewer and Editor groups if present', () => {
    cy.visit('/auth/group/');
    ['Viewer', 'Editor'].forEach((group) => {
      cy.get('body').then(($body) => {
        if ($body.text().includes(group)) {
          cy.contains(group).click();
          cy.get('.deletelink').click();
          cy.get('input[value="Yes, I’m sure"]').click();
          cy.visit('/auth/group/');
        }
      });
    });
  });

  it('Creates Viewer group with view permissions', () => {
    // Create the Viewer group if it doesn't exist
    cy.visit('/auth/group/add/');
    cy.get('input[name="name"]').type('Viewer');
    cy.get('input[placeholder="Filter"]').first().type('view');
    cy.get('.selector-chooseall').click();
    cy.save();
    cy.contains('Viewer').should('be.visible');
  });

  it('Creates Editor group with change permissions', () => {
    // Create the Editor group if it doesn't exist
    cy.visit('/auth/group/add/');
    cy.get('input[name="name"]').type('Editor');
    cy.get('input[placeholder="Filter"]').first().type('change');
    cy.get('.selector-chooseall').click();
    cy.save();
    cy.contains('Editor').should('be.visible');
  });

  it('Creates Viewer user', () => {
    // Create the Viewer user if not present
    cy.visit('/communityEmpowerment/customuser/add/');
    cy.get('input[name="username"]').type(users.viewer.username);
    cy.get('input[name="email"]').type(`${users.viewer.username}@gmail.com`);
    cy.get('input[name="password1"]').type(users.viewer.password);
    cy.get('input[name="password2"]').type(users.viewer.password);
    cy.get('input[name="is_staff"]').check();
    cy.save();
  });

  it('Creates Editor user', () => {
    // Create the Editor user if not present
    cy.visit('/communityEmpowerment/customuser/add/');
    cy.get('input[name="username"]').type(users.editor.username);
    cy.get('input[name="email"]').type(`${users.editor.username}@gmail.com`);
    cy.get('input[name="password1"]').type(users.editor.password);
    cy.get('input[name="password2"]').type(users.editor.password);
    cy.get('input[name="is_staff"]').check();
    cy.save();
  });

  it('Assigns Viewer group to viewer user', () => {
    // Assign the Viewer group to the user
    cy.visit('/communityEmpowerment/customuser/');
    cy.contains(users.viewer.username).click();
    cy.get('#id_groups_from').select('Viewer');
    cy.get('#id_groups_add_link').click();
    cy.save();
  });

  it('Assigns Editor group to editor user', () => {
    // Assign the Editor group to the user
    cy.visit('/communityEmpowerment/customuser/');
    cy.contains(users.editor.username).click();
    cy.get('#id_groups_from').select('Editor');
    cy.get('#id_groups_add_link').click();
    cy.save();
    cy.admin_logout();
  });

  it('Viewer user can view but not add schemes', () => {
    // Log in as the Viewer user
    cy.admin_logout()
    cy.admin_login(users.viewer.username, users.viewer.password);
    cy.visit('/communityEmpowerment/scheme/');
    cy.get('.results').should('be.visible');

    cy.visit('/communityEmpowerment/scheme/add', { failOnStatusCode: false });
    cy.contains('403 Forbidden').should('be.visible');
    cy.go('back');
    cy.admin_logout();
  });

  it('Editor user can change but not add or delete schemes', () => {
    // Log in as the Editor user
    cy.admin_logout()
    cy.admin_login(users.editor.username, users.editor.password);
    cy.visit('/communityEmpowerment/scheme/');
    cy.get('.results').should('be.visible');

    cy.visit('/communityEmpowerment/scheme/add', { failOnStatusCode: false });
    cy.contains('403 Forbidden').should('be.visible');
    cy.go('back');
    cy.visit('/communityEmpowerment/scheme/1/change/', { failOnStatusCode: false });
    cy.get('form').should('be.visible');

    cy.visit('/communityEmpowerment/scheme/1/delete/', { failOnStatusCode: false });
    cy.contains('403 Forbidden').should('be.visible');
    cy.go('back');
    cy.admin_logout();
  });
});
