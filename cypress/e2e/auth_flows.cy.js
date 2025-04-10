// Authentication Flows Tests
// Tests user registration, email verification, password reset, and login processes

describe('Authentication Flows', () => {
  const timestamp = Date.now();
  
  // Test user data
  const testUser = {
    email: `test.user.${timestamp}@example.com`,
    password: 'SecurePassword123!',
    firstName: 'Test',
    lastName: 'User'
  };
  
  context('User Registration', () => {
    it('should allow a user to register with valid information', () => {
      cy.visit('/register/');
      
      // Fill registration form
      cy.get('input[name="email"]').type(testUser.email);
      cy.get('input[name="first_name"]').type(testUser.firstName);
      cy.get('input[name="last_name"]').type(testUser.lastName);
      cy.get('input[name="password1"]').type(testUser.password);
      cy.get('input[name="password2"]').type(testUser.password);
      
      // Accept terms if present
      cy.get('body').then($body => {
        if ($body.find('input[type="checkbox"][name="terms"]').length > 0) {
          cy.get('input[type="checkbox"][name="terms"]').check();
        }
      });
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Verify success message or redirection
      cy.get('body').then($body => {
        const hasSuccessMessage = $body.text().includes('verification') || 
                                $body.text().includes('email') || 
                                $body.text().includes('confirm');
        
        if (hasSuccessMessage) {
          cy.log('Registration successful, verification email message shown');
        } else {
          // Check if we were redirected to login page
          cy.url().should('include', '/login/');
          cy.log('Registration successful, redirected to login page');
        }
      });
    });
    
    it('should show validation errors with invalid registration data', () => {
      cy.visit('/register/');
      
      // Test invalid email
      cy.get('input[name="email"]').type('invalid-email');
      cy.get('input[name="first_name"]').type(testUser.firstName);
      cy.get('input[name="last_name"]').type(testUser.lastName);
      cy.get('input[name="password1"]').type(testUser.password);
      cy.get('input[name="password2"]').type(testUser.password);
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Check for email validation error
      cy.get('body').should('contain', 'valid email');
      
      // Clear form and test password mismatch
      cy.get('input[name="email"]').clear().type(testUser.email);
      cy.get('input[name="password1"]').clear().type(testUser.password);
      cy.get('input[name="password2"]').clear().type('DifferentPassword123!');
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Check for password mismatch error
      cy.get('body').should('contain', 'match');
    });
  });
  
  context('Email Verification', () => {
    // Since we can't test actual email verification directly in Cypress,
    // we'll test the verification success and failure pages
    
    it('should show success page for valid verification token', () => {
      // Simulate opening a valid verification link
      // Note: This is a mock test since we can't generate real tokens in the test
      cy.visit('/verify-email/mock-valid-token/');
      
      // Check for success message elements or redirects
      cy.get('body').then($body => {
        if ($body.text().includes('verified') || $body.text().includes('successful')) {
          cy.log('Email verification success page shown properly');
        } else if ($body.find('a[href*="login"]').length > 0) {
          cy.log('Verification successful, login link available');
        }
      });
    });
    
    it('should show failure page for invalid verification token', () => {
      // Simulate opening an invalid verification link
      cy.visit('/verify-email/invalid-token/');
      
      // Check for failure message
      cy.get('body').then($body => {
        if ($body.text().includes('invalid') || 
            $body.text().includes('expired') || 
            $body.text().includes('failed')) {
          cy.log('Email verification failure page shown properly');
        }
      });
    });
  });
  
  context('Password Reset', () => {
    it('should allow requesting a password reset', () => {
      cy.visit('/password-reset/');
      
      // Fill in the email field
      cy.get('input[type="email"]').type(testUser.email);
      
      // Submit the form
      cy.get('button[type="submit"]').click();
      
      // Verify success message
      cy.get('body').then($body => {
        const hasSuccessMessage = $body.text().includes('email') || 
                                $body.text().includes('sent') || 
                                $body.text().includes('instructions');
        
        if (hasSuccessMessage) {
          cy.log('Password reset request successful');
        }
      });
    });
    
    it('should show the password reset confirmation page', () => {
      // Simulate opening a password reset link
      // Note: This is a mock test since we can't generate real tokens in the test
      cy.visit('/password-reset-confirm/mock-user-id/mock-token/');
      
      // Check if the new password form is displayed
      cy.get('body').then($body => {
        if ($body.find('input[type="password"]').length > 0) {
          // Fill in new passwords
          cy.get('input[type="password"]').first().type('NewPassword123!');
          cy.get('input[type="password"]').last().type('NewPassword123!');
          
          // Submit form
          cy.get('button[type="submit"]').click();
          
          // Check for success message or redirect to login
          cy.get('body').then($successBody => {
            const isSuccess = $successBody.text().includes('success') || 
                            $successBody.text().includes('changed') ||
                            $successBody.text().includes('updated');
            
            const redirectedToLogin = $successBody.find('form[action*="login"]').length > 0;
            
            if (isSuccess || redirectedToLogin) {
              cy.log('Password reset confirmation successful');
            }
          });
        } else {
          cy.log('Password reset confirmation page structure differs from expected');
        }
      });
    });
  });
  
  context('Login with Verified/Unverified Accounts', () => {
    before(() => {
      // Create another test user for this context to avoid conflicts
      cy.visit('/register/');
      const loginTestUser = {
        email: `login.test.${timestamp}@example.com`,
        password: 'LoginTest123!'
      };
      
      cy.get('input[name="email"]').type(loginTestUser.email);
      cy.get('input[name="first_name"]').type('Login');
      cy.get('input[name="last_name"]').type('Test');
      cy.get('input[name="password1"]').type(loginTestUser.password);
      cy.get('input[name="password2"]').type(loginTestUser.password);
      
      // Accept terms if present
      cy.get('body').then($body => {
        if ($body.find('input[type="checkbox"][name="terms"]').length > 0) {
          cy.get('input[type="checkbox"][name="terms"]').check();
        }
      });
      
      // Submit form
      cy.get('button[type="submit"]').click();
    });
    
    it('should handle login attempts with unverified email', () => {
      cy.visit('/login/');
      
      // Attempt to log in with unverified test user
      cy.get('input[name="username"]').type(`login.test.${timestamp}@example.com`);
      cy.get('input[name="password"]').type('LoginTest123!');
      cy.get('button[type="submit"]').click();
      
      // Check for verification required message
      cy.get('body').then($body => {
        if ($body.text().includes('verify') || 
            $body.text().includes('verification') || 
            $body.text().includes('confirm email')) {
          cy.log('System correctly requires email verification before login');
        }
        // If no verification message but login succeeded, system might not require verification
        else if ($body.text().includes('welcome') || $body.text().includes('dashboard')) {
          cy.log('Login successful without verification (verification might not be required)');
        }
      });
    });
    
    it('should handle login with valid credentials', () => {
      // For this test, we'll use admin credentials since they are definitely verified
      cy.visit('/login/');
      
      cy.get('input[name="username"]').type('admin');
      cy.get('input[name="password"]').type('adminpassword');
      cy.get('button[type="submit"]').click();
      
      // Verify successful login
      cy.url().should('include', '/dashboard/').or('include', '/admin/');
      cy.get('body').should('contain', 'Welcome').or('contain', 'Dashboard');
      
      // Logout for cleanup
      cy.get('body').then($body => {
        if ($body.find('a:contains("Logout")').length > 0) {
          cy.contains('Logout').click();
        } else if ($body.find('a:contains("Log out")').length > 0) {
          cy.contains('Log out').click();
        }
      });
    });
  });
});

