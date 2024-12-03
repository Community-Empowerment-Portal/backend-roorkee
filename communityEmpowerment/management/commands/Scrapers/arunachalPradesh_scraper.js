const puppeteer = require('puppeteer')
const { v4: uuidv4 } = require('uuid');
const fs = require('fs')

async function scrapeArunachalSchemeUrls(){
    const browser = await puppeteer.launch()
    const page = await browser.newPage()
    await page.goto('https://arunachalipr.gov.in/index.php/schemes/')
    const result = await page.evaluate(()=>{
        const urlNodeList = document.querySelectorAll('.elementor-3324')
        const schemeUrls = []
        urlNodeList.forEach((node)=>{
            const schemeUrl = node.querySelector('a').href
            schemeUrls.push(schemeUrl)

        })
        return schemeUrls
    })
    await browser.close()
    return result
    
}


async function scrapeArunachalSchemeDeatils(){
    const browser = await puppeteer.launch()
    const page = await browser.newPage()
    const schemeUrls = await scrapeArunachalSchemeUrls()
    console.log("ye scheme urls",schemeUrls)
    const schemes = []
    for (const url of schemeUrls){
        await page.goto(url)
        const result = await page.evaluate((url)=>{
            const title = document.querySelector('.elementor-element-2a80e346 h1').textContent
            const objectiveNode = document.querySelector('.elementor-element-30d68263 p')

            const textNodes = Array.from(objectiveNode.childNodes)
            .filter(node => node.nodeType === Node.TEXT_NODE)
            .map(node => node.nodeValue.trim());

            const objective =  textNodes.join(' ');

            const benefitsNode = document.querySelector('.elementor-element-30d68263 div ul')
            const benefitsNodes = benefitsNode.querySelectorAll('li')
            const benefits = []
            benefitsNodes.forEach((benefit)=>{
                benefits.push(benefit.textContent)
            })

            const criteriaNodes = document.querySelectorAll('.elementor-element-30d68263 div ul')
            const criteriaNode = criteriaNodes[1]
            const criteriaListNodes = criteriaNode.querySelectorAll('li')
            const criteria = []
            criteriaListNodes.forEach((node)=>{
                criteria.push(node.textContent)
            })

            const documentsNodes = document.querySelectorAll('.elementor-element-30d68263 div ul')
            const documentsNode = documentsNodes[2]
            const documentsListNodes = documentsNode.querySelectorAll('li')
            const documents = []
            documentsListNodes.forEach((node)=>{
                documents.push(node.textContent)
            })

            return {title, objective, benefits, criteria, documents, schemeUrl: url}
        }, url)
        const updatedScheme = {...result,id: uuidv4()}
        schemes.push(updatedScheme)
        console.log(result)
    }
    await browser.close()
    const targetDir = path.join(__dirname, '..','..','scrapedData');
    const filePath = path.join(targetDir, 'arunachalPradesh.json');
    fs.writeFileSync(filePath, JSON.stringify(schemes, null, 2), 'utf-8');

    console.log('Data has been saved to arunachalPradeshSchemes.json');

}

scrapeArunachalSchemeDeatils()