#!/usr/bin/env node
/**
 * AI Daily Pulse - Puppeteer 辅助抓取脚本
 * 用法: node fetch_with_browser.js <url> [selector]
 * 输出: JSON { success: bool, content: string, title: string }
 */

const puppeteer = require('puppeteer');

async function fetchPage(url, selector = 'body') {
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-extensions',
        '--disable-background-timer-throttling',
      ],
      timeout: 30000,
    });

    const page = await browser.newPage();

    // 设置 User-Agent
    await page.setUserAgent(
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );

    // 设置视口
    await page.setViewport({ width: 1280, height: 800 });

    // 拦截不需要的资源
    await page.setRequestInterception(true);
    page.on('request', (req) => {
      const type = req.resourceType();
      if (['image', 'media', 'font', 'stylesheet'].includes(type)) {
        req.abort();
      } else {
        req.continue();
      }
    });

    // 导航
    await page.goto(url, {
      waitUntil: 'networkidle2',
      timeout: 45000,
    });

    // 等待选择器
    try {
      await page.waitForSelector(selector, { timeout: 10000 });
    } catch (e) {
      // 选择器未找到，继续用 body
    }

    // 获取内容
    const content = await page.evaluate((sel) => {
      const el = document.querySelector(sel) || document.body;
      return el.innerHTML;
    }, selector);

    const title = await page.title();

    const result = {
      success: true,
      content: content,
      title: title,
      url: url,
    };

    console.log(JSON.stringify(result));
  } catch (error) {
    const result = {
      success: false,
      content: '',
      title: '',
      url: url,
      error: error.message,
    };
    console.log(JSON.stringify(result));
    process.exitCode = 1;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// 入口
const args = process.argv.slice(2);
if (args.length < 1) {
  console.error('Usage: node fetch_with_browser.js <url> [selector]');
  process.exit(1);
}

const url = args[0];
const selector = args[1] || 'body';

fetchPage(url, selector);
