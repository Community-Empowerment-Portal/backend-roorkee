describe('Admin Layout Customization and Profile Field Management', () => {
  const timestamp = Date.now();
  
  const admin = {
    username: 'admin',
    password: 'adminpassword'
  };
  
  const testLayoutItem = {
    column_name: `Schemes`,
    is_active: true,
    order: 1
  };

  const testProfileField = {
    name: `Test Profile Field ${timestamp}`,
    field_type: 'char',
    is_required: true,
    is_active: true,
    placeholder: 'Enter text',
    position: 1,
    is_fixed: false
  };

  beforeEach(() => {
    cy.clearCookies();
    cy.admin_login(admin.username, admin.password);
  });

  after(() => {
    cy.visit('/communityEmpowerment/layoutitem/');
    cy.contains(testLayoutItem.column_name).should('exist')
      .then(() => {
        cy.contains('.field-column_name', testLayoutItem.column_name).parent().find('a').click();
        cy.fillAdminForm({ 'is_active': false }, 'checkbox'); // Set to inactive instead of deletion
        cy.fillAdminForm({ 'order': 1 }, 'input'); // Reset order
        cy.save();
      });

    cy.visit('/communityEmpowerment/profilefield/');
    cy.contains(testProfileField.name).should('exist')
      .then(() => {
        cy.contains('.field-name', testProfileField.name).parent().find('a').click();
        cy.fillAdminForm({ 'is_active': false }, 'checkbox'); // Set to inactive
        cy.save();
      });

    cy.admin_logout();
  });

  context('Layout Item Operations', () => {

    it('should edit a layout item', () => {
      cy.visit('/communityEmpowerment/layoutitem/');
      cy.contains('.field-column_name', testLayoutItem.column_name).parent().find('a').click();
      cy.fillAdminForm({ 'is_active': false }, 'checkbox'); 
      cy.fillAdminForm({ 'order': 5 }, 'input'); // Change order
      cy.save();
      cy.verifyMessage('success', 'changed successfully');
      cy.wait(1000)
      cy.contains(testLayoutItem.column_name).should('exist');
    });
  });

  context('Profile Field Operations', () => {
    it('should create a new profile field', () => {
      cy.visit('/communityEmpowerment/profilefield/add/');
      cy.fillAdminForm({ 'name': testProfileField.name }, 'input');
      cy.fillAdminForm({ 'field_type': testProfileField.field_type }, 'select');
      cy.fillAdminForm({ 'is_required': testProfileField.is_required }, 'checkbox');
      cy.fillAdminForm({ 'is_active': testProfileField.is_active }, 'checkbox');
      cy.fillAdminForm({ 'placeholder': testProfileField.placeholder }, 'input');
      cy.fillAdminForm({ 'position': testProfileField.position }, 'input');
      cy.fillAdminForm({ 'is_fixed': testProfileField.is_fixed }, 'checkbox');
      cy.save();
      cy.verifyMessage('success', 'added successfully');
      cy.contains(testProfileField.name).should('exist');
    });

    it('should edit a profile field', () => {
      cy.visit('/communityEmpowerment/profilefield/');
      cy.contains('.field-name', testProfileField.name).parent().find('a').click();
      cy.fillAdminForm({ 'is_active': false }, 'checkbox'); 
      cy.save();
      cy.verifyMessage('success', 'changed successfully');
      cy.visit('/communityEmpowerment/profilefield/');
      cy.contains(testProfileField.name).should('exist');
    });
  });
});
