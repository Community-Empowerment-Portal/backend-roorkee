const puppeteer = require('puppeteer');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');

// Define possible selectors for each field
const fieldSelectors = {
    title: ['.field-name-body .field-item strong', '.scheme-title h1', '.title-class'],
    description: ['.field-name-body .field-item', '.scheme-description', '.description-class'],
    eligibility: ['strong:contains("ELIGIBILITY:-")','strong:contains("ELIGIBILITY:")', 'p:contains("ELIGIBILITY")', '.eligibility-class'],
    funding: ['strong:contains("FUNDING")', 'strong:contains("FUNDING PATTERN:-")','p:contains("FUNDING")', '.funding-class'],
    subsidy: ['strong:contains("SUBSIDY")','strong:contains("SUBSIDY:-")', 'strong:contains("SUBSIDY:")','p:contains("SUBSIDY")', '.subsidy-class'],
    sources: ['strong:contains("SOURCES OF FUNDS")', 'strong:contains("SOURCES OF FUNDS:-")','p:contains("SOURCES")', '.sources-class'],
    repayment: ['strong:contains("REPAYMENT")','strong:contains("REPAYMENT:-")', 'p:contains("REPAYMENT")', '.repayment-class'],
    rateOfInterest: ['strong:contains("RATE OF INTEREST :-")','strong:contains("Loan:")','strong:contains("RATE OF INTEREST:-")', 'p:contains("RATE OF INTEREST")', '.rate-class'],
    procedure: ['strong:contains("PROCEDURE FOR TAKING LOAN")','strong:contains("Procedure for taking loan:")','strong:contains("PROCEDURE FOR TAKING LOAN:-")', 'p:contains("PROCEDURE")', '.procedure-class']
};

async function scrapeScheme(url) {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle2' });

  const data = await page.evaluate((fieldSelectors) => {
    const getTextContent = (selectors) => {
      for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) return element.textContent.trim();
      }
      return '';
    };

    const getDescription = (selectors) => {
      for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) return element.innerText.trim();
      }
      return '';
    };

    const getStructuredData = () => {
      const structuredData = {
        'ELIGIBILITY': '',
        'FUNDING PATTERN': '',
        'SUBSIDY': '',
        'SOURCES OF FUNDS': '',
        'REPAYMENT': '',
        'RATE OF INTEREST': '',
        'PROCEDURE FOR TAKING LOAN': '',
        'Description': ''
      };

      const descriptionElement = document.querySelector('.field-name-body .field-item');
      if (!descriptionElement) return structuredData;

      const paragraphs = descriptionElement.querySelectorAll('p, div, ul');
      paragraphs.forEach(p => {
        const strong = p.querySelector('strong');
        if (strong) {
          const key = strong.textContent.replace(/[:-]/g, '').trim().toUpperCase();
          const value = p.innerHTML.replace(/<strong>.*<\/strong>/, '').replace(/<br\s*\/?>/g, '').trim();
          if (structuredData.hasOwnProperty(key)) {
            structuredData[key] = value;
          } else {
            structuredData['Description'] += value + ' ';
          }
        } else {
          structuredData['Description'] += p.textContent.replace(/<br\s*\/?>/g, '').trim() + ' ';
        }
      });

      // Trim extra spaces
      Object.keys(structuredData).forEach(key => {
        structuredData[key] = structuredData[key].trim();
      });

      return structuredData;
    };

    const title = getTextContent(fieldSelectors.title);
    const description = getDescription(fieldSelectors.description);
    const structuredData = getStructuredData();

    return {
      title,
      description,
      ...structuredData
    };
  }, fieldSelectors);

  await browser.close();
  return data;
}

(async () => {
  const urls = [
    'https://pbscfc.punjab.gov.in/?q=node/26',
    'https://pbscfc.punjab.gov.in/?q=node/29',
    'https://pbscfc.punjab.gov.in/?q=node/165',
    'https://pbscfc.punjab.gov.in/?q=node/25',
    'https://pbscfc.punjab.gov.in/?q=node/30',
    'https://pbscfc.punjab.gov.in/?q=node/31'
  ];

  const allData = {};

  for (const url of urls) {
    console.log(`Scraping URL: ${url}`);
    try {
      const data = await scrapeScheme(url);
      const schemeId = uuidv4(); // Generate a unique ID for each scheme
      if (data.title) {
        const schemeName = data.title || `Scheme from ${url}`;
        console.log(`Extracted data for scheme: ${schemeName}`);
        allData[schemeId] = {
          id: schemeId,
          ...data
        };
      } else {
        console.log(`No title found for URL: ${url}`);
      }
    } catch (error) {
      console.error(`Error scraping URL: ${url}`, error);
    }
  }

  // Save data to punjab_scheme.json
    const targetDir = path.join(__dirname, '..','..','scrapedData');
    const filePath = path.join(targetDir, 'punjab.json');
  fs.writeFile(filePath, JSON.stringify(allData, null, 2), (err) => {
    if (err) {
      console.error('Error writing to file', err);
    } else {
      console.log('Data successfully saved to punjab_schemes.json');
    }
  });
})();