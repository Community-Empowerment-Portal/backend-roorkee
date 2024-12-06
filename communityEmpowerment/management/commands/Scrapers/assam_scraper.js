const puppeteer = require('puppeteer');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');

// Function to generate unique IDs
const generateUUID = () => uuidv4();

async function scrapeSchemes(url) {
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();
    await page.goto(url, { waitUntil: 'networkidle2' });

    const data = await page.evaluate(() => {
        const getTextContent = (element) => element ? element.textContent.trim() : '';

        // Function to clean Roman numerals and unwanted characters from description
        const cleanDescription = (description) => {
            return description.replace(/(\([ivxlc]+\)|[ivxlc]+\))/gi, '').trim().replace(/^\s*[-:]+\s*/, '').replace(/<br>/g, ' ');
        };

        // Function to extract title from strong tag inside p tag
        const extractTitleFromStrong = (pElement) => {
            const strongElement = pElement.querySelector('strong');
            if (strongElement) {
              return getTextContent(strongElement);
          } else {
              const text = getTextContent(pElement);
              // Extract title from text if it starts with a pattern such as "(i)", "(ii)", etc.
              const match = text.match(/^\(\w+\)\s*(.*?)(?=:| -|:| -| -)/);
              return match ? match[1] : 'No Title';
          }
        };

        const schemes = [];
        const container = document.querySelector('.pane-content .view-content');
        if (container) {
            const sections = container.querySelectorAll('.views-field.views-field-php .field-content .text-wrap p');
            sections.forEach((section) => {
                const title = extractTitleFromStrong(section);
                let description = getTextContent(section).replace(title, '').trim();
                
                description = cleanDescription(description);

                schemes.push({
                    title: title,
                    description: description
                });
            });
        }
        return schemes;
    });

    // Generate UUIDs in Node.js context
    const dataWithUUIDs = data.map(scheme => ({
        id: generateUUID(),
        ...scheme
    }));

    await browser.close();
    return dataWithUUIDs;
}

(async () => {
    const urls = [
        'https://wptbc.assam.gov.in/frontimpotentdata/schemes-for-welfare-of-obc',
        'https://wptbc.assam.gov.in/frontimpotentdata/scheme-for-welfare-of-sc',
        'https://wptbc.assam.gov.in/frontimpotentdata/welfare-schemes-for-st',
        'https://wptbc.assam.gov.in/information-services/central-earmarked-scheme-to-sc'
    ];

    let allData = [];

    for (const url of urls) {
        try {
            const data = await scrapeSchemes(url);
            allData = allData.concat(data);
        } catch (error) {
            console.error(`Error during scraping ${url}`, error);
        }
    }


    // Save data to assam_schemes.json
    const targetDir = path.join(__dirname, '..','..','scrapedData');
    const filePath = path.join(targetDir, 'assam.json');
    fs.writeFile(filePath, JSON.stringify(allData, null, 2), (err) => {
        if (err) {
            console.error('Error writing to file', err);
        } else {
            console.log('Data successfully saved to assam.json');
        }
    });
})();