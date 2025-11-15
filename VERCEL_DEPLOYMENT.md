# Vercel Deployment Guide

This guide will help you deploy the Weather Activity Advisor application on Vercel.

## Architecture

For this full-stack application, we'll use a **hybrid approach**:
- **Frontend (React)**: Deploy on Vercel ✅
- **Backend (FastAPI)**: Deploy on Railway/Render (recommended) or use Vercel serverless functions

## Option 1: Frontend on Vercel + Backend on Railway (Recommended)

This is the easiest and most reliable approach for a demo.

### Step 1: Deploy Backend on Railway

1. **Sign up/Login to Railway**: https://railway.app

2. **Create a New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo" (or upload the backend folder)

3. **Configure Backend**:
   - Set root directory to `backend`
   - Railway will auto-detect Python
   - Add environment variables:
     ```
     GROQ_API_KEY=your_groq_api_key
     WEATHER_API_KEY=your_weather_api_key
     DEEPGRAM_API_KEY=your_deepgram_api_key
     CORS_ORIGINS=https://your-vercel-app.vercel.app
     ```

4. **Get Backend URL**:
   - Railway will provide a URL like: `https://your-app.railway.app`
   - Note this URL for the next step

### Step 2: Deploy Frontend on Vercel

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Set Environment Variable**:
   - Create a `.env.production` file in the `frontend` directory:
     ```env
     VITE_API_URL=https://your-app.railway.app
     ```
   - Or set it in Vercel dashboard after deployment

4. **Deploy**:
   ```bash
   cd frontend
   vercel
   ```
   
   Or deploy via GitHub:
   - Push your code to GitHub
   - Go to https://vercel.com
   - Click "New Project"
   - Import your repository
   - Set root directory to `frontend`
   - Add environment variable: `VITE_API_URL` = your Railway backend URL
   - Deploy!

5. **Update CORS in Backend**:
   - After getting your Vercel URL, update `CORS_ORIGINS` in Railway to include your Vercel domain

## Option 2: Frontend on Vercel + Backend on Render

### Deploy Backend on Render:

1. **Sign up/Login**: https://render.com

2. **Create New Web Service**:
   - Connect your GitHub repository
   - Set:
     - **Root Directory**: `backend`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Environment**: Python 3

3. **Add Environment Variables**:
   ```
   GROQ_API_KEY=your_groq_api_key
   WEATHER_API_KEY=your_weather_api_key
   DEEPGRAM_API_KEY=your_deepgram_api_key
   CORS_ORIGINS=https://your-vercel-app.vercel.app
   ```

4. **Deploy and get URL**: Render will provide a URL like `https://your-app.onrender.com`

5. **Follow Step 2 from Option 1** to deploy frontend, using the Render URL

## Option 3: Both on Vercel (Advanced)

This requires converting the FastAPI backend to Vercel serverless functions.

### Create API Handler for Vercel:

1. **Install Vercel Python Runtime**:
   ```bash
   pip install vercel
   ```

2. **Create `api/index.py`** in the root:
   ```python
   from backend.main import app
   from mangum import Mangum
   
   handler = Mangum(app)
   ```

3. **Update `vercel.json`**:
   ```json
   {
     "builds": [
       {
         "src": "api/index.py",
         "use": "@vercel/python"
       },
       {
         "src": "frontend/package.json",
         "use": "@vercel/static-build",
         "config": {
           "distDir": "dist"
         }
       }
     ],
     "routes": [
       {
         "src": "/api/(.*)",
         "dest": "api/index.py"
       },
       {
         "src": "/(.*)",
         "dest": "frontend/$1"
       }
     ]
   }
   ```

**Note**: This approach has limitations with file uploads and may require additional configuration.

## Quick Deploy Commands

### For Frontend on Vercel:
```bash
# From project root
cd frontend
vercel --prod
```

### Or via GitHub:
1. Push code to GitHub
2. Go to vercel.com
3. Import repository
4. Set root directory: `frontend`
5. Add environment variable: `VITE_API_URL`
6. Deploy

## Environment Variables Checklist

### Frontend (Vercel):
- `VITE_API_URL` - Your backend URL (Railway/Render)

### Backend (Railway/Render):
- `GROQ_API_KEY` - Your Groq API key
- `WEATHER_API_KEY` - Your WeatherAPI.com key
- `DEEPGRAM_API_KEY` - Your Deepgram API key
- `CORS_ORIGINS` - Your Vercel frontend URL (comma-separated if multiple)

## Testing After Deployment

1. **Frontend URL**: `https://your-app.vercel.app`
2. **Backend URL**: `https://your-backend.railway.app` or `https://your-backend.onrender.com`
3. **Test endpoints**:
   - Frontend: Open in browser
   - Backend: `https://your-backend-url/api/docs` (FastAPI docs)

## Troubleshooting

### CORS Errors:
- Make sure `CORS_ORIGINS` in backend includes your Vercel frontend URL
- Check that the URL matches exactly (including https://)

### API Connection Issues:
- Verify `VITE_API_URL` is set correctly in Vercel
- Check backend is running and accessible
- Test backend URL directly: `https://your-backend-url/`

### Build Errors:
- Ensure all dependencies are in `package.json` (frontend) and `requirements.txt` (backend)
- Check Node.js and Python versions match your local environment

## Recommended: Option 1 (Railway + Vercel)

This is the most straightforward approach:
- ✅ Easy setup
- ✅ Reliable
- ✅ Free tiers available
- ✅ Fast deployment
- ✅ Good for demos

## Next Steps

1. Deploy backend on Railway (5 minutes)
2. Deploy frontend on Vercel (5 minutes)
3. Update CORS settings
4. Test the full application
5. Share your demo URL! 🚀

