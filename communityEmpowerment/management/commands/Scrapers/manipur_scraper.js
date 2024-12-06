const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  const urls = [
    'https://ukhrul.nic.in/scheme/district-disability-rehabilitation-centre/',
    'https://ukhrul.nic.in/scheme/manipur-old-age-pension-scheme/',
    'https://ukhrul.nic.in/scheme/pradhan-mantri-matru-vandana-yojana-pmmvy/',
    'https://ukhrul.nic.in/scheme/prevention-of-alcoholism-substance-drugs-abuse/',
    'https://ukhrul.nic.in/scheme/composite-regional-centre-crc/',
    'https://ukhrul.nic.in/scheme/bal-bhavan/',
    'https://ukhrul.nic.in/scheme/mahila-shakti-kendra/',
    'https://ukhrul.nic.in/scheme/rajiv-gandhi-national-creche-schemes/',
    'https://ukhrul.nic.in/scheme/child-protection-servicescps-scheme-mission-vatsalya/',
    'https://ukhrul.nic.in/scheme/national-social-assistance-programmensap/',
    'https://ukhrul.nic.in/scheme/indira-gandhi-national-disable-pension-scheme-igndps/',
    'https://ukhrul.nic.in/scheme/grant-in-aid-ngos-disabled-handicapped/',
    'https://ukhrul.nic.in/scheme/indira-gandhi-national-widow-pension-scheme-ignwps/',
    'https://ukhrul.nic.in/scheme/i-indira-gandhi-national-old-age-pension-scheme-ignoaps/',
    // Add more URLs here if needed
  ];

  const scrapeData = async (page, url) => {
    await page.goto(url, { waitUntil: 'networkidle2' });

    const data = await page.evaluate((url) => {
      const schemes = [];
      document.querySelectorAll('.scheme').forEach((schemeElement) => {
        const title = schemeElement.querySelector('h1')?.innerText.trim() || '';
        var date = schemeElement.querySelector('.schemeMeta strong')?.nextSibling?.nodeValue.trim() || '';
        date = date.replace(' -  |', '').trim();

        const beneficiary = schemeElement.querySelector('h2.heading4 + p')?.innerText.trim() || '';
        const benefits = schemeElement.querySelector('h2.heading4:nth-of-type(2) + p')?.innerText.trim() || '';
        const howToApply = schemeElement.querySelector('h3 + p')?.innerText.trim() || '';

        schemes.push({ title, date, beneficiary, benefits, howToApply, schemeUrl: url });
      });
      return schemes;
    },url);

    return data;
  };

  const browser = await puppeteer.launch({ headless: false }); // Set headless to false for debugging
  const page = await browser.newPage();

  let allSchemes = [];
  for (const url of urls) {
    const schemes = await scrapeData(page, url);
    allSchemes = allSchemes.concat(schemes);
  }

  await browser.close();
  const targetDir = path.join(__dirname, '..','..','scrapedData');
  const filePath = path.join(targetDir, 'manipur.json');
  fs.writeFileSync(filePath, JSON.stringify(allSchemes, null, 2), 'utf-8');

  console.log('Data saved to manipur.json');
})();
