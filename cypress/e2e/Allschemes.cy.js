describe('All Schemes - Admin Panel CRUD Tests', () => {

    const models = [
      { name: 'Schemes', url: '/admin/communityEmpowerment/scheme/',
        data: {
        'input[name="benefit_type"]': "benefit_type_Test", 
        'input[name="description"]': "description_Test"
          }
      },
      { name: 'Benefits', url: '/admin/communityEmpowerment/benefit/',
        data: {
        'input[name="benefit_type"]': "benefit_type_Test", 
        'input[name="description"]': "description_Test"
          }
       },
      { name: 'Criteria', url: '/admin/communityEmpowerment/criteria/',
        data: {
            'input[name="benefit_type"]': "benefit_type_Test", 
            'input[name="description"]': "description_Test"
          }
       },
      { name: 'Departments', url: '/admin/communityEmpowerment/department/',
        data: {
            'input[name="benefit_type"]': "benefit_type_Test", 
            'input[name="description"]': "description_Test"
          }
       },
      { name: 'Organizations', url: '/admin/communityEmpowerment/organisation/',
        data: {
            'input[name="benefit_type"]': "benefit_type_Test", 
            'input[name="description"]': "description_Test"
          }
       },
      { name: 'Procedures', url: '/admin/communityEmpowerment/procedure/',
        data: {
            'input[name="benefit_type"]': "benefit_type_Test", 
            'input[name="description"]': "description_Test"
          }
       },
      { name: 'Scheme Beneficiaries', url: '/admin/communityEmpowerment/schemebeneficiary/',
        data: {
            'input[name="benefit_type"]': "benefit_type_Test", 
            'input[name="description"]': "description_Test"
          }
       },
      { name: 'Documents', url: '/admin/communityEmpowerment/document/',
        data: {
            'input[name="benefit_type"]': "benefit_type_Test", 
            'input[name="description"]': "description_Test"
          }
       },
      { name: 'Scheme Sponsors', url: '/admin/communityEmpowerment/schemesponsor/',
        data: {
            'input[name="benefit_type"]': "benefit_type_Test", 
            'input[name="description"]': "description_Test"
          }
       },
      { name: 'States', url: '/admin/communityEmpowerment/state/',
        data: {
            'input[name="benefit_type"]': "benefit_type_Test", 
            'input[name="description"]': "description_Test"
          }
       },
      { name: 'Tags', url: '/admin/communityEmpowerment/tag/',
        data: {
            'input[name="benefit_type"]': "benefit_type_Test", 
            'input[name="description"]': "description_Test"
          }
       },
      { name: 'Resources', url: '/admin/communityEmpowerment/resource/',
        data: {
            'input[name="benefit_type"]': "benefit_type_Test", 
            'input[name="description"]': "description_Test"
          }
       },
      { name: 'Company Meta', url: '/admin/communityEmpowerment/companymeta/',
        data: {
            'input[name="name"]': "name_Test", 
            'input[name="tagline"]': "tagline_Test",
            'input[name="description"]': "description_Test",
            'input[name="email"]': "description_Test",
          }
       }
    ];
  
    before(() => {
      cy.admin_login('karthik', 'Test@123'); // Log in once before tests
    });
  
    models.forEach((model) => {
      
      it(`Create, Read, Update, and Delete a record in ${model.name}`, () => {
  
        //Step 1: Visit Model List Page
        cy.visit(model.url);
        cy.url().should('include', model.url);
        
        //Step 2: Create a New Record
        cy.get('.addlink').click();
        cy.get('input, textarea, select').first().type('Test Entry'); 
        cy.save();
        cy.contains('was added successfully').should('be.visible');
  
        //Step 3: Read (Check List Page)
        cy.visit(model.url);
        cy.contains('Test Entry').should('be.visible');
  
        //Step 4: Update the Record
        cy.contains('Test Entry').click();
        cy.get('input, textarea, select').first().clear().type('Updated Entry'); 
        cy.save();
        cy.contains('was changed successfully').should('be.visible');
  
        //Step 5: Delete the Record
        cy.visit(model.url);
        cy.contains('Updated Entry').click();
        cy.get('.deletelink').click();
        cy.get('input[value="Yes, I’m sure"]').click();
        cy.contains('was deleted successfully').should('be.visible');
  
      });
  
    });
  
    after(() => {
      cy.admin_logout(); // Log out after tests
    });
  
  });
  