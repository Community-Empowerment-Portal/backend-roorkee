describe('Django Admin RBAC with Groups', () => {
  it('Admin creates a group with view permissions', () => {
    cy.admin_login('karthik', 'Test@123');
    cy.visit('/auth/group/add/');
    cy.get('input[name="name"]').type('Viewer');
    cy.get('input[placeholder="Filter"]').first().type('view');
    cy.get('.selector-chooseall').click();
    cy.save();
    cy.url().should('include', '/auth/group');
    cy.contains('Viewer').should('be.visible');
  });

  it('Admin creates testuser without staff permissions', () => {
    cy.admin_login('karthik', 'Test@123');
    cy.visit('/communityEmpowerment/customuser/add/');
    cy.get('input[name="username"]').type('testuser');
    cy.get('input[name="email"]').type('testuser@gmail.com');
    cy.get('input[name="password1"]').type('Epson&l3115');
    cy.get('input[name="password2"]').type('Epson&l3115');
    cy.save();
    cy.admin_logout();
  });

  it('Ensure non-staff user is denied admin access', () => {
    cy.admin_login('testuser', 'Epson&l3115');
    cy.get('.errornote').should('be.visible');
  });

  it('Admin deletes and recreates testuser with Viewer group', () => {
    cy.admin_login('karthik', 'Test@123');
    cy.visit('/communityEmpowerment/customuser/');
    cy.contains('testuser').click();
    cy.get('.deletelink').click();
    cy.get('input[value="Yes, I’m sure"]').click();

    cy.visit('/communityEmpowerment/customuser/add/');
    cy.get('input[name="username"]').type('testuser');
    cy.get('input[name="email"]').type('testuser@gmail.com');
    cy.get('input[name="password1"]').type('Epson&l3115');
    cy.get('input[name="password2"]').type('Epson&l3115');
    cy.get('input[name="is_staff"]').check();
    cy.get('input[name="_continue"]').click();
    cy.get('#id_groups_add_all_link').click();
    cy.save();
    cy.admin_logout();
  });

  it('Ensure Viewer user has restricted access', () => {
    cy.admin_login('testuser', 'Epson&l3115');
    cy.visit('/communityEmpowerment/scheme/');
    cy.get('.results').should('be.visible');
    cy.visit('/communityEmpowerment/scheme/add', { failOnStatusCode: false });
    cy.contains('403 Forbidden').should('be.visible');
  });

  it('Upgrade testuser to full access', () => {
    cy.admin_login('karthik', 'Test@123');
    cy.visit('/communityEmpowerment/customuser/');
    cy.contains('testuser').click();
    cy.get('#id_user_permissions_add_all_link').click();
    cy.save();
    cy.admin_logout();
  });

  it('Ensure upgraded user can delete groups', () => {
    cy.admin_login('testuser', 'Epson&l3115');
    cy.visit('/auth/group');
    cy.contains('Viewer').click();
    cy.get('.deletelink').click();
    cy.get('input[value="Yes, I’m sure"]').click();
    cy.contains('The group “Viewer” was deleted successfully.').should('be.visible');
  });

  it('Admin deletes testuser', () => {
    cy.admin_login('karthik', 'Test@123');
    cy.visit('/communityEmpowerment/customuser/');
    cy.contains('testuser').click();
    cy.get('.deletelink').click();
    cy.get('input[value="Yes, I’m sure"]').click();
  });
});
