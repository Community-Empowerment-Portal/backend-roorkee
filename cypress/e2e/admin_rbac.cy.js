describe('Django Admin RBAC with Groups', () => {
  it('Admin creates a group, assigns permissions, and adds a user to the group', () => {
   
    //admin login
    cy.admin_login('karthik', 'Test@123')
    // Go to Group Creation Page
    cy.visit('/auth/group/add/')

    // Create a new group
    cy.get('input[name="name"]').type('Viewer')

    // Filter all view permissions
    cy.get('input[placeholder="Filter"]').first().type('view')

    // Choose All the permisssions
    cy.get('.selector-chooseall').click()

    // Save the changes 
    cy.save()

    // Ensuring auto redirect to groups page 
    cy.url().should('include', '/auth/group')
    
    // Ensure the group created is visible 
    cy.contains('Viewer').should('be.visible')

    // Go to user creation page
    cy.visit('/communityEmpowerment/customuser/add/')

    // Enter the required credentials
    cy.get('input[name="username"]').type('testuser')
    cy.get('input[name="email"]').type('testuser@gmail.com')
    cy.get('input[name="password1"]').type('Epson&l3115')
    cy.get('input[name="password2"]').type('Epson&l3115')

    //Note: not checking is_staff checkbox to check accessibility to admin portal 
    cy.save()
    cy.admin_logout()

    // Login as a non staff user
    cy.admin_login('testuser','Passw0rd')

    // ensure error is thrown 
    cy.get('.errornote').should('be.visible')

    cy.admin_login('karthik', 'Test@123')
    cy.visit('/communityEmpowerment/customuser')
    cy.contains('testuser').should('be.visible').click()
    cy.get('.deletelink').click()
    cy.get('input[value="Yes, I’m sure"]').should('be.visible').click()

    // Go to user creation page
    cy.visit('/communityEmpowerment/customuser/add/')

    // Enter the required credentials
    cy.get('input[name="username"]').type('testuser')
    cy.get('input[name="email"]').type('testuser@gmail.com')
    cy.get('input[name="password1"]').type('Epson&l3115')
    cy.get('input[name="password2"]').type('Epson&l3115')

    cy.get('input[name="is_staff"]').check()
    cy.get('input[name="_continue"]').click()
    cy.get('option[title="Viewer"]').click()
    cy.get('#id_groups_add_link').click()
    cy.save()
    cy.admin_logout()
    cy.admin_login('testuser','Epson&l3115')

  })

})
