const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");
const { v4: uuidv4 } = require("uuid");
const { fileURLToPath } = require('url');
const { dirname } = require('path');



const config = {
  baseUrl: "https://sjsa.maharashtra.gov.in/en/schemes-categories",
  selectors: {
    menuItems: ".mainColum .menu-block-wrapper li",
    menuLink: "a",
    accordion: ".accoSchemes",
    title: ".accTrigger h3",
    tables: ".tableData",
    tableRows: "tbody tr",
    cells: "td, th",
    nextButton: ".pager-next",
  },
};

async function extractUrls() {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(config.baseUrl, { waitUntil: "networkidle2" });
  const urls = await page.evaluate((selectors) => {
    const list = document.querySelectorAll(selectors.menuItems);
    const pageUrls = [];
    list.forEach((item) => {
      const link = item.querySelector(selectors.menuLink);
      if (link) {
        pageUrls.push(link.href);
      }
    });
    return pageUrls;
  }, config.selectors);
  await browser.close();
  return urls;
} //extracting the scheme page url

async function scrapeData(url, selectors, allSchemes) {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  const schemes = [];

  try {
    await page.goto(url, { waitUntil: "networkidle2" });
    let hasNextPage = true;
    // let pageIndex = 0;

    while (hasNextPage) {
      // const paginatedUrl = `${url}?page=${pageIndex}`;
      await page.waitForSelector(selectors.accordion);
      const data = await page.evaluate((selectors) => {
        const accordionItems = document.querySelectorAll(selectors.accordion);
        const extractedData = [];

        accordionItems.forEach((item) => {
          const title = item.querySelector(selectors.title)
            .innerText.replace(/\n/g, "")
            .replace(/\t/g, "")
            .trim();

          let details = {};
          const tables = item.querySelectorAll(selectors.tables);
          tables.forEach((table, tableIndex) => {
            const tableRows = table.querySelectorAll(selectors.tableRows);
            if (tableIndex === 0) {
              tableRows.forEach((row) => {
                const cells = row.querySelectorAll(selectors.cells);
                if (cells.length === 3 && cells[1].innerText !== "Scheme") {
                  const key = cells[1].innerText
                    .replace(/\n/g, "")
                    .replace(/\t/g, "")
                    .trim();
                  const value = cells[2].innerText
                    .replace(/\n/g, "")
                    .replace(/\t/g, "")
                    .trim();
                  details[key] = value;
                }
              });
            } else {
              const stats = [];
              tableRows.forEach((row) => {
                const cells = row.querySelectorAll(selectors.cells);
                if (cells.length === 4 && cells[0].innerText !== "Sr.No.") {
                  const year = cells[1].innerText.replace(/\n/g, "")
                  .replace(/\t/g, "")
                  .trim();;
                  const expenditure = cells[2].innerText.replace(/\n/g, "")
                  .replace(/\t/g, "")
                  .trim();;
                  const beneficiaries = cells[3].innerText
                    .replace(/\n/g, "")
                    .replace(/\t/g, "")
                    .trim();
                  stats.push({ year, expenditure, beneficiaries });
                }
              });
              details["Statistical Summary"] = stats;
            }
          });
          extractedData.push({ title, details });
        });

        return extractedData;
      }, selectors);

      data.forEach((item) => schemes.push({ ...item, id: uuidv4() }));

      const nextButton = await page.$(selectors.nextButton);
      if (nextButton) {
        // Click the next button
        await nextButton.click();
        // Wait for navigation to complete
        await page.waitForNavigation({ waitUntil: "networkidle2" });
      } else {
        hasNextPage = false;
      }
    }
  } catch (error) {
    console.error(`Error scraping data from ${url}:`, error);
  } finally {
    await page.close();
    await browser.close();
  }
  return schemes;
}


async function main() {
  try {
    const urls = await extractUrls();
    let allSchemes = [];
    const selectors = config.selectors;

    for (const url of urls) {
      console.log(`Scraping data from ${url}`);
      const urlSchemes = await scrapeData(url, selectors);
      allSchemes = allSchemes.concat(urlSchemes);
      console.log(`Scraped ${urlSchemes.length} schemes from ${url}`);
    }
    
    const targetDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..','scrapedData'))
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    const filepath = path.join(targetDir, "maharashtra.json");
    fs.writeFileSync(filepath, JSON.stringify(allSchemes, null, 2));
    console.log(`Data saved to ${filepath}`);
  } catch (error) {
    console.error("Error in main function:", error);
  }
}

main();
