const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const { v4: uuidv4 } = require('uuid');

let allResults = [];

async function departmental_pdf_links() {
    const url = 'https://sje.rajasthan.gov.in/Default.aspx?PageID=3453';
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto(url, { timeout: 60000 });

    const result = await page.evaluate(() => {
        let data = [];
        const rows = document.querySelectorAll('.tbl tbody tr');
        rows.forEach((it, index) => {
            if (index === 0) return; 
            const title = it.children[1].children[0]?.textContent;
            const schemeUrl = it.children[1].children[0]?.href;
            const requireDocumentsUrl = it.children[2].children[0]?.href;
            const userManualUrl = it.children[3].children[0]?.href;
            data.push({ title, schemeUrl, requireDocumentsUrl, userManualUrl });
        });
        return data;
    });

    const resultWithUUID = result.map(item => ({ id: uuidv4(), ...item }));
    await fs.writeFile('rajasthan-department-scheme_url.json', JSON.stringify(resultWithUUID, null, 2));
    await browser.close();
}
departmental_pdf_links()

async function scrape_title_and_pdfUrl(urls) {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    for (const url of urls) {
        try {
            await page.goto(url, { timeout: 60000 });

            let result = await page.evaluate(() => {
                let data = [];
                const rows = document.querySelectorAll('p a');
                rows.forEach((it) => {
                    const title = it.textContent.trim();
                    const pdfUrl = it.href;
                    data.push({ title, pdfUrl });
                });
                return data;
            });

            for (let res of result) {
                if (!res.pdfUrl.endsWith('.pdf')) {
                    res.pdfUrl = await getEmbedSrc(res.pdfUrl, browser);
                }
            }

            allResults = [...allResults, ...result];
        } catch (err) {
            console.error(`Error scraping ${url}:`, err);
        }
    }

    const resultWithUUID = allResults.map(item => ({ id: uuidv4(), ...item }));
    const targetDir = path.join(__dirname, '..','..','scrapedData', 'scrapedPdfs');
    const filePath = path.join(targetDir, 'rajasthanPdf.json');
    await fs.writeFile(filePath, JSON.stringify(resultWithUUID, null, 2), 'utf8');

    console.log('Scraping complete. Results saved to rajasthan-pdf-links.json.');
    await browser.close();
}

async function getEmbedSrc(url, browser) {
    const page = await browser.newPage();
    let embedSrc = null;

    try {
        await page.goto(url, { timeout: 60000 });
        embedSrc = await page.evaluate(() => {
            const embedTag = document.querySelector('embed');
            return embedTag ? embedTag.src : null;
        });
    } catch (err) {
        console.error(`Error fetching embed src for ${url}:`, err);
    }
    await page.close();
    return embedSrc;
}

async function getUrls(base_url) {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto(base_url, { timeout: 60000 });

    const result = await page.evaluate(() => {
        let allUrls = [];
        const links = document.querySelectorAll('li div a');
        links.forEach((it) => {
            const link = it.href;
            const title = it.textContent.trim();
            if (link.endsWith('.pdf')) {
                allUrls.push({ title, pdfUrl: link });
            } else {
                allUrls.push(link);
            }
        });
        return allUrls;
    });

    await browser.close();
    return result.map(item => (typeof item === 'string' ? item : { id: uuidv4(), ...item }));
}

(async () => {
    const base_url = 'https://sje.rajasthan.gov.in/Default.aspx?PageID=2';
    const res = await getUrls(base_url);

    const urls = [];
    res.forEach(url => {
        if (typeof url === 'string') urls.push(url);
        else allResults.push(url);
    });

    await scrape_title_and_pdfUrl(urls);
})();