# Vision-Based Testing - AI-Powered Web Page Verification

A powerful web application that uses AI vision to analyze web pages. Built with Next.js and deployable to Vercel.

## ⚠️ Important Legal Notice

**For Educational and Personal Use Only**

This tool is intended for:
- ✅ Testing and analyzing websites you own or have permission to access
- ✅ Personal research and educational purposes
- ✅ Legitimate accessibility testing

**You are responsible for:**
- ❌ Respecting robots.txt and website Terms of Service
- ❌ Not using this for scraping, data harvesting, or unauthorized access
- ❌ Not overwhelming servers with excessive requests
- ❌ Not bypassing paywalls, authentication, or access controls

**By using this tool, you agree to use it responsibly and legally. The authors are not responsible for misuse.**

## ✨ Perfect for Public Deployment

This app uses a **"Bring Your Own API Key" (BYOK)** model - users provide their own OpenAI API keys, so you can deploy it publicly at **zero cost** for OpenAI usage!

## Features

- 🔑 **User-Provided API Keys**: Users bring their own OpenAI keys (never stored on server)
- 🔍 **Smart URL Analysis**: Enter any URL and get AI-powered analysis
- 📸 **Full-Page Screenshots**: Captures entire page content, not just visible area
- 🤖 **AI-Powered Verification**: Uses OpenAI GPT-4 Vision to analyze page content
- 📜 **Intelligent Scrolling**: Automatically scrolls through entire page and expands collapsible content
- 🚀 **Vercel-Ready**: Optimized for serverless deployment on Vercel
- 💰 **Zero Cost Hosting**: Users pay for their own OpenAI usage

## Technology Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: Next.js API Routes, Puppeteer (serverless-optimized)
- **AI**: OpenAI GPT-4 Vision API
- **Deployment**: Vercel

## Setup Instructions

### Prerequisites

- Node.js 18+ installed
- Vercel account (for deployment)

**Note**: You DON'T need an OpenAI API key for deployment! Users will provide their own keys.

### Local Development

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **No environment setup needed!**
   - The app uses user-provided API keys
   - No `.env` file required for deployment
   - For testing locally, you'll enter your API key in the UI

3. **Run the development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Deploy to Vercel (Public Deployment)

### Option 1: Deploy via Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Deploy**:
   ```bash
   vercel
   ```

3. **Deploy to production**:
   ```bash
   vercel --prod
   ```

**That's it!** No environment variables needed. Users will provide their own API keys.

### Option 2: Deploy via Vercel Dashboard

1. **Push to GitHub**:
   - Create a new repository on GitHub
   - Push your code:
     ```bash
     git init
     git add .
     git commit -m "Initial commit"
     git remote add origin <your-repo-url>
     git push -u origin main
     ```

2. **Import to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repository
   - **No environment variables needed!**
   - Click "Deploy"

3. **Done!** Your app will be live at `https://your-project.vercel.app`

### Share with Users

Your users will need to:
1. Get their own OpenAI API key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Enter it in the app's API Key field
3. Optionally save it in their browser for convenience

## Usage

1. Enter your OpenAI API key (get one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys))
2. Optionally check "Remember my API key" to save it in your browser
3. Enter a website URL (e.g., `https://example.com`)
4. Enter a verification prompt (e.g., "Check if the page has a contact form and describe its fields")
5. Click "Verify Page"
6. Wait for the AI to analyze the page
7. View the analysis and full-page screenshot

**Cost**: Each analysis costs approximately $0.02-0.05, charged to your OpenAI account.

## Features Explained

### Smart Scrolling

The app automatically:
- Scrolls through the entire page systematically
- Expands collapsible content (accordions, dropdowns, "show more" buttons)
- Handles infinite scroll and lazy-loaded content
- Clicks "Load More" buttons automatically
- Captures full-page screenshot after content is fully loaded

### AI Analysis

Uses OpenAI's GPT-4 Vision model to:
- Analyze the full-page screenshot
- Understand page layout and content
- Answer specific questions about the page
- Verify presence of elements
- Extract structured information

## Configuration

### Timeout Settings

For Vercel Pro plans, you can increase the function timeout in `vercel.json`:

```json
{
  "functions": {
    "pages/api/**/*.ts": {
      "maxDuration": 60
    }
  }
}
```

Free tier has a 10-second limit; Pro tier allows up to 60 seconds.

### Screenshot Quality

Adjust screenshot settings in `pages/api/verify.ts`:

```typescript
const screenshotBuffer = await page.screenshot({ 
  fullPage: true,
  type: 'png',
  quality: 90 // for jpeg type
});
```

## Troubleshooting

### "Function timeout" errors

- Increase `maxDuration` in `vercel.json` (requires Vercel Pro)
- Reduce the number of scroll iterations in the API route
- Test with simpler pages first

### "Browser launch failed"

- Check that `chrome-aws-lambda` is properly installed
- Verify Vercel is using the correct Node.js version (18+)

### High API costs

- The app uses GPT-4 Vision which has token costs for images
- Consider implementing caching for repeated analyses
- Add rate limiting if deploying publicly

## License

MIT

## Credits

Inspired by the Playwright-based `class_schedule_extractor.py` script, adapted for serverless deployment with Puppeteer.
