const puppeteer = require('puppeteer')
const fs = require('fs').promises
async function extract_title_and_pdfUrl(){
    const url = "https://www.goa.gov.in/government/schemes/"
    const browser = await puppeteer.launch()
    const page =  await browser.newPage()
    await page.goto(url, { timeout: 60000 })
    
    const result = await page.evaluate(()=>{
        let data = []

        document.querySelectorAll('.vc_col-md-12.nopad-left.document_holder').forEach((it)=>{
            title = it.children[0].textContent.trim()
            dateText = it.children[1].textContent.split(":")
            publishDate = dateText[dateText.length-1].trim()
            pdf_link = it.children[3].children[1].querySelector(`a`).href
            data.push({
                title, publishDate, pdf_link
            })
        })
        return data
    })
    const targetDir = path.join(__dirname, '..','..','scrapedData', 'scrapedPdfs');
const filePath = path.join(targetDir, 'goadPdf.json');
    await fs.writeFile(filePath, JSON.stringify(result, null, 2), 'utf-8')
    await browser.close()
}
extract_title_and_pdfUrl()