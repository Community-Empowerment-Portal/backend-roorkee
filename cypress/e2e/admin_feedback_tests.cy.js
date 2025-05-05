import {
  generateRandomString,
  createSchemeFeedbackTestData,
  navigateToAdminSection,
  openAddNewForm,
  openEditForm,
  fillSchemeFeedbackForm,
  filterByDate
} from '../support/admin-test-helpers';

describe('Admin Portal - Feedback and Reports CRUD Tests', () => {
  const users = {
    admin: {
      username: 'admin',
      password: 'adminpassword',
      role: 'Administrator'
    },
    editor: {
      username: 'editor', 
      password: 'editorpassword',
      role: 'Editor'
    },
    viewer: {
      username: 'viewer',
      password: 'viewerpassword',
      role: 'Viewer'
    }
  };
  
  const testData = users.admin;
  
  beforeEach(() => {
    // Login before each test
    cy.admin_login(testData.username, testData.password);
    cy.waitForDjangoAdmin();
  });
  
  afterEach(() => {
    // Logout after each test
    cy.admin_logout();
  });
  
  describe('Common Admin Portal Tests', () => {
    it('should successfully navigate to the Feedback & Reports section', () => {
      cy.contains('Feedback & Reports').should('be.visible').click();
      cy.get('.model-group').should('be.visible');
      cy.contains('Scheme Feedbacks').should('be.visible');
      cy.contains('Scheme Reports').should('be.visible');
      cy.contains('Website Feedbacks').should('be.visible');
    });
    
    it('should verify proper error messages for invalid inputs', () => {
      // Navigate to Scheme Feedback creation
      navigateToAdminSection('Scheme Feedbacks');
      openAddNewForm();
      
      // Try to submit empty form
      cy.get('input[name="_save"]').click();
      
      // Verify error messages
      cy.verifyMessage('error', 'Please correct the error');
      cy.get('.errorlist').should('be.visible');
    });
  });
  
  describe('Scheme Feedback CRUD Tests', () => {
    it('should create a new scheme feedback entry', () => {
      // Navigate to Scheme Feedback section
      navigateToAdminSection('Scheme Feedbacks');
      openAddNewForm();
      
      // Generate test data
      const feedbackData = createSchemeFeedbackTestData();
      
      // Fill form with test data
      fillSchemeFeedbackForm({
        user: 'admin', 
        scheme: 0,
        feedback: feedbackData.feedback,
        rating: feedbackData.rating
      });
      
      // Submit form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'was added successfully');
    });
    
    it('should read/view scheme feedback entries in list view', () => {
      // Navigate to Scheme Feedback list
      navigateToAdminSection('Scheme Feedbacks');
      
      // Verify list view headers
      cy.get('#result_list thead').should('contain', 'Scheme feedback');
      
      // Verify list contains at least one entry
      cy.get('#result_list tbody tr').should('have.length.at.least', 1);
    });
    
    it('should update an existing scheme feedback entry', () => {
      // Navigate to Scheme Feedback list
      navigateToAdminSection('Scheme Feedbacks');
      
      // Open first entry for editing
      openEditForm(0);
      
      // Update the feedback text
      const updatedFeedback = `Updated feedback ${generateRandomString(5)}`;
      cy.get('#id_feedback').clear().type(updatedFeedback);
      
      // Submit the form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'was changed successfully');
    });
  });

  describe('Scheme Report CRUD Tests', () => {
    it('should create a new scheme report entry', () => {
      // Navigate to Scheme Reports section
      navigateToAdminSection('Scheme Reports');
      openAddNewForm();
      

      cy.get('#id_scheme_id').type('10691');

      // Fill form with test data
      // Select user
      cy.get('#id_user').select('admin');

      cy.get('#id_report_category').select('incorrect_info');
      cy.get('#id_description').type('testing scheme report');
      // Submit form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'was added successfully');
    });
    
    it('should read/view scheme report entries in list view', () => {
      // Navigate to Scheme Report list
      navigateToAdminSection('Scheme Reports');
      
      // Verify list view headers
      cy.get('#result_list thead').should('contain', 'ID');
      cy.get('#result_list thead').should('contain', 'User');
      cy.get('#result_list thead').should('contain', 'Scheme id');
      cy.get('#result_list thead').should('contain', 'Created at');
      
      // Verify list contains at least one entry
      cy.get('#result_list tbody tr').should('have.length.at.least', 1);
    });
    
    it('should verify linked_user functionality', () => {
      // Navigate to Scheme Report list
      navigateToAdminSection('Scheme Reports');
      
      // Find first user link and verify it's clickable
      cy.get('#result_list tbody tr').first().find('td a').first()
        .should('exist')
        .and('have.attr', 'href')
        .and('include', '/admin/communityEmpowerment/customuser/');
    });
    
    it('should update an existing scheme report entry', () => {
      // Navigate to Scheme Report list
      navigateToAdminSection('Scheme Reports');
      
      // Open first entry for editing
      openEditForm(0);
      
      // Change scheme selection if possible
      cy.get('#id_scheme_id').type('10690');
      
      // Submit the form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'was changed successfully');
    });
    
    it('should filter scheme reports by created_at date', () => {
      // Navigate to Scheme Report list
      navigateToAdminSection('Scheme Reports');
      
      cy.get('.viewlink').click()
      // Apply date filter
      filterByDate();
      
      // Verify filter is applied
      cy.get('#changelist-filter').should('contain', 'By created at');
      cy.get('#changelist-filter li.selected').should('be.visible');
    });
  });

  describe('Website Feedback CRUD Tests', () => {
    it('should create a new website feedback entry', () => {
      // Navigate to Website Feedback section
      navigateToAdminSection('Website Feedbacks');
      openAddNewForm();
      
      cy.get('#id_user').select('admin')
      cy.get('#id_category').select('Bug Report')
      cy.get('#id_description').type('testing website feeback table')      

      // Submit form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'was added successfully');
    });
    
    it('should read/view website feedback entries in list view', () => {
      // Navigate to Website Feedback list
      navigateToAdminSection('Website Feedbacks');
      
      // Verify list view headers
      cy.get('#result_list thead').should('contain', 'Website feedback');
      
      // Verify list contains at least one entry
      cy.get('#result_list tbody tr').should('have.length.at.least', 1);
    });
    
    it('should update an existing website feedback entry', () => {
      // Navigate to Website Feedback list
      navigateToAdminSection('Website Feedbacks');
      
      // Open first entry for editing
      openEditForm(0);
      
      // Update the description

      const updatedDescription = `Updated website feedback ${generateRandomString(5)}`;
      cy.get('#id_description').clear().type(updatedDescription);
      
      // Submit the form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'was changed successfully');
    });
    
  });


});
