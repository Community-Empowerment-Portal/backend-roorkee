const puppeteer = require('puppeteer')
const fs = require('fs')
async function odishaSchemeUrls(){
    console.log("stared")
    const browser = await puppeteer.launch()
    const page = await browser.newPage()
    await page.goto('https://rd.odisha.gov.in/scheme')
    console.log("stared 2")
    const result = await page.evaluate(()=>{
        const schemeList = document.querySelectorAll('.views-field-name')
        const schemeUrls = []
        schemeList.forEach((scheme)=>{
            
            const urlofScheme = scheme.querySelector('a').href
            schemeUrls.push(urlofScheme)
            
        })
    
    return schemeUrls
    })
    await browser.close()
    return result
    
}

async function main(){
    const schemes = []
    const schemeUrlList = await odishaSchemeUrls()
    for (const schemeLink of schemeUrlList){
        const browser = await puppeteer.launch()
        const page = await browser.newPage()
        await page.goto(schemeLink)
        const result = await page.evaluate((schemeLink)=>{
            let title = document.querySelector('.block-page-title-block h1 div')
            let description = document.querySelector('.views-field-body div :last-child')
            if (title){
                title = title.textContent
            }
            if (description){
                description = description.textContent
            }
            // const description = document.querySelector('.field-content :nth-child(2)').textContent
            const schemeData = {
                title: title,
                description: description,
                schemeUrl: schemeLink
            }
        return schemeData
        },schemeLink)
    schemes.push(result)
    await browser.close()
    }

    console.log(schemes)
    const targetDir = path.join(__dirname, '..','..','scrapedData');
    const filePath = path.join(targetDir, 'odisha.json');
    fs.writeFileSync(filePath, JSON.stringify(schemes, null, 2), 'utf-8');

    console.log('Data has been saved to odishaSchemes.json');
}

main()
