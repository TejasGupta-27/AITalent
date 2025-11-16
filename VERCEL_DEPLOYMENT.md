# Vercel Deployment Guide

This guide will help you deploy the Weather Activity Advisor application on Vercel.

## Architecture

For this full-stack application, we'll use a **hybrid approach**:
- **Frontend (React)**: Deploy on Vercel ✅
- **Backend (FastAPI)**: Deploy on Render (recommended) or Railway, or use Vercel serverless functions

## Option 1: Frontend on Vercel + Backend on Render (Recommended)

This is the easiest and most reliable approach for a demo.

### Step 1: Deploy Backend on Render

1. **Sign up/Login to Render**: https://render.com

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

3. **Configure Backend**:
   - **Name**: Choose a name (e.g., `weather-advisor-backend`)
   - **Root Directory**: Leave empty (uses root) OR set to `backend`
     - **Root directory** (recommended): Uses the root `main.py` and `Procfile`
     - **Backend directory**: Set to `backend`, uses `backend/main.py` and `backend/Procfile`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**:
   - Go to "Environment" tab
   - Click "Add Environment Variable" for each:
     ```
     GROQ_API_KEY=your_groq_api_key
     WEATHER_API_KEY=your_weather_api_key
     DEEPGRAM_API_KEY=your_deepgram_api_key
     CORS_ORIGINS=https://your-vercel-app.vercel.app
     ```
   - You can set `CORS_ORIGINS` to `*` initially for testing

5. **Create and Deploy**:
   - Click "Create Web Service"
   - Render will start deploying
   - **Get Backend URL**: Render will provide a URL like `https://aitalent.onrender.com`
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
     VITE_API_URL=https://aitalent.onrender.com
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
   - Add environment variable: `VITE_API_URL` = your Render backend URL
   - Deploy!

5. **Update CORS in Backend**:
   - After getting your Vercel URL, go to Render dashboard
   - Click on your web service → "Environment" tab
   - Update `CORS_ORIGINS` environment variable to include your Vercel domain
   - Render will automatically redeploy

## Option 2: Frontend on Vercel + Backend on Railway

### Deploy Backend on Railway:

1. **Sign up/Login**: https://railway.app

2. **Create a New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"

3. **Configure Backend**:
   - Set root directory to `backend`
   - Railway will auto-detect Python
   - Add environment variables (see Railway dashboard → Variables tab)

4. **Get Backend URL**: Railway will provide a URL like `https://your-app.railway.app`

5. **Follow Step 2 from Option 1** to deploy frontend, using the Railway URL

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

### Backend (Render/Railway):
- `GROQ_API_KEY` - Your Groq API key
- `WEATHER_API_KEY` - Your WeatherAPI.com key
- `DEEPGRAM_API_KEY` - Your Deepgram API key
- `CORS_ORIGINS` - Your Vercel frontend URL (comma-separated if multiple)

### How to Add Environment Variables in Render:

1. Go to your Render dashboard: https://dashboard.render.com
2. Click on your web service
3. Click on the **"Environment"** tab (in the left sidebar)
4. Scroll to **"Environment Variables"** section
5. Click **"Add Environment Variable"**
6. Enter the **Key** and **Value**
7. Click **"Save Changes"**
8. Render will automatically redeploy your service

**Note**: Environment variable values are hidden after saving for security.

## Testing After Deployment

1. **Frontend URL**: `https://your-app.vercel.app`
2. **Backend URL**: `https://aitalent.onrender.com` (or your Railway URL if using Railway)
3. **Test endpoints**:
   - Frontend: Open in browser
   - Backend Root: `https://aitalent.onrender.com/`
   - Backend API Docs: `https://aitalent.onrender.com/api/docs`

## Troubleshooting

### CORS Errors:
- Make sure `CORS_ORIGINS` in backend includes your Vercel frontend URL
- Check that the URL matches exactly (including https://)

### API Connection Issues:
- Verify `VITE_API_URL` is set correctly in Vercel (should be `https://aitalent.onrender.com`)
- Check backend is running and accessible
- Test backend URL directly: `https://aitalent.onrender.com/`
- Check API docs: `https://aitalent.onrender.com/api/docs`

### Build Errors:
- Ensure all dependencies are in `package.json` (frontend) and `requirements.txt` (backend)
- Check Node.js and Python versions match your local environment

## Recommended: Option 1 (Render + Vercel)

This is the most straightforward approach:
- ✅ Easy setup
- ✅ Reliable
- ✅ Free tiers available
- ✅ Fast deployment
- ✅ Good for demos
- ✅ Clear dashboard for managing environment variables

## Next Steps

1. Deploy backend on Render (5 minutes)
2. Deploy frontend on Vercel (5 minutes)
3. Update CORS settings in Render
4. Test the full application
5. Share your demo URL! 🚀

