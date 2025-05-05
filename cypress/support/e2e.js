// cypress/support/e2e.js

// Import commands.js using ES2015 syntax:
import './commands'

// Import helpers
import { loadTestUsersConfig, setupTestUser, verifyUserPermissions, checkModelPermissions } from './helpers'

// Make helpers available globally
Cypress.Commands.add('loadTestUsersConfig', loadTestUsersConfig);
Cypress.Commands.add('setupTestUser', setupTestUser);
Cypress.Commands.add('verifyUserPermissions', verifyUserPermissions);
Cypress.Commands.add('checkModelPermissions', checkModelPermissions);

// Configure Cypress for Django admin testing
Cypress.on('uncaught:exception', (err, runnable) => {
  // Return false to prevent Cypress from failing the test
  return false
})

// Add custom assertions
chai.Assertion.addMethod('containSuccess', function () {
  this.assert(
    this._obj.find('.success').length > 0,
    'expected element to contain success message',
    'expected element to not contain success message'
  )
})

// Configure default behavior
beforeEach(() => {
  // Reset viewport size
  cy.viewport(1200, 800)
  
  // Clear cookies and local storage
  cy.clearCookies()
  cy.clearLocalStorage()
})

// Add custom commands for Django admin testing
Cypress.Commands.add('waitForDjango', () => {
  // Wait for Django admin to be ready
  cy.get('body').should('not.have.class', 'loading')
})

Cypress.Commands.add('checkDjangoError', () => {
  // Check for Django error pages
  cy.get('body').then($body => {
    if ($body.find('.errornote').length) {
      throw new Error('Django error page encountered')
    }
  })
})
