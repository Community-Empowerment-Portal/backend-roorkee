const puppeteer = require('puppeteer')
const { v4: uuidv4 } = require('uuid');
const fs = require('fs')

async function scrapeDelhiSchemeUrls(){
    const browser = await  puppeteer.launch()
    const page = await browser.newPage()
    await page.goto('https://dmnewdelhi.delhi.gov.in/schemes/')
    const result = await page.evaluate(()=>{
        const schemeUrlListNode = document.querySelectorAll('.eventItem')
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

async function scrapeDelhiSchemes(){
    const schemeUrls = await scrapeDelhiSchemeUrls()
    const browser = await puppeteer.launch()
    const page = await browser.newPage()
    const schemes = []
    for (const url of schemeUrls){
        await page.goto(url)
        const result = await page.evaluate((url)=>{
            const title = document.querySelector('.col-9 div div h1').textContent
            const description = document.querySelector('.col-9 div :nth-child(2) p').textContent
            const benefitNodes = document.querySelectorAll('.col-9 div :nth-child(2) :nth-child(7) li')
            const benefits = []
            benefitNodes.forEach((node)=>{
                benefits.push(node.textContent)
            })
            return {title, description, benefits, schemeUrl: url}
        }, url)
        schemes.push({...result, id: uuidv4()})
    }
    await browser.close()
    console.log(schemes)
    return schemes
    
}

async function main(){
    const schemes = await scrapeDelhiSchemes()
    const targetDir = path.join(__dirname, '..','..','scrapedData');
    const filePath = path.join(targetDir, 'delhi.json');
    fs.writeFileSync(filePath, JSON.stringify(schemes, null, 2), 'utf-8');
    console.log('Data has been saved to delhiSchemes.json');
}

main()

