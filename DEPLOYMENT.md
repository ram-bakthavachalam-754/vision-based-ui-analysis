# Deployment Guide - Vercel

This guide will help you deploy the Vision-Based Testing app to Vercel.

## Prerequisites

1. A Vercel account ([Sign up here](https://vercel.com/signup))
2. An OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
3. GitHub account (recommended for automatic deployments)

## Quick Deploy (GitHub + Vercel Dashboard)

### Step 1: Push to GitHub

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Vision-based testing app"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New Project"
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: Next.js (should be auto-detected)
   - **Root Directory**: `./` (default)
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)

5. **Add Environment Variable**:
   - Click "Environment Variables"
   - Name: `OPENAI_API_KEY`
   - Value: `sk-your-openai-api-key-here`
   - Select all environments (Production, Preview, Development)

6. Click "Deploy"

### Step 3: Wait for Deployment

Vercel will:
- Install dependencies
- Build your Next.js app
- Deploy to a production URL

This takes 2-5 minutes.

### Step 4: Test Your Deployment

Once deployed, you'll get a URL like: `https://your-project.vercel.app`

Test it by:
1. Opening the URL
2. Enter a test URL (e.g., `https://example.com`)
3. Enter a test prompt (e.g., "Describe the main heading of this page")
4. Click "Verify Page"

## Deploy via Vercel CLI

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Login to Vercel

```bash
vercel login
```

### Step 3: Deploy

```bash
# From the project directory
cd /Users/ram-bakthavachalam/projects/vision-based-testing

# Deploy to preview
vercel

# Follow the prompts
```

### Step 4: Add Environment Variables

```bash
vercel env add OPENAI_API_KEY
```

When prompted:
- Select: **Production, Preview, Development**
- Paste your OpenAI API key

### Step 5: Deploy to Production

```bash
vercel --prod
```

## Important Configuration

### Function Timeout

The `vercel.json` file configures the API route timeout:

```json
{
  "functions": {
    "pages/api/**/*.ts": {
      "maxDuration": 60
    }
  }
}
```

**Note**: 
- **Free Plan**: 10-second limit (may timeout on complex pages)
- **Pro Plan**: 60-second limit (recommended)
- **Enterprise Plan**: 300-second limit

If you experience timeouts on the free plan, consider:
- Upgrading to Vercel Pro
- Testing with simpler/faster-loading pages
- Reducing the number of scroll iterations in the code

### Memory and Performance

For better performance with large screenshots:
- Vercel Pro provides 3GB memory (vs 1GB on free)
- Consider upgrading if you see memory-related errors

## Troubleshooting

### Deployment Fails with "Module not found"

- Ensure all dependencies are in `package.json`
- Clear cache and redeploy: `vercel --force`

### Function Timeout Errors

- Upgrade to Vercel Pro for 60s timeout
- Or reduce processing time by modifying scroll logic

### Browser Launch Fails

- This usually works automatically with `@sparticuz/chromium`
- Check build logs for specific errors
- Ensure Node.js version is 18.x or higher

### Environment Variables Not Working

- Redeploy after adding environment variables
- Check variable names match exactly
- Ensure variables are added to all environments

### High OpenAI API Costs

- Each verification uses GPT-4 Vision (more expensive)
- Consider adding caching for repeated URLs
- Add authentication to prevent abuse
- Monitor usage at [platform.openai.com/usage](https://platform.openai.com/usage)

## Post-Deployment

### Custom Domain

1. In Vercel dashboard, go to your project
2. Click "Settings" → "Domains"
3. Add your custom domain
4. Follow DNS configuration instructions

### Analytics

Enable Vercel Analytics:
1. Go to project settings
2. Click "Analytics"
3. Enable Web Analytics

### Monitoring

Monitor your deployment:
- **Functions**: See execution logs and errors
- **Usage**: Track API calls and bandwidth
- **Analytics**: View page views and performance

## Continuous Deployment

Once connected to GitHub:
- Every push to `main` branch triggers production deployment
- Pull requests get preview deployments
- Automatic rollback available if issues detected

## Security Best Practices

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Use environment variables** for all secrets
3. **Add rate limiting** for public deployments
4. **Monitor API usage** to prevent abuse
5. **Consider adding authentication** for production use

## Cost Optimization

### Vercel Costs
- Free tier: Good for testing and demos
- Pro tier ($20/month): Recommended for production

### OpenAI API Costs
- GPT-4 Vision: ~$0.01-0.03 per image depending on size
- Full-page screenshots can be large (higher cost)
- Consider resizing images before sending to API

## Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Next.js Docs**: [nextjs.org/docs](https://nextjs.org/docs)
- **OpenAI Docs**: [platform.openai.com/docs](https://platform.openai.com/docs)

## Next Steps

After deployment:
1. Test thoroughly with various websites
2. Add error boundaries and better error handling
3. Implement caching for repeated analyses
4. Add authentication if needed
5. Set up monitoring and alerts
6. Consider adding a database for storing results
