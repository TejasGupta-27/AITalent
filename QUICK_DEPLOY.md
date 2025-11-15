# Quick Deployment Guide for Demo

## 🚀 Fastest Way: Railway (Backend) + Vercel (Frontend)

### Step 1: Deploy Backend on Railway (5 minutes)

1. Go to https://railway.app and sign up/login
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. In project settings:
   - Set **Root Directory** to `backend`
   - Add these environment variables:
     ```
     GROQ_API_KEY=your_key_here
     WEATHER_API_KEY=your_key_here
     DEEPGRAM_API_KEY=your_key_here
     CORS_ORIGINS=https://your-app.vercel.app
     ```
5. Railway will auto-deploy. **Copy the URL** (e.g., `https://your-app.railway.app`)

### Step 2: Deploy Frontend on Vercel (5 minutes)

**Option A: Via Vercel CLI**
```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```
When prompted, add environment variable:
- `VITE_API_URL` = your Railway backend URL

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
   - Value: Your Railway backend URL (from Step 1)
7. Click **"Deploy"**

### Step 3: Update CORS

1. Go back to Railway dashboard
2. Update `CORS_ORIGINS` environment variable to include your Vercel URL:
   ```
   CORS_ORIGINS=https://your-app.vercel.app
   ```
3. Redeploy backend (Railway auto-redeploys on env changes)

### Step 4: Test Your Demo

- Frontend: `https://your-app.vercel.app`
- Backend API Docs: `https://your-backend.railway.app/api/docs`

## ✅ Done! Share your demo URL

Your application is now live and ready to demo!

## Alternative: Render (if Railway doesn't work)

### Backend on Render:
1. Go to https://render.com
2. **New** → **Web Service**
3. Connect GitHub repo
4. Settings:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add same environment variables as Railway
6. Deploy and get URL

Then follow Step 2 above, using Render URL instead.

## Troubleshooting

**CORS Error?**
- Make sure `CORS_ORIGINS` includes your exact Vercel URL (with https://)
- Redeploy backend after updating CORS

**API not connecting?**
- Check `VITE_API_URL` is set in Vercel
- Test backend URL directly: `https://your-backend-url/`

**Build failing?**
- Check all dependencies are in `package.json` and `requirements.txt`
- Check Railway/Render logs for errors

