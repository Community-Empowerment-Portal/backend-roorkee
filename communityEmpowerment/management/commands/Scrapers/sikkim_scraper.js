const puppeteer = require('puppeteer')
const { v4: uuidv4 } = require('uuid');
const fs = require('fs')

async function paginationLinks(){
    const browser = await puppeteer.launch()
    const page = await browser.newPage()
    await page.goto('https://sikkim.gov.in/scheme/schemes');
    const result = await page.evaluate(()=>{
        const schemeLinks = []
        const schemeNodes = document.querySelectorAll(".corner-cut")
        schemeNodes.forEach((scheme)=>{
            const schemeUrl = scheme.querySelector("ul")
            const lastLi = schemeUrl.querySelector("li:last-child");
            const anchorTag = lastLi.querySelector("a");
            const href = anchorTag ? anchorTag.href : null;
            schemeLinks.push(href)
        })
        return schemeLinks
        

    })
    browser.close()
    return result
}

async function scrapeSikkim(){
    const schemeUrls = await paginationLinks()
    const schemes = []
    for (const url of schemeUrls){
        const browser = await puppeteer.launch()
        const page = await browser.newPage()
        const uniqueId = uuidv4();
        await page.goto(url,{
            waitUntil: 'networkidle0',
          });
        const result = await page.evaluate((url, uniqueId)=>{
            const schemeTitle = document.querySelector('.card-body :nth-child(1) h3').textContent
            const schemeDepartment = document.querySelector('.card-body :nth-child(1) h4').textContent
            const schemeDescription = document.querySelector('.card-body :nth-child(4) :nth-child(2)').textContent
            const schemeData = {
                id: uniqueId,
                title: schemeTitle.trim().replace(/[\t\n\r]+/g, ''),
                department: schemeDepartment.trim().replace(/[\t\n\r]+/g, ''),
                description: schemeDescription.trim().replace(/[\t\n\r]+/g, ''),
                schemeUrl: url
            }
            

            return schemeData
        }, url, uniqueId)
        await browser.close()
        schemes.push(result)

    }
    
    const targetDir = path.join(__dirname, '..','..','scrapedData');
    const filePath = path.join(targetDir, 'sikkim.json');
    fs.writeFileSync(filePath, JSON.stringify(schemes, null, 2), 'utf-8');

    console.log('Data has been saved to sikkimSchemes.json');
}

scrapeSikkim()