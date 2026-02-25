const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto('https://oag.parliament.nz');
    console.log('Page title:', await page.title());
    await browser.close();
})();
