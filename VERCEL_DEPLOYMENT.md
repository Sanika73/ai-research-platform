# 🚀 Vercel Deployment Guide

This guide will help you deploy the AI Research Platform to Vercel successfully.

## 📋 Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **OpenAI API Key**: Get from [platform.openai.com](https://platform.openai.com/api-keys)
3. **GitHub Repository**: Your code should be in a GitHub repository

## 🔧 Pre-Deployment Setup

### 1. Environment Variables

In your Vercel dashboard, you'll need to set these environment variables:

| Key | Value | Description |
|-----|-------|-------------|
| `OPENAI_API_KEY` | `your_openai_api_key` | Your OpenAI API key |
| `PYTHONPATH` | `/var/task` | Python path for imports |

### 2. Project Configuration

The following files are already configured for Vercel deployment:

- ✅ `vercel.json` - Vercel configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `api/index.py` - Serverless FastAPI app
- ✅ `services/vercel_storage.py` - Serverless-compatible storage

## 🚀 Deployment Steps

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Import Project**:
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import from GitHub: `MajorAbdullah/ai-research-platform`

2. **Configure Project**:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (leave as default)
   - **Build Command**: Leave empty (not needed for serverless)
   - **Output Directory**: Leave empty
   - **Install Command**: `pip install -r requirements.txt`

3. **Add Environment Variables**:
   - In the deployment configuration, add:
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `PYTHONPATH`: `/var/task`

4. **Deploy**:
   - Click "Deploy"
   - Wait for deployment to complete

### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   cd /path/to/your/project
   vercel
   ```

4. **Set Environment Variables**:
   ```bash
   vercel env add OPENAI_API_KEY
   vercel env add PYTHONPATH
   ```

## 🔍 Verification

After deployment, test these endpoints:

1. **Home Page**: `https://your-app.vercel.app/`
2. **Health Check**: `https://your-app.vercel.app/api/health`
3. **Models**: `https://your-app.vercel.app/api/models`

## ⚡ Performance Considerations

### Serverless Limitations

1. **Function Timeout**: Max 10 seconds (Hobby) / 5 minutes (Pro)
2. **Memory**: 1024MB max
3. **Cold Starts**: First request may be slower
4. **Stateless**: No persistent storage between requests

### Optimizations Applied

- ✅ **Synchronous Processing**: Research happens immediately
- ✅ **Simplified Models**: Optimized for serverless
- ✅ **Memory Storage**: Uses in-memory storage for session
- ✅ **Error Handling**: Graceful fallbacks

## 🗄️ Database Options

For production use, consider these external databases:

### Option 1: Vercel KV (Redis)
```bash
# Add to your Vercel project
vercel env add KV_REST_API_URL
vercel env add KV_REST_API_TOKEN
```

### Option 2: PlanetScale (MySQL)
```bash
# Add connection string
vercel env add DATABASE_URL
```

### Option 3: Supabase (PostgreSQL)
```bash
# Add Supabase URL and key
vercel env add SUPABASE_URL
vercel env add SUPABASE_ANON_KEY
```

## 🐛 Troubleshooting

### Common Issues

1. **"Module not found" Error**:
   - Ensure `PYTHONPATH=/var/task` is set
   - Check import paths in `api/index.py`

2. **OpenAI API Error**:
   - Verify `OPENAI_API_KEY` is set correctly
   - Check API key permissions

3. **Function Timeout**:
   - Research queries taking too long
   - Consider using shorter prompts
   - Upgrade to Vercel Pro for longer timeouts

4. **Memory Issues**:
   - Large responses causing memory problems
   - Implement response streaming
   - Use external storage for large results

### Debug Steps

1. **Check Logs**:
   ```bash
   vercel logs your-app-url
   ```

2. **Test Locally**:
   ```bash
   cd api
   python index.py
   ```

3. **Verify Environment**:
   ```bash
   vercel env ls
   ```

## 📊 Monitoring

### Vercel Analytics

Enable analytics in your Vercel dashboard:
- Function execution times
- Error rates
- Geographic performance

### Custom Monitoring

Add logging to track:
- Research request patterns
- API response times
- Error frequencies

## 🔄 Updates and Maintenance

### Automatic Deployments

- Connected to GitHub for auto-deploy on push
- Staging/preview deployments for pull requests

### Manual Updates

```bash
# Redeploy current version
vercel --prod

# Deploy specific branch
vercel --prod --branch main
```

## 🎯 Next Steps

1. **Custom Domain**: Add your domain in Vercel dashboard
2. **Database**: Integrate external database for persistence
3. **Caching**: Implement Redis for response caching
4. **Analytics**: Add user analytics and monitoring
5. **Rate Limiting**: Implement API rate limiting

## 📞 Support

If you encounter issues:

1. Check [Vercel Documentation](https://vercel.com/docs)
2. Review [FastAPI on Vercel Guide](https://vercel.com/guides/deploying-fastapi-with-vercel)
3. Open an issue in the GitHub repository

---

**Your AI Research Platform is now ready for Vercel! 🎉**
