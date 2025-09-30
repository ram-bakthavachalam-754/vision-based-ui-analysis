import type { NextApiRequest, NextApiResponse } from 'next';
import puppeteer from 'puppeteer-core';
import chromium from '@sparticuz/chromium-min';
import { OpenAI } from 'openai';

export const config = {
  api: {
    bodyParser: {
      sizeLimit: '10mb',
    },
    responseLimit: false,
  },
  maxDuration: 60,
};

type StatusCallback = (message: string) => void;

// Helper function to replace waitForTimeout
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Smart scrolling with status updates
async function intelligentScrollAndExpand(page: any, sendStatus: StatusCallback) {
  sendStatus('📜 Performing intelligent scrolling to reveal all content...');
  
  const initialHeight = await page.evaluate(() => document.body.scrollHeight);
  sendStatus(`📏 Initial page height: ${initialHeight}px`);
  
  await expandCollapsibleContent(page, sendStatus);
  await systematicPageScroll(page, sendStatus);
  await handleDynamicContentLoading(page, sendStatus);
  
  const finalHeight = await page.evaluate(() => document.body.scrollHeight);
  sendStatus(`📏 Final page height: ${finalHeight}px (expanded by ${finalHeight - initialHeight}px)`);
  
  await page.evaluate(() => window.scrollTo(0, 0));
  await delay(1000);
}

async function expandCollapsibleContent(page: any, sendStatus: StatusCallback) {
  sendStatus('🔍 Expanding collapsible content...');
  
  const expandableSelectors = [
    'button[aria-expanded="false"]',
    '.dropdown-toggle:not(.show)',
    '[data-toggle="dropdown"]',
    '.accordion-header',
    '.collapse:not(.show)',
    '[data-toggle="collapse"]',
    'button:has-text("Show more")',
    'button:has-text("Read more")',
    'button:has-text("View all")',
    'a:has-text("See all")',
    'button:has-text("More")',
    'a:has-text("More")',
  ];
  
  let expandedCount = 0;
  
  for (const selector of expandableSelectors) {
    try {
      const elements = await page.$$(selector);
      for (let i = 0; i < Math.min(elements.length, 10); i++) {
        try {
          const element = elements[i];
          const isVisible = await element.isIntersectingViewport();
          if (isVisible) {
            await element.click();
            await delay(800);
            expandedCount++;
          }
        } catch (error) {
          continue;
        }
      }
    } catch (error) {
      continue;
    }
  }
  
  sendStatus(`✅ Expanded ${expandedCount} collapsible elements`);
}

async function systematicPageScroll(page: any, sendStatus: StatusCallback) {
  sendStatus('📜 Starting systematic page scroll...');
  
  let pageHeight = await page.evaluate(() => document.body.scrollHeight);
  const viewportHeight = await page.evaluate(() => window.innerHeight);
  
  const scrollStep = Math.floor(viewportHeight * 0.7);
  let currentPosition = 0;
  let scrollCount = 0;
  let expansionCount = 0;
  const maxExpansions = 1; // Limit to 2 page expansions
  
  while (currentPosition < pageHeight) {
    await page.evaluate((pos: number) => window.scrollTo(0, pos), currentPosition);
    await delay(1200);
    scrollCount++;
    
    const newHeight = await page.evaluate(() => document.body.scrollHeight);
    if (newHeight > pageHeight) {
      expansionCount++;
      sendStatus(`📈 Page expanded by ${newHeight - pageHeight}px to ${newHeight}px (expansion ${expansionCount}/${maxExpansions})`);
      pageHeight = newHeight;
      
      // Stop if reached expansion limit
      if (expansionCount >= maxExpansions) {
        sendStatus(`⏹️ Reached expansion limit (${maxExpansions}), stopping scroll`);
        break;
      }
    }
    
    currentPosition += scrollStep;
    
    if (scrollCount > 50) {
      sendStatus('⚠️ Maximum scroll limit reached');
      break;
    }
  }
  
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await delay(2000);
  
  sendStatus(`✅ Systematic scroll complete: ${scrollCount} scrolls`);
}

async function handleDynamicContentLoading(page: any, sendStatus: StatusCallback) {
  sendStatus('🔄 Handling dynamic content loading...');
  
  const loadMoreSelectors = [
    'button:has-text("Load more")',
    'button:has-text("Show more")',
    'button:has-text("View more")',
    'a:has-text("Load more")',
    '.load-more-button',
    '.show-more-button',
    '.pagination-next',
  ];
  
  let totalClicks = 0;
  
  for (const selector of loadMoreSelectors) {
    try {
      const buttons = await page.$$(selector);
      for (let i = 0; i < Math.min(buttons.length, 5); i++) {
        try {
          const button = buttons[i];
          const isVisible = await button.isIntersectingViewport();
          if (isVisible) {
            await button.click();
            await delay(2500);
            totalClicks++;
          }
        } catch (error) {
          break;
        }
      }
    } catch (error) {
      continue;
    }
  }
  
  let previousHeight = await page.evaluate(() => document.body.scrollHeight);
  
  for (let i = 0; i < 1; i++) {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await delay(2000);
    
    const newHeight = await page.evaluate(() => document.body.scrollHeight);
    if (newHeight > previousHeight) {
      sendStatus(`📈 Infinite scroll detected: page grew by ${newHeight - previousHeight}px (attempt ${i + 1}/1)`);
      previousHeight = newHeight;
    } else {
      sendStatus(`⏹️ No more content loading after ${i + 1} scroll attempts`);
      break;
    }
  }
  
  sendStatus(`✅ Dynamic content loading complete: ${totalClicks} buttons clicked, infinite scroll limited to 1 attempt`);
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, error: 'Method not allowed' });
  }

  // Set up SSE
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache, no-transform');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');

  const sendStatus = (message: string) => {
    res.write(`data: ${JSON.stringify({ type: 'status', message })}\n\n`);
  };

  const sendError = (error: string) => {
    res.write(`data: ${JSON.stringify({ type: 'error', error })}\n\n`);
    res.end();
  };

  const sendComplete = (analysis: string, screenshot: string) => {
    res.write(`data: ${JSON.stringify({ type: 'complete', analysis, screenshot })}\n\n`);
    res.end();
  };

  const { url, prompt, apiKey } = req.body;

  if (!url || !prompt) {
    return sendError('URL and prompt are required');
  }

  if (!apiKey || !apiKey.startsWith('sk-')) {
    return sendError('Valid OpenAI API key is required');
  }

  try {
    new URL(url);
  } catch (error) {
    return sendError('Invalid URL format');
  }

  let browser = null;

  try {
    const openai = new OpenAI({ apiKey });

    sendStatus('🚀 Launching browser...');
    
    // Use @sparticuz/chromium-min optimized for serverless
    const isLocal = process.env.NODE_ENV === 'development';
    
    browser = await puppeteer.launch({
      args: isLocal 
        ? ['--no-sandbox']
        : [
            ...chromium.args,
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--single-process',
            '--disable-gpu',
          ],
      defaultViewport: chromium.defaultViewport,
      executablePath: isLocal
        ? process.platform === 'win32'
          ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
          : process.platform === 'darwin'
          ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
          : '/usr/bin/google-chrome'
        : await chromium.executablePath(
            'https://github.com/Sparticuz/chromium/releases/download/v131.0.0/chromium-v131.0.0-pack.tar'
          ),
      headless: chromium.headless,
    });

    const page = await browser.newPage();
    
    // Add stealth features to improve compatibility with websites
    // Note: Only use on websites you own or have permission to test
    const useStealthMode = true; // Set to false to disable
    
    if (useStealthMode) {
      // Set realistic user agent
      await page.setUserAgent(
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      );
      
      // Add extra headers to appear more like a real browser
      await page.setExtraHTTPHeaders({
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Upgrade-Insecure-Requests': '1',
      });
      
      // Add stealth scripts to avoid detection
      await page.evaluateOnNewDocument(() => {
      // Override the navigator.webdriver property
      Object.defineProperty(navigator, 'webdriver', {
        get: () => false,
      });
      
      // Override the plugins property
      Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
      });
      
      // Override the languages property
      Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
      });
      
      // Override the chrome property
      (window as any).chrome = {
        runtime: {},
      };
      
      // Override permissions
      const originalQuery = window.navigator.permissions.query;
      window.navigator.permissions.query = (parameters: any) => (
        parameters.name === 'notifications' ?
          Promise.resolve({ state: Intl.DateTimeFormat().resolvedOptions().timeZone } as any) :
          originalQuery(parameters)
      );
      });
    }
    
    await page.setViewport({ width: 1366, height: 768 });

    sendStatus(`🌐 Navigating to ${url}...`);
    
    try {
      await page.goto(url, { 
        waitUntil: 'networkidle0',
        timeout: 30000 
      });
    } catch (error: any) {
      // If networkidle0 times out, try with domcontentloaded
      if (error.message.includes('timeout') || error.message.includes('Navigation')) {
        sendStatus('⚠️ Page taking long to load, trying alternative method...');
        await page.goto(url, { 
          waitUntil: 'domcontentloaded',
          timeout: 30000 
        });
      } else {
        throw error;
      }
    }
    
    await delay(2000);

    await intelligentScrollAndExpand(page, sendStatus);

    sendStatus('📸 Capturing full-page screenshot...');
    await page.evaluate(() => window.scrollTo(0, 0));
    await delay(1000);
    
    const screenshotBuffer = await page.screenshot({ 
      fullPage: true,
      type: 'png',
      encoding: 'base64'
    }) as string;
    
    const screenshotBase64 = screenshotBuffer;
    sendStatus(`📸 Screenshot captured (${screenshotBase64.length} chars)`);

    sendStatus('🤖 Analyzing page with AI...');
    const response = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text: `Analyze this webpage screenshot and respond to the following instruction:\n\n${prompt}\n\nIMPORTANT: This is a FULL-PAGE screenshot showing ALL content on the page, including content that was below the fold. The page was systematically scrolled and all collapsible content was expanded before taking this screenshot. Please analyze the ENTIRE image carefully from top to bottom.`
            },
            {
              type: 'image_url',
              image_url: {
                url: `data:image/png;base64,${screenshotBase64}`
              }
            }
          ]
        }
      ],
      max_tokens: 2000,
      temperature: 0.1
    });

    const analysis = response.choices[0]?.message?.content || 'No analysis provided';
    sendStatus('✅ Analysis complete');

    await browser.close();

    sendComplete(analysis, `data:image/png;base64,${screenshotBase64}`);

  } catch (error: any) {
    if (browser) {
      try {
        await browser.close();
      } catch (closeError) {
        // Ignore
      }
    }
    sendError(error.message || 'An error occurred during verification');
  }
}
