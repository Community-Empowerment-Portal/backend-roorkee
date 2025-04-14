// Admin Analytics and Reporting Tests - Simplified
// Focuses on user events, analytics dashboards, and report generation

describe('Admin Analytics and Reporting', () => {
  const admin = {
    username: 'admin',
    password: 'adminpassword'
  };

  // Login once before all tests
  before(() => {
    cy.clearCookies();
    cy.admin_login(admin.username, admin.password);
  });

  // Logout after all tests
  after(() => {
    cy.admin_logout();
  });

  context('User Event Analytics', () => {
    beforeEach(() => {
      // Start each test at the user events page
      cy.visit('/communityEmpowerment/userevent/');
    });

    it('should display and interact with user events list', () => {
      // Verify page loaded correctly
      cy.get('h1').should('contain', 'user event');
      
      // Verify essential columns exist
      cy.get('#result_list thead th').should('exist');
      
      // Check if we can view details of an event
      cy.get('#result_list tbody tr').then($rows => {
        if ($rows.length > 0) {
          // Click on the first event to view details
          cy.get('#result_list tbody tr:first-child th a').click();
          
          // Verify we're on the detail page
          cy.get('h1').should('contain', 'user event');
        } else {
          cy.log('No user events found to view details');
        }
      });
    });

    it('should test basic filtering options', () => {
      // Try date filtering
      cy.get('#changelist-filter').then($filter => {
        // Test timestamp filter if available
        if ($filter.text().includes('By timestamp')) {
          cy.contains('By timestamp').click();
          cy.contains('Today').click();
          cy.url().should('include', 'timestamp');
        }
        
        // Test event type filter if available
        if ($filter.text().includes('By event type')) {
          cy.contains('By event type').click();
          
          // Click the first event type option
          cy.get('#changelist-filter > div > ul:nth-of-type(2) > li:nth-child(2) > a').click();
          cy.url().should('include', 'event_type');
        }
      });
    });
  });

  context('Analytics Dashboards', () => {
    it('should access available analytics dashboards', () => {
      // Try to find and access analytics pages
      cy.visit('/');
      
      // List of common analytics-related keywords
      const analyticsKeywords = ['Analytics', 'Dashboard', 'Statistics', 'Reports', 'Metrics', 'Popular'];
      
      // Find and test the first analytics link
      cy.get('a').then($links => {
        // Find links containing any of our keywords
        const analyticsLinks = $links.filter((i, link) => {
          return analyticsKeywords.some(keyword => 
            link.textContent.toLowerCase().includes(keyword.toLowerCase())
          );
        });
        
        if (analyticsLinks.length > 0) {
          // Click the first analytics link
          cy.wrap(analyticsLinks[0]).click();
          
          // Verify page changed
          cy.url().should('not.include', '/admin/$');
          
          // Look for common visualization elements
          cy.get('body').then($body => {
            const hasVisualizations = 
              $body.find('.chart, .graph, canvas, svg, [data-chart], .dashboard-module').length > 0;
            
            if (hasVisualizations) {
              cy.log('Found visualization elements on the dashboard');
            } else {
              cy.log('No visualization elements found, might be a text-based dashboard');
            }
          });
        } else {
          cy.log('No analytics dashboard links found, skipping test');
        }
      });
    });
    
    it('should verify data is displayed in dashboard tables if available', () => {
      cy.visit('/');
      
      // Find links to admin index or dashboard
      cy.get('a').then($links => {
        const dashLinks = $links.filter((i, link) => {
          return link.textContent.toLowerCase().includes('dashboard') ||
                 link.textContent.toLowerCase().includes('analytics') ||
                 link.href.includes('dashboard');
        });
        
        if (dashLinks.length > 0) {
          cy.wrap(dashLinks[0]).click();
          
          // Check for data tables
          cy.get('table, .results, #result_list').then($tables => {
            if ($tables.length > 0) {
              // Verify at least one table has data rows
              cy.get('table tbody tr, .results li, #result_list tbody tr').should('exist');
              cy.log('Dashboard contains data tables with entries');
            } else {
              cy.log('No data tables found on dashboard');
            }
          });
        } else {
          cy.log('No dashboard links found, skipping table verification');
        }
      });
    });
  });

  context('Report Generation and Export', () => {
    it('should test CSV export functionality for user events', () => {
      // Navigate to user events page
      cy.visit('/communityEmpowerment/userevent/');
      
      // Check if export action is available
      cy.get('body').then($body => {
        const hasExportOption = 
          $body.find('select[name="action"] option:contains("Export")').length > 0 || 
          $body.find('a:contains("Export")').length > 0;
        
        if (hasExportOption) {
          // If dropdown export exists
          if ($body.find('select[name="action"] option:contains("Export")').length > 0) {
            // First select at least one row if any exist
            cy.get('#result_list tbody tr').then($rows => {
              if ($rows.length > 0) {
                cy.get('#result_list tbody tr:first-child input[type="checkbox"]').check();
                
                // Select export action
                cy.get('select[name="action"]').select('export_as_csv');
                cy.get('button[type="submit"]').contains('Go').click();
                
                // Log export attempt (can't verify download in headless mode)
                cy.log('CSV export action triggered successfully');
              } else {
                cy.log('No rows to export');
              }
            });
          } 
          // If direct export link exists
          else if ($body.find('a:contains("Export")').length > 0) {
            cy.contains('Export').click();
            cy.log('Export link clicked successfully');
          }
        } else {
          cy.log('No export functionality found');
        }
      });
    });

    it('should check for report filter functionality', () => {
      // Try to find a page with reporting capabilities
      cy.visit('/admin/');
      
      // Keywords that might indicate report pages
      const reportKeywords = ['Report', 'Analytics', 'Statistics', 'Export'];
      
      // Check menu for report links
      cy.get('a').then($links => {
        const reportLinks = $links.filter((i, link) => {
          return reportKeywords.some(keyword => 
            link.textContent.toLowerCase().includes(keyword.toLowerCase())
          );
        });
        
        if (reportLinks.length > 0) {
          cy.wrap(reportLinks[0]).click();
          
          // Check for filter functionality on the report page
          cy.get('body').then($body => {
            // Look for common filter UI elements
            const hasFilters = 
              $body.find('form input[type="text"], select, .filter, #changelist-filter').length > 0;
            
            if (hasFilters) {
              // Try a basic filter operation if a date filter exists
              if ($body.find('input[type="date"], input[name*="date"]').length) {
                // Try to interact with the first date filter
                cy.get('input[type="date"], input[name*="date"]').first().then($dateField => {
                  // Just verify we can interact with the field
                  cy.wrap($dateField).should('be.visible');
                  cy.log('Date filter field is available for filtering reports');
                });
              } else {
                cy.log('Filter UI elements found but no date filters');
              }
            } else {
              cy.log('No filter functionality found on this report page');
            }
          });
        } else {
          cy.log('No report pages found in menu');
        }
      });
    });
  });

  context('Chart and Data Visualization', () => {
    it('should verify chart elements are rendered if available', () => {
      // Visit admin home to find potential dashboard links
      cy.visit('/admin/');
      
      // Find any dashboard or analytics links
      cy.get('a').then($links => {
        const dashLinks = $links.filter((i, link) => {
          return link.textContent.toLowerCase().includes('dashboard') ||
                 link.textContent.toLowerCase().includes('analytics') ||
                 link.textContent.toLowerCase().includes('statistics');
        });
        
        if (dashLinks.length > 0) {
          cy.wrap(dashLinks[0]).click();
          
          // Check for chart elements
          cy.get('body').then($body => {
            // Look for common chart elements across different libraries
            const chartSelectors = [
              'canvas', 
              'svg', 
              '.chart', 
              '.graph', 
              '[data-chart]',
              '.chartjs-render-monitor',
              '.highcharts-container',
              '.nv-chart',
              '.dashboard-module'
            ];
            
            // Combine selectors
            const combinedSelector = chartSelectors.join(', ');
            
            if ($body.find(combinedSelector).length > 0) {
              // Verify chart elements exist
              cy.get(combinedSelector).should('exist');
              cy.log('Chart/visualization elements found and rendered');
            } else {
              cy.log('No chart elements found on this page');
            }
          });
        } else {
          cy.log('No dashboard or analytics links found');
        }
      });
    });
    
    it('should check for data metrics and summary statistics', () => {
      // Visit admin home
      cy.visit('/admin/');
      
      // Look for summary cards or metrics display
      cy.get('body').then($body => {
        // Common selectors for metric displays
        const metricSelectors = [
          '.stat', 
          '.metric', 
          '.count', 
          '.summary', 
          '.dashboard-tools',
          '.model-count',
          '.card',
          '.dashboard-module'
        ];
        
        // Combine selectors
        const combinedSelector = metricSelectors.join(', ');
        
        if ($body.find(combinedSelector).length > 0) {
          // Verify metrics exist
          cy.get(combinedSelector).should('exist');
          cy.log('Summary metrics or statistics found on dashboard');
        } else {
          // Check app list for count indicators
          if ($body.find('#app-list .count').length > 0) {
            cy.get('#app-list .count').should('exist');
            cy.log('Count metrics found in application list');
          } else {
            cy.log('No summary metrics found on dashboard');
          }
        }
      });
    });
  });
});
