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

        // Function to clean unwanted characters from description
        const cleanDescription = (description) => {
            return description
                .replace(/\s*:\s*$/, '') // Remove trailing colons
                .replace(/^\s*[-:]+\s*/, '') // Remove leading dashes or colons
                .replace(/<br>/g, ' '); // Replace <br> with space
        };
        

        const schemes = [];
        const container = document.querySelector('article.item-page');
        if (container) {
            const sections = container.querySelectorAll('p');
            let currentTitle = '';
            let currentDescription = '';

            sections.forEach((section) => {
                const strongElement = section.querySelector('strong');
                if (strongElement) {
                    // If there is an existing title and description, push it to schemes
                    if (currentTitle && currentDescription) {
                        schemes.push({
                            title: currentTitle.replace(/\s*:\s*$/, ''),
                            description: cleanDescription(currentDescription)
                        });
                        currentDescription = ''; // Reset description for next scheme
                    }
                    // Update the title for the new scheme
                    currentTitle = getTextContent(strongElement);
                } else {
                    // Accumulate the description
                    currentDescription += getTextContent(section) + ' ';
                }
            });

            // Push the last scheme
            if (currentTitle && currentDescription) {
                schemes.push({
                    title: currentTitle.replace(/\s*:\s*$/, ''),
                    description: cleanDescription(currentDescription)
                });
            }
        }
        return schemes;
    });

    // Generate UUIDs in Node.js context
    const dataWithUUIDs = data.map(scheme => ({
        id: generateUUID(),
        schemeUrl: url,
        ...scheme

    }));

    await browser.close();
    return dataWithUUIDs;
}

(async () => {
    const urls = [
        'https://scdd.kerala.gov.in/index.php/schemes/educational-programmes',
       ' https://scdd.kerala.gov.in/index.php/schemes/economic-development-programmes',
        'https://scdd.kerala.gov.in/index.php/schemes/social-development-schemes'
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



    // Save Kerala data to kerala.json
    const targetDir = path.join(__dirname, '..','..','scrapedData');
    const filePath = path.join(targetDir, 'kerela.json');    
    fs.writeFile(filePath, JSON.stringify(allData, null, 2), (err) => {
        if (err) {
            console.error('Error writing to file', err);
        } else {
            console.log('Data successfully saved to kerala.json');
        }
    });
})();
