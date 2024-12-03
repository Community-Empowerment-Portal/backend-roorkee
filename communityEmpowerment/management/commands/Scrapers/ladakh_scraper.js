const puppeteer = require('puppeteer')
const { v4: uuidv4 } = require('uuid');
const fs = require('fs')

async function scrapeladakhSchemeUrls(){
    const browser = await  puppeteer.launch()
    const page = await browser.newPage()
    await page.goto('https://ladakh.gov.in/schemes-programmes/')
    const result = await page.evaluate(()=>{
        const schemeUrlListNode = document.querySelectorAll('.eventContent')
        const schemeUrlList = []
        schemeUrlListNode.forEach((node)=>{
            schemeUrlList.push(node.querySelector('a').href)
        })
        return schemeUrlList
    })
    console.log(result)
    await browser.close()
    return result
    
}

async function scrapeladakhSchemes(){
    const schemeUrls = await scrapeladakhSchemeUrls()
    const browser = await puppeteer.launch()
    const page = await browser.newPage()
    const schemes = []
    for (const url of schemeUrls){
        await page.goto(url)
        const result = await page.evaluate((url)=>{
            const title = document.querySelector('.col-xs-12 h1').textContent
            const description = document.querySelector('.col-lg-12 p').textContent
            
            return {title, description, schemeUrl: url}
        }, url)
        schemes.push({...result, id: uuidv4()})
    }
    await browser.close()
    console.log(schemes)
    return schemes
    
}

async function main(){
    const schemes = await scrapeladakhSchemes()
    const targetDir = path.join(__dirname, '..','..','scrapedData');
    const filePath = path.join(targetDir, 'ladakh.json');
    fs.writeFileSync(filePath, JSON.stringify(schemes, null, 2), 'utf-8');
    console.log('Data has been saved to ladakhSchemes.json');
}

main()