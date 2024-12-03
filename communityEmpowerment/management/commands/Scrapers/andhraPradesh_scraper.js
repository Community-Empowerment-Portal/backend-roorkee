const puppeteer = require('puppeteer');
const fs = require('fs');

async function scrapeData() {
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();
    
    // Replace with the target URL
    const url = 'https://socialwelfare.apcfss.in/schemes.html';
    await page.goto(url, { waitUntil: 'domcontentloaded' });

    const data = await page.evaluate(() => {
        const result = [];
        
        // Function to clean up text
        const cleanText = (text) => {
            return text.replace(/\n/g, ' ').trim();
        };
        
        const sections = document.querySelectorAll('.col-xs-12.col-sm-12.col-md-12.col-lg-12');
        
        sections.forEach(section => {
            const titles = section.querySelectorAll('.captions, .captions2');
            titles.forEach(title => {
                const titleText = cleanText(title.innerText);
                const paragraphs = [];
                let nextElement = title.nextElementSibling;
                while (nextElement && nextElement.tagName.toLowerCase() === 'p') {
                    paragraphs.push(cleanText(nextElement.innerText));
                    nextElement = nextElement.nextElementSibling;
                }
                result.push({
                    title: titleText,
                    description: paragraphs.join(' ')
                });
            });
        });

        return result;
    });

    // Save data to a JSON file
    const targetDir = path.join(__dirname, '..','..','scrapedData');
    const filePath = path.join(targetDir, 'andhra.json');
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
    
    await browser.close();
}

scrapeData();