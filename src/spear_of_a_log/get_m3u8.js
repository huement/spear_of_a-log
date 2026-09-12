const puppeteer = require('puppeteer');

(async () => {
  const url = process.argv[2];
  if (!url) process.exit(1);

  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  let m3u8Url = null;

  page.on('request', request => {
    const reqUrl = request.url();
    if (reqUrl.includes('.m3u8') && !m3u8Url) {
      m3u8Url = reqUrl;
    }
  });

  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
  } catch (e) {}

  await browser.close();

  if (m3u8Url) {
    console.log(m3u8Url);
  } else {
    process.exit(1);
  }
})();
