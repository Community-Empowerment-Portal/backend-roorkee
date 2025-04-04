Cypress.Commands.add('admin_login', (name, password) =>{
    cy.visit('/')
    // Login as Admin
    cy.get('input[name="username"]').type(name)
    cy.get('input[name="password"]').type(password)
    cy.get('input[type="submit"]').click()
})

Cypress.Commands.add('admin_logout',()=>{
    cy.contains('Log out').should('be.visible').click()
})

Cypress.Commands.add('save',()=>{
    cy.get('input[name="_save"]').click()
})