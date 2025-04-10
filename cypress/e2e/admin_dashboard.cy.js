// Admin Dashboard Tests
// Tests admin navigation, search, quick actions, and UI elements

describe('Admin Dashboard Functionality', () => {
  const admin = {
    username: 'admin',
    password: 'adminpassword'
  };

  beforeEach(() => {
    // Clear cookies and login as admin before each test
    cy.clearCookies();
    cy.admin_login(admin.username, admin.password);
  });

  afterEach(() => {
    // Logout after each test
    cy.admin_logout();
  });

  context('Admin Site Header and Branding', () => {
    it('should display the correct site header and title', () => {
      cy.visit('/');
      
      // Check custom site header
      cy.get('#site-name a')
        .should('contain', 'Community Empowerment Portal Admin Panel');
      
      // Check page title
      cy.title().should('include', 'Admin Portal');
      
      // Check welcome message
      cy.get('h1').should('contain', 'Welcome to your Admin Panel');
    });

    it('should display the correct branding in the login page', () => {
      // Logout first
      cy.admin_logout();
      
      // Visit login page
      cy.visit('/');
      
      // Check branding on login page
      cy.get('#site-name')
        .should('contain', 'Community Empowerment Portal Admin Panel');
      
      // Login again for subsequent tests
      cy.admin_login(admin.username, admin.password);
    });
  });

  context('Custom App Groups Navigation', () => {
    it('should display all custom app groupings', () => {
      cy.visit('/');
      
      // Verify all custom app groups are present
      const appGroups = [
        'Access Management',
        'Layouts',
        'All Schemes',
        'Feedback & Reports',
        'User Events',
        'Assets',
        'Periodic Tasks',
        'Token Blacklist'
      ];
      
      appGroups.forEach(groupName => {
        cy.get('#content-main').should('contain', groupName);
      });
    });

    it('should navigate to Access Management sections', () => {
      cy.visit('/');
      
      // Click on Users link within Access Management
      cy.contains('Access Management')
        .parents('.app-communityEmpowerment')
        .contains('Users')
        .click();
      
      // Verify we're on the users page
      cy.url().should('include', '/admin/communityEmpowerment/customuser/');
      cy.get('h1').should('contain', 'Select user to change');
      
      // Go back to home
      cy.visit('/');
      
      // Click on Groups link
      cy.contains('Access Management')
        .parents('.app-communityEmpowerment')
        .contains('Groups')
        .click();
      
      // Verify we're on the groups page
      cy.url().should('include', '/admin/auth/group/');
      cy.get('h1').should('contain', 'Select group to change');
    });

    it('should navigate to Layouts sections', () => {
      cy.visit('/');
      
      // Click on Profile Fields link within Layouts
      cy.contains('Layouts')
        .parents('.app-communityEmpowerment')
        .contains('Profile Fields')
        .click();
      
      // Verify we're on the profile fields page
      cy.url().should('include', '/admin/communityEmpowerment/profilefield/');
      cy.get('h1').should('contain', 'Select profile field to change');
      
      // Go back to home
      cy.visit('/');
      
      // Click on FAQs link
      cy.contains('Layouts')
        .parents('.app-communityEmpowerment')
        .contains('FAQs')
        .click();
      
      // Verify we're on the FAQs page
      cy.url().should('include', '/admin/communityEmpowerment/faq/');
      cy.get('h1').should('contain', 'Select faq to change');
    });

    it('should navigate to All Schemes sections', () => {
      cy.visit('/');
      
      // Click on Schemes link within All Schemes
      cy.contains('All Schemes')
        .parents('.app-communityEmpowerment')
        .contains('Schemes')
        .click();
      
      // Verify we're on the schemes page
      cy.url().should('include', '/admin/communityEmpowerment/scheme/');
      cy.get('h1').should('contain', 'Select scheme to change');
      
      // Go back to home
      cy.visit('/');
      
      // Click on States link
      cy.contains('All Schemes')
        .parents('.app-communityEmpowerment')
        .contains('States')
        .click();
      
      // Verify we're on the states page
      cy.url().should('include', '/admin/communityEmpowerment/state/');
      cy.get('h1').should('contain', 'Select state to change');
    });
  });

  context('Model Search Functionality', () => {
    it('should search for users', () => {
      // Go to users page
      cy.visit('/admin/communityEmpowerment/customuser/');
      
      // Search for admin user
      cy.get('#searchbar').type(admin.username);
      cy.get('#changelist-search input[type="submit"]').click();
      
      // Verify search results
      cy.get('#result_list').should('contain', admin.username);
      
      // Clear search
      cy.get('#changelist-search a').contains('Clear').click();
    });

    it('should search for schemes', () => {
      // Create a test scheme with a unique name if not exists
      const testSchemeName = 'Test Scheme ' + Date.now();
      cy.visit('/admin/communityEmpowerment/scheme/add/');
      
      // Check if we can create a scheme (might need a department first)
      cy.get('body').then($body => {
        if ($body.find('select[name="department"]').length > 0) {
          // Create the scheme
          cy.fillAdminForm({ 'title': testSchemeName }, 'input');
          cy.get('select[name="department"]').select(1); // Select the first department
          cy.fillAdminForm({ 'funding_pattern': 'Central' }, 'select');
          cy.save();
          
          // Go to schemes list
          cy.visit('/admin/communityEmpowerment/scheme/');
          
          // Search for the test scheme
          cy.get('#searchbar').type(testSchemeName);
          cy.get('#changelist-search input[type="submit"]').click();
          
          // Verify search results
          cy.get('#result_list').should('contain', testSchemeName);
        } else {
          // Skip test if we can't create a scheme
          cy.log('Cannot create test scheme - department field not found');
        }
      });
    });
  });

  context('Quick Actions', () => {
    it('should use recent actions sidebar', () => {
      cy.visit('/');
      
      // Check if recent actions section exists
      cy.get('#recent-actions-module').should('exist');
      cy.get('#recent-actions-module h2').should('contain', 'Recent actions');
    });

    it('should use breadcrumbs for navigation', () => {
      // Go to a detail page (e.g., states)
      cy.visit('/admin/communityEmpowerment/state/');
      
      // Verify breadcrumbs
      cy.get('.breadcrumbs').should('contain', 'Home');
      cy.get('.breadcrumbs').should('contain', 'CommunityEmpowerment');
      cy.get('.breadcrumbs').should('contain', 'States');
      
      // Click on a state (if any exists)
      cy.get('#result_list tbody tr:first-child th a').then($link => {
        if ($link.length > 0) {
          cy.wrap($link).click();
          
          // Verify breadcrumbs on detail page
          cy.get('.breadcrumbs').should('contain', 'Home');
          cy.get('.breadcrumbs').should('contain', 'CommunityEmpowerment');
          cy.get('.breadcrumbs').should('contain', 'States');
          cy.get('.breadcrumbs').should('contain', 'State');
          
          // Navigate back using breadcrumb
          cy.get('.breadcrumbs a').contains('States').click();
          cy.url().should('include', '/admin/communityEmpowerment/state/');
        }
      });
    });
  });

  context('Dashboard Stats and Elements', () => {
    it('should display app list in the correct order', () => {
      cy.visit('/');
      
      // Verify the first app group is Access Management
      cy.get('#content-main .app-communityEmpowerment').eq(0)
        .should('contain', 'Access Management');
      
      // Verify ordering of models within Access Management
      cy.get('#content-main .app-communityEmpowerment').eq(0).within(() => {
        cy.get('.model').eq(0).should('contain', 'Users');
        cy.get('.model').eq(1).should('contain', 'Groups');
        cy.get('.model').eq(2).should('contain', 'Permissions');
      });
    });

    it('should have working links to documentation', () => {
      cy.visit('/');
      
      // Check if documentation link exists and works
      cy.get('#content-related').contains('Documentation').should('have.attr', 'href');
    });
  });

  context('Admin View Customizations', () => {
    it('should have custom list display for schemes', () => {
      cy.visit('/admin/communityEmpowerment/scheme/');
      
      // Verify custom columns in scheme list view
      const expectedColumns = ['Title', 'Department', 'Is active', 'Introduced on', 'Valid upto', 'Funding pattern'];
      
      // Check table headers
      cy.get('#result_list thead th').each(($th, index) => {
        if (index < expectedColumns.length) {
          cy.wrap($th).should('contain', expectedColumns[index]);
        }
      });
    });

    it('should have custom list filters for schemes', () => {
      cy.visit('/admin/communityEmpowerment/scheme/');
      
      // Verify filter options are present
      cy.get('#changelist-filter').should('exist');
      cy.get('#changelist-filter').should('contain', 'By department');
      cy.get('#changelist-filter').should('contain', 'By introduced on');
      cy.get('#changelist-filter').should('contain', 'By valid upto');
    });
  });
});

