import {
  generateRandomString,
  openAddNewForm,
  verifyListViewContains,
  verifyPagination
} from '../support/admin-test-helpers';

describe('FAQ Tests', () => {
  // Define our user roles for testing
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
  
  // Use admin for our main CRUD tests
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

  describe('FAQ Listing Tests', () => {
    it('should display FAQs in the admin list view', () => {
      // Navigate to FAQs section
      cy.visit('/communityEmpowerment/faq/');
      
      // Check if the page loaded correctly
      cy.get('h1').should('contain', 'faq');
      cy.get('#content-main').should('be.visible');
      
      // Check table headers
      cy.get('#result_list thead').should('exist');
      cy.get('#result_list thead th').should('contain', 'Question');
      cy.get('#result_list thead th').should('contain', 'Is active');
      cy.get('#result_list thead th').should('contain', 'Order');
      
      // Verify there are FAQs listed or a message saying no results
      cy.get('body').then($body => {
        if ($body.find('#result_list tbody tr').length > 0) {
          cy.get('#result_list tbody tr').should('have.length.at.least', 1);
        } else {
          cy.contains('0 faqs').should('exist');
        }
      });
    });

    it('should allow searching FAQs', () => {
      cy.visit('/communityEmpowerment/faq/');
      
      // Check if search box exists and is functional
      cy.get('#searchbar').should('exist').type('test{enter}');
      
      // Verify the search results page loaded
      cy.get('#content-main').should('be.visible');
    });

    it('should verify pagination works for FAQs', () => {
      cy.visit('/communityEmpowerment/faq/');
      
      // Check for pagination and test it if it exists
      verifyPagination();
    });
  });

  describe('FAQ CRUD Operations', () => {
    const faqQuestion = `Test FAQ Question ${generateRandomString(5)}`;
    const faqUpdatedQuestion = `Updated FAQ Question ${generateRandomString(5)}`;
    const faqAnswer = 'This is a test FAQ answer.';
    let initialFaqCount = 0;
    
    it('should create a new FAQ', () => {
      cy.visit('/communityEmpowerment/faq');
      
      // Store initial count of FAQs
      cy.get('body').then($body => {
        if ($body.find('#result_list tbody tr').length > 0) {
          cy.get('#result_list tbody tr').then($rows => {
            initialFaqCount = $rows.length;
          });
        }
      });
      
      openAddNewForm();
      
      // Fill in FAQ form fields
      cy.get('textarea[name="question"]').type(faqQuestion);
      cy.get('textarea[name="answer"]').type(faqAnswer);
      cy.get('input[name="order"]').clear().type('99'); // Put at end of the list
      
      // Save the form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'added successfully');
      
      // Verify the FAQ appears in the list
      cy.visit('/communityEmpowerment/faq/');
      verifyListViewContains('faq', faqQuestion);
      
      // Verify count increased
      cy.get('body').then($body => {
        if ($body.find('#result_list tbody tr').length > 0) {
          cy.get('#result_list tbody tr').should('have.length', initialFaqCount + 1);
        }
      });
    });

    it('should view and update an existing FAQ', () => {
      cy.visit('/communityEmpowerment/faq/');
      
      // Find our test FAQ
      cy.contains('tr', faqQuestion).find('th a').click();
      
      // Update fields
      cy.get('textarea[name="question"]').clear().type(faqUpdatedQuestion);
      cy.get('textarea[name="answer"]').clear().type('This is an updated FAQ answer.');
      cy.get('input[name="order"]').clear().type('1'); // Move to top of the list
      
      // Save the form
      cy.save();
      
      // Verify success message
      cy.verifyMessage('success', 'changed successfully');
      
      // Verify the updated FAQ appears in the list
      cy.visit('/communityEmpowerment/faq/');
      verifyListViewContains('faq', faqUpdatedQuestion);
    });

    it('should test FAQ active/inactive state', () => {
      cy.visit('/communityEmpowerment/faq/');
      
      // Find our test FAQ and check/uncheck is_active
      cy.contains('tr', faqUpdatedQuestion).find('input[name*="is_active"]').uncheck();
      
      // Save changes
      cy.get('input[name="_save"]').click();
      
      // Verify the is_active state is saved
      cy.visit('/communityEmpowerment/faq/');
      cy.contains('tr', faqUpdatedQuestion).find('input[name*="is_active"]').should('not.be.checked');
      
      // Reactivate FAQ
      cy.contains('tr', faqUpdatedQuestion).find('input[name*="is_active"]').check();
      cy.get('input[name="_save"]').click();
      
      // Verify it's active again
cy.visit('/communityEmpowerment/faq/');
      cy.contains('tr', faqUpdatedQuestion).find('input[name*="is_active"]').should('be.checked');
    });

    it('should delete an FAQ', () => {
      cy.visit('/communityEmpowerment/faq/');
      
      // Find our test FAQ
      cy.contains('tr', faqUpdatedQuestion).find('th a').click();
      
      // Delete the FAQ
      cy.contains('a', 'Delete').click();
      cy.get('input[value="Yes, I’m sure"]').click();
      
      // Verify success message
      cy.verifyMessage('success', 'deleted successfully');
      
      // Verify the FAQ was removed from the list
      cy.visit('/communityEmpowerment/faq/');
      cy.get('body').then($body => {
        const faqExists = $body.text().includes(faqUpdatedQuestion);
        expect(faqExists).to.be.false;
      });
    });
  });

  describe('FAQ Order Tests', () => {
    it('should verify FAQ order functionality works', () => {
      cy.visit('/communityEmpowerment/faq/');
      
      // Check if there are at least two FAQs to reorder
      cy.get('body').then($body => {
        if ($body.find('#result_list tbody tr').length >= 2) {
          // Get the order value of the first FAQ
          cy.get('#result_list tbody tr:nth-child(1) input[name*="order"]')
            .invoke('val')
            .then(originalOrder => {
              // Change the order to a higher number to move it down
              cy.get('#result_list tbody tr:nth-child(1) input[name*="order"]')
                .clear()
                .type('999');
              
              // Save changes
              cy.get('input[name="_save"]').click();
              
              // Verify the FAQ has moved down in the list
              cy.visit('/communityEmpowerment/faq/');
              
              // The FAQ should now be at a different position
              cy.get('#result_list tbody tr:last-child input[name*="order"]')
                .invoke('val')
                .should('not.eq', originalOrder);
            });
        } else {
          cy.log('Not enough FAQs to test ordering');
        }
      });
    });
  });
});

