const puppeteer = require('puppeteer')
const { v4: uuidv4 } = require('uuid');
const fs = require('fs')

async function scrapeSchemeUrls(){
    const browser = await puppeteer.launch()
    const page = await browser.newPage()
    await page.goto('https://ukrdd.uk.gov.in/?page_id=4136')
    const result = await page.evaluate(()=>{
        const title = document.querySelectorAll('.genList')
        const urlList = []
        title.forEach((url)=>{
            const schemeUrlNode = url.querySelectorAll('li')
            schemeUrlNode.forEach((nodeurl)=>{
                const schemeUrl = nodeurl.querySelector('a').href
                urlList.push(schemeUrl)
            })
            
        })
        return urlList
    })
    await browser.close()
    return result
}


async function scrapeSchemeData(){
    const browser = await puppeteer.launch({
        args: ['--ignore-certificate-errors'],
      })
    const page = await browser.newPage()
    const schemeUrls = await scrapeSchemeUrls()
    const schemes = []
    for (const schemeurl of schemeUrls){
        const uniqueId = uuidv4();
        await page.goto(schemeurl);
        const result = await page.evaluate((schemeurl, uniqueId)=>{
            const title = document.querySelector('.section-main-title')?.textContent || 'Not available';
            const description = document.querySelector('.el_text p')?.textContent || 'Not available';
            const objective = []
            const objectivesNode = document.querySelectorAll('.el_text ul li')
            objectivesNode.forEach((node)=>{
                objective.push(node.textContent)
            })
            const schemeData = {
                id: uniqueId,
                title: title,
                description: description,
                objectives: objective,
                schemeUrl: schemeurl
            }

            return schemeData
        },schemeurl, uniqueId)
        await browser.close()
        schemes.push(result)
        
    }
    const targetDir = path.join(__dirname, '..','..','scrapedData');
    const filePath = path.join(targetDir, 'uttarakhand.json');
    fs.writeFileSync(filePath, JSON.stringify(schemes, null, 2), 'utf-8');

    console.log('Data has been saved to uttarakhandSchemes.json');
}

scrapeSchemeData()