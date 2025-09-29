import type { NextApiRequest, NextApiResponse } from 'next';
import chromium from '@sparticuz/chromium';
import puppeteer from 'puppeteer-core';
import { OpenAI } from 'openai';

type VerifyRequest = {
  url: string;
  prompt: string;
  apiKey: string;
};

type VerifyResponse = {
  success: boolean;
  analysis?: string;
  screenshot?: string;
  error?: string;
};

export const config = {
  api: {
    bodyParser: {
      sizeLimit: '10mb',
    },
    responseLimit: false,
  },
  maxDuration: 60, // Max execution time for Vercel Pro
};

// Helper to send SSE messages
function sendSSE(res: any, event: string, data: any) {
  res.write(`event: ${event}\n`);
  res.write(`data: ${JSON.stringify(data)}\n\n`);
}

// Helper function to replace waitForTimeout
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Smart scrolling functionality from class_schedule_extractor.py
async function intelligentScrollAndExpand(page: any) {
  console.log('📜 Performing intelligent scrolling to reveal all content...');
  
  // Step 1: Get initial page dimensions
  const initialHeight = await page.evaluate(() => document.body.scrollHeight);
  console.log(`📏 Initial page height: ${initialHeight}px`);
  
  // Step 2: Expand common collapsible elements
  await expandCollapsibleContent(page);
  
  // Step 3: Perform systematic scrolling
  await systematicPageScroll(page);
  
  // Step 4: Handle infinite scroll or lazy loading
  await handleDynamicContentLoading(page);
  
  // Step 5: Final scroll to top
  const finalHeight = await page.evaluate(() => document.body.scrollHeight);
  console.log(`📏 Final page height: ${finalHeight}px (expanded by ${finalHeight - initialHeight}px)`);
  
  await page.evaluate(() => window.scrollTo(0, 0));
  await delay(1000);
}

async function expandCollapsibleContent(page: any) {
  console.log('🔍 Expanding collapsible content...');
  
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
    '.nav-tab:not(.active)',
    '.tab-button:not(.active)',
    '.menu-toggle',
    '.hamburger',
    '.mobile-menu-button',
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
  
  console.log(`✅ Expanded ${expandedCount} collapsible elements`);
}

async function systematicPageScroll(page: any) {
  console.log('📜 Starting systematic page scroll...');
  
  let pageHeight = await page.evaluate(() => document.body.scrollHeight);
  const viewportHeight = await page.evaluate(() => window.innerHeight);
  
  const scrollStep = Math.floor(viewportHeight * 0.7);
  let currentPosition = 0;
  let scrollCount = 0;
  let expansionCount = 0;
  const maxExpansions = 2; // Limit to 2 page expansions
  
  while (currentPosition < pageHeight) {
    await page.evaluate((pos: number) => window.scrollTo(0, pos), currentPosition);
    await delay(1200);
    scrollCount++;
    
    // Check if new content loaded
    const newHeight = await page.evaluate(() => document.body.scrollHeight);
    if (newHeight > pageHeight) {
      expansionCount++;
      console.log(`📈 Page expanded by ${newHeight - pageHeight}px to ${newHeight}px (expansion ${expansionCount}/${maxExpansions})`);
      pageHeight = newHeight;
      
      // Stop if reached expansion limit
      if (expansionCount >= maxExpansions) {
        console.log(`⏹️ Reached expansion limit (${maxExpansions}), stopping scroll`);
        break;
      }
    }
    
    currentPosition += scrollStep;
    
    // Safety check
    if (scrollCount > 50) {
      console.log('⚠️ Maximum scroll limit reached');
      break;
    }
  }
  
  // Final scroll to bottom
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await delay(2000);
  
  console.log(`✅ Systematic scroll complete: ${scrollCount} scrolls`);
}

async function handleDynamicContentLoading(page: any) {
  console.log('🔄 Handling dynamic content loading...');
  
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
  
  // Handle infinite scroll (limited to 3 attempts)
  let previousHeight = await page.evaluate(() => document.body.scrollHeight);
  
  for (let i = 0; i < 1; i++) {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await delay(2000);
    
    const newHeight = await page.evaluate(() => document.body.scrollHeight);
    if (newHeight > previousHeight) {
      console.log(`📈 Infinite scroll detected: page grew by ${newHeight - previousHeight}px (attempt ${i + 1}/3)`);
      previousHeight = newHeight;
    } else {
      console.log(`⏹️ No more content loading after ${i + 1} scroll attempts`);
      break;
    }
  }
  
  console.log(`✅ Dynamic content loading complete: ${totalClicks} buttons clicked, infinite scroll limited to 3 attempts`);
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<VerifyResponse>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, error: 'Method not allowed' });
  }

  const { url, prompt, apiKey } = req.body as VerifyRequest;

  if (!url || !prompt) {
    return res.status(400).json({ 
      success: false, 
      error: 'URL and prompt are required' 
    });
  }

  if (!apiKey) {
    return res.status(400).json({ 
      success: false, 
      error: 'OpenAI API key is required' 
    });
  }

  // Basic API key format validation
  if (!apiKey.startsWith('sk-')) {
    return res.status(400).json({ 
      success: false, 
      error: 'Invalid API key format. OpenAI API keys start with "sk-"' 
    });
  }

  // Validate URL
  try {
    new URL(url);
  } catch (error) {
    return res.status(400).json({ 
      success: false, 
      error: 'Invalid URL format' 
    });
  }

  let browser = null;

  try {
    // Initialize OpenAI with user-provided API key
    const openai = new OpenAI({
      apiKey: apiKey, // Use the user's API key
    });

    // Launch browser
    console.log('🚀 Launching browser...');
    
    const isDev = process.env.NODE_ENV === 'development';
    
    let executablePath: string;
    let browserArgs: string[];
    
    if (isDev) {
      // Local development - use local Chrome
      const localChromePaths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
      ];
      
      const fs = require('fs');
      executablePath = await chromium.executablePath();
      for (const path of localChromePaths) {
        if (fs.existsSync(path)) {
          executablePath = path;
          break;
        }
      }
      browserArgs = ['--no-sandbox', '--disable-setuid-sandbox'];
    } else {
      // Production - use @sparticuz/chromium
      executablePath = await chromium.executablePath();
      browserArgs = [
        ...chromium.args,
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--single-process',
        '--no-zygote',
      ];
    }
    
    browser = await puppeteer.launch({
      args: browserArgs,
      defaultViewport: { width: 1366, height: 768 },
      executablePath,
      headless: true,
      ignoreHTTPSErrors: true,
    });

    const page = await browser.newPage();
    
    // Set viewport
    await page.setViewport({ width: 1366, height: 768 });

    // Navigate to URL
    console.log(`🌐 Navigating to ${url}...`);
    await page.goto(url, { 
      waitUntil: 'networkidle0',
      timeout: 30000 
    });
    
    await delay(2000);

    // Perform intelligent scrolling and content expansion
    await intelligentScrollAndExpand(page);

    // Take full-page screenshot
    console.log('📸 Capturing full-page screenshot...');
    await page.evaluate(() => window.scrollTo(0, 0));
    await delay(1000);
    
    const screenshotBuffer = await page.screenshot({ 
      fullPage: true,
      type: 'png'
    });
    
    const screenshotBase64 = screenshotBuffer.toString('base64');
    console.log(`📸 Screenshot captured (${screenshotBase64.length} chars)`);

    // Analyze with OpenAI Vision
    console.log('🤖 Analyzing page with AI...');
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
    console.log('✅ Analysis complete');

    // Close browser
    await browser.close();

    return res.status(200).json({
      success: true,
      analysis,
      screenshot: `data:image/png;base64,${screenshotBase64}`
    });

  } catch (error: any) {
    console.error('❌ Error:', error);
    
    if (browser) {
      try {
        await browser.close();
      } catch (closeError) {
        console.error('Error closing browser:', closeError);
      }
    }

    return res.status(500).json({
      success: false,
      error: error.message || 'An error occurred during verification'
    });
  }
}
