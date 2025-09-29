# Quick Start Guide

Get your Vision-Based Testing app running in 5 minutes!

## 1. Install Dependencies

```bash
npm install
```

## 2. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Don't have an OpenAI API key?** Get one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

## 3. Run the Development Server

```bash
npm run dev
```

## 4. Open Your Browser

Navigate to [http://localhost:3000](http://localhost:3000)

## 5. Test the App

Try these examples:

### Example 1: Simple Website
- **URL**: `https://example.com`
- **Prompt**: `What is the main heading on this page?`

### Example 2: Contact Form Check
- **URL**: `https://www.wikipedia.org`
- **Prompt**: `Does this page have a search box? If so, where is it located?`

### Example 3: Content Analysis
- **URL**: `https://news.ycombinator.com`
- **Prompt**: `List the top 3 article titles visible on this page`

## How It Works

1. **You enter a URL and prompt** - Tell the AI what to look for
2. **Smart scrolling happens** - The app scrolls through the entire page, expands hidden content, clicks "show more" buttons
3. **Full-page screenshot taken** - Captures everything, not just the visible area
4. **AI analyzes the page** - GPT-4 Vision examines the screenshot and responds to your prompt
5. **Results displayed** - See the AI's analysis and the full-page screenshot

## What You Can Ask

### Verification Tasks
- "Check if this page has a newsletter signup form"
- "Verify that the privacy policy link is present in the footer"
- "Does this page display customer testimonials?"

### Content Extraction
- "List all the main navigation menu items"
- "What are the pricing tiers shown on this page?"
- "Extract the contact information displayed"

### UI/UX Analysis
- "Describe the layout and color scheme of this page"
- "Are there any accessibility issues visible?"
- "What call-to-action buttons are present?"

### Data Gathering
- "List all the product categories shown"
- "What social media links are available?"
- "What languages or region options are available?"

## Troubleshooting

### "OPENAI_API_KEY environment variable is not set"
- Make sure you created the `.env` file
- Check that your API key is correctly pasted
- Restart the dev server after adding the key

### "Browser launch failed" (Development)
- Make sure you have Chrome installed
- On Linux, install: `sudo apt-get install chromium-browser`
- On macOS, install Chrome from [google.com/chrome](https://www.google.com/chrome/)

### Slow Response Times
- Large pages with lots of content take longer
- Complex pages may take 30-60 seconds
- This is normal - the app is scrolling through the entire page

### OpenAI API Errors
- Check your API key is valid
- Ensure you have credits on your OpenAI account
- Check [platform.openai.com/usage](https://platform.openai.com/usage) for usage limits

## Next Steps

### Deploy to Vercel
See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

Quick deploy:
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Add your API key
vercel env add OPENAI_API_KEY

# Deploy to production
vercel --prod
```

### Customize the App
- Modify the UI in `pages/index.tsx`
- Adjust scrolling behavior in `pages/api/verify.ts`
- Change viewport size or screenshot quality in the API route

### Add Features
- Save analysis history to a database
- Add user authentication
- Implement caching for repeated URLs
- Add support for PDFs or other document types
- Create scheduled monitoring of pages

## Support

If you run into issues:
1. Check the console for error messages
2. Verify your OpenAI API key is valid
3. Try with a simpler website first
4. Check the [README.md](./README.md) for more details

Happy testing! 🚀
