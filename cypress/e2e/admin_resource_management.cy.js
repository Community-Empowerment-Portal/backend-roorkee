describe('Admin Resource Management', () => {
  const admin = { username: 'admin', password: 'adminpassword' };
  const editor = { username: 'editor', password: 'editorpassword' };
  const timestamp = Date.now();

  const resources = {
    faq: {
      model: 'faq',
      nameField: 'question',
      title: `Test FAQ ${timestamp}`,
      updatedTitle: `Updated FAQ ${timestamp}`,
      fields: {
        question: `Test FAQ ${timestamp}`,
        answer: 'This is a test FAQ answer.',
        order: '10',
        is_active: true
      }
    },
    banner: {
      model: 'banner',
      nameField: 'title',
      title: `Test Banner ${timestamp}`,
      updatedTitle: `Updated Banner ${timestamp}`,
      fields: {
        title: `Test Banner ${timestamp}`,
        description: 'This is a test banner.',
        is_active: true
      }
    },
    announcement: {
      model: 'announcement',
      nameField: 'title',
      title: `Test Announcement ${timestamp}`,
      updatedTitle: `Updated Announcement ${timestamp}`,
      fields: {
        title: `Test Announcement ${timestamp}`,
        description: 'This is a test announcement.',
        is_active: true
      }
    }
  };

  beforeEach(() => {
    cy.clearCookies();
    cy.admin_login(admin.username, admin.password);
  });

  after(() => {
    cy.admin_logout();
  });

  const fillForm = (fields) => {
    Object.entries(fields).forEach(([key, value]) => {
      const type = typeof value === 'boolean' ? 'checkbox'
                : ['answer', 'description', 'question'].includes(key) ? 'textarea'
                : 'input';
      cy.fillAdminForm({ [key]: value }, type);
    });
  };

  const testResource = (key) => {
    const resource = resources[key];
    const baseUrl = `/communityEmpowerment/${resource.model}/`;

    context(`${key.toUpperCase()} Resource`, () => {
      it('should create', () => {
        cy.visit(`${baseUrl}add/`);
        fillForm(resource.fields);
        cy.save();
        cy.verifyMessage('success', 'added successfully');
        cy.verifyListView(resource.model, resource.title);
      });

      it('should edit', () => {
        cy.visit(baseUrl);
        cy.contains('tr', resource.title).find('th a').click();
        cy.fillAdminForm({ [resource.nameField]: resource.updatedTitle }, 'input');
        cy.save();
        cy.verifyMessage('success', 'changed successfully');
        cy.verifyListView(resource.model, resource.updatedTitle);
        resource.title = resource.updatedTitle; // update title for next tests
      });

      it('should toggle active status', () => {
        cy.visit(baseUrl);
        cy.contains('tr', resource.title).within(() => {
          cy.get('input[name*="is_active"]').click();
        });
        cy.get('input[name="_save"]').click();
        cy.verifyMessage('success', 'successfully');
      });

      it('should delete', () => {
        cy.visit(baseUrl);
        cy.contains('tr', resource.title).find('th a').click();
        cy.contains('Delete').click();
        cy.get('input[type="submit"][value="Yes, I’m sure"]').click();
        cy.verifyMessage('success', 'deleted successfully');
        cy.verifyListView(resource.model, resource.title, false);
      });
    });
  };

  ['faq', 'banner', 'announcement'].forEach(testResource);

  context('Permission Tests (Editor)', () => {
    const question = `Permission Test FAQ ${timestamp}`;

    before(() => {
      cy.visit('/communityEmpowerment/faq/add/');
      fillForm({
        question,
        answer: 'Permission test answer.',
        is_active: true
      });
      cy.save();
    });

    after(() => {
      cy.visit('/communityEmpowerment/faq/');
      cy.contains('tr', question).then($row => {
        if ($row.length) {
          cy.wrap($row).find('th a').click();
          cy.contains('Delete').click();
          cy.get('input[type="submit"][value="Yes, I’m sure"]').click();
        }
      });
    });

    it('should check editor permissions', () => {
      cy.admin_logout();
      cy.admin_login(editor.username, editor.password);
      cy.visit('/communityEmpowerment/faq/');

      cy.get('body').then($body => {
        const canAdd = $body.find('a.addlink').length > 0;
        cy.log(`Editor ${canAdd ? 'can' : 'cannot'} add FAQs`);

        if ($body.find(`tr:contains("${question}")`).length) {
          cy.contains('tr', question).find('th a').click();
          const canEdit = $body.find('input[name="_save"]').length > 0;
          cy.log(`Editor ${canEdit ? 'can' : 'cannot'} edit FAQs`);
        }
      });

      cy.admin_logout();
      cy.admin_login(admin.username, admin.password);
    });
  });

  context('Bulk Operations & Filtering', () => {
    const bulkFAQs = Array.from({ length: 3 }, (_, i) => ({
      question: `Bulk FAQ ${i + 1} - ${timestamp}`,
      answer: `Bulk answer ${i + 1}`,
      is_active: i % 2 === 0
    }));

    before(() => {
      bulkFAQs.forEach(faq => {
        cy.visit('/communityEmpowerment/faq/add/');
        fillForm(faq);
        cy.save();
      });
    });

    it('should filter by active status', () => {
      cy.visit('/communityEmpowerment/faq/');
      cy.get('#changelist-filter').contains('Active').click();
      cy.get('#changelist-filter').contains('Yes').click();

      bulkFAQs.forEach(faq => {
        cy.contains(faq.question).should(faq.is_active ? 'exist' : 'not.exist');
      });
    });

    it('should bulk delete FAQs', () => {
      cy.visit('/communityEmpowerment/faq/');
      bulkFAQs.forEach(faq => {
        cy.contains('tr', faq.question).find('input[type="checkbox"]').check({ force: true });
      });

      cy.get('select[name="action"]').select('delete_selected');
      cy.get('button[type="submit"]').contains('Go').click();
      cy.get('input[type="submit"][value="Yes, I’m sure"]').click();
      cy.verifyMessage('success', 'successfully deleted');

      bulkFAQs.forEach(faq => {
        cy.contains(faq.question).should('not.exist');
      });
    });
  });
});
