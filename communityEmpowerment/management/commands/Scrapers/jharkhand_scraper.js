const puppeteer = require('puppeteer')
const {v4: uuidv4} = require('uuid')
const fs = require('fs').promises


const getAllUrls = async function(){
    const url = "https://jharkhand.gov.in/Home/SearchSchemes"
    const browser = await puppeteer.launch()
    const page = await browser.newPage()
    await  page.goto(url , {timeout:60000})

    const values = await page.evaluate(() => {
        const options = Array.from(document.querySelector('select').children); 
        return options.map(option => {
            return {
                value: option.value,
                departmentName: option.innerText.trim() 
            };
        });
    });

    await browser.close()
    return values 
}


async function main() {
    const allResults = []
    const values = await getAllUrls()
    await Promise.all(values.map(async (item) => {
        const res = await get_pdf_link(`https://jharkhand.gov.in/Home/SearchSchemes?department=${item.value}`, item.departmentName)
        allResults.push(...res)
    }))
    const targetDir = path.join(__dirname, '..','..','scrapedData');
    const filePath = path.join(targetDir, 'jharkhandpdf.json');
    await fs.writeFile(filePath, JSON.stringify(allResults, null, 2))
}
main()
async function get_pdf_link(url, departmentName) {
    const browser = await puppeteer.launch()
    const page = await browser.newPage()
    await  page.goto(url , {timeout:60000})
    const result = await page.evaluate(()=>{
        const rows = document.querySelectorAll('tbody tr')
        const data = []
        rows.forEach((row, index)=>{
            if(index === 0) return;
            const title = row.children[1].innerText.trim()
            const publishDate = row.children[5].innerText.trim()
            const pdfUrl = row.children[6].children[0].href
            data.push({title,publishDate, pdfUrl})
        })
        return data 
    })

    const resultWithUUID = result.map((item)=>({id:uuidv4(), ...item, departmentName}))

    await browser.close()
    return resultWithUUID

}




