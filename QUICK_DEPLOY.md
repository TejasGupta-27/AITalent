# Quick Deployment Guide for Demo

## 🚀 Fastest Way: Render (Backend) + Vercel (Frontend)

### Step 1: Deploy Backend on Render (5 minutes)

1. Go to https://render.com and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: Choose a name (e.g., `weather-advisor-backend`)
   - **Root Directory**: Leave empty (uses root) OR set to `backend` (see note below)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   
   **Note**: You can use either:
   - **Root directory** (recommended): Leave Root Directory empty. Uses the root `main.py` and `Procfile` we set up.
   - **Backend directory**: Set Root Directory to `backend`. Uses `backend/main.py` and `backend/Procfile`.

5. **Add Environment Variables**:
   - Click on "Environment" tab or "Environment Variables" section
   - Click "Add Environment Variable" for each:
     ```
     GROQ_API_KEY=your_key_here
     WEATHER_API_KEY=your_key_here
     DEEPGRAM_API_KEY=your_key_here
     CORS_ORIGINS=https://your-app.vercel.app
     ```
   - You can set `CORS_ORIGINS` to `*` initially for testing, then update with your Vercel URL later

6. Click **"Create Web Service"**
7. Render will start deploying. **Copy the URL** when ready (e.g., `https://aitalent.onrender.com`)

### Step 2: Deploy Frontend on Vercel (5 minutes)

**Option A: Via Vercel CLI**
```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```
When prompted, add environment variable:
- `VITE_API_URL` = your Render backend URL

**Option B: Via GitHub (Recommended)**
1. Push your code to GitHub
2. Go to https://vercel.com
3. Click **"Add New..."** → **"Project"**
4. Import your GitHub repository
5. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
6. Add Environment Variable:
   - Key: `VITE_API_URL`
   - Value: Your Render backend URL (from Step 1)
7. Click **"Deploy"**

### Step 3: Update CORS

1. Go back to Render dashboard
2. Click on your web service
3. Go to "Environment" tab
4. Update `CORS_ORIGINS` environment variable to include your Vercel URL:
   ```
   CORS_ORIGINS=https://your-app.vercel.app
   ```
5. Render will automatically redeploy when you save environment variable changes

### Step 4: Test Your Demo

- Frontend: `https://your-app.vercel.app`
- Backend API Docs: `https://aitalent.onrender.com/api/docs`
- Backend Root: `https://aitalent.onrender.com/`

## ✅ Done! Share your demo URL

Your application is now live and ready to demo!

## How to Add Environment Variables in Render

1. Go to your Render dashboard: https://dashboard.render.com
2. Click on your web service
3. Click on the **"Environment"** tab (in the left sidebar)
4. Scroll to **"Environment Variables"** section
5. Click **"Add Environment Variable"**
6. Enter:
   - **Key**: Variable name (e.g., `GROQ_API_KEY`)
   - **Value**: Your API key value
7. Click **"Save Changes"**
8. Render will automatically redeploy your service

**Note**: Environment variable values are hidden after saving for security. You can edit them later if needed.

## Troubleshooting

**CORS Error?**
- Make sure `CORS_ORIGINS` includes your exact Vercel URL (with https://)
- Redeploy backend after updating CORS

**API not connecting?**
- Check `VITE_API_URL` is set in Vercel (should be `https://aitalent.onrender.com`)
- Test backend URL directly: `https://aitalent.onrender.com/`
- Check API docs: `https://aitalent.onrender.com/api/docs`

**Build failing?**
- Check all dependencies are in `package.json` and `requirements.txt`
- Check Render logs for errors (click on your service → "Logs" tab)
- Verify Python version is 3.x in Render settings
- Make sure Root Directory is set correctly (empty for root, or `backend` for backend directory)

