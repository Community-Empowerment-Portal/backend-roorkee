const puppeteer = require('puppeteer')
const { v4: uuidv4 } = require('uuid');
const fs = require('fs')

async function scrapeTelangana(){
    const browser = await puppeteer.launch()
    const page = await browser.newPage()
    await page.goto('https://www.telangana.gov.in/government-initiatives/')
    const uniqueId1 = uuidv4();
    const uniqueId2 = uuidv4();
    const result = await page.evaluate((uniqueId1, uniqueId2)=>{
        const title1 = document.querySelector('.tsportal-page h4').textContent
        const description1 = document.querySelector('.tsportal-page :nth-child(3)').textContent
        const benefit1 = document.querySelector('.tsportal-page :nth-child(4)').textContent
        const title2 = document.querySelector('.tsportal-page :nth-child(6)').textContent
        const description2 = document.querySelector('.tsportal-page :nth-child(7)').textContent
        const scheme1 = {
            id: uniqueId1,
            title: title1,
            description: description1,
            benefits: benefit1,
            schemeUrl: 'https://www.telangana.gov.in/government-initiatives/'
        }
        const scheme2 = {
            id: uniqueId2,
            title: title2,
            description: description2,
            schemeUrl: 'https://www.telangana.gov.in/government-initiatives/'
        }
        return [scheme1, scheme2]
        
    }, uniqueId1, uniqueId2)
    await browser.close()
    const targetDir = path.join(__dirname, '..','..','scrapedData');
    const filePath = path.join(targetDir, 'telangana.json');
    fs.writeFileSync(filePath, JSON.stringify(result, null, 2), 'utf-8');

    console.log('Data has been saved to telanganaSchemes.json');
}

scrapeTelangana()