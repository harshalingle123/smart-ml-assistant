# Render Blueprint - Quick Start Guide

Fast-track deployment guide for Smart ML Assistant using Render Blueprint.

## 5-Minute Pre-Deployment Checklist

### 1. MongoDB Atlas (10 minutes)
- [ ] Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
- [ ] Create free M0 cluster
- [ ] Create database user (username + password)
- [ ] Whitelist all IPs (0.0.0.0/0) under Network Access
- [ ] Copy connection string
- [ ] Format: `mongodb+srv://username:password@cluster.mongodb.net/smart_ml_assistant?retryWrites=true&w=majority`

### 2. Generate SECRET_KEY (1 minute)
Run this command:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Save the output.

### 3. GitHub (2 minutes)
```bash
git add .
git commit -m "Ready for Render deployment"
git push
```

### 4. Prepare Environment Variables
Copy these values to a text file:

```
MONGO_URI=mongodb+srv://your_user:your_pass@cluster.mongodb.net/smart_ml_assistant?retryWrites=true&w=majority
SECRET_KEY=<output from step 2>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
CORS_ORIGINS=
```

## Deploy to Render (15 minutes)

### Step 1: Create Blueprint Instance
1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New +** → **Blueprint**
3. Connect your GitHub repository
4. Render detects `render.yaml`

### Step 2: Set Environment Variables
When prompted, paste the values you prepared:

| Variable | Value |
|----------|-------|
| `MONGO_URI` | Your MongoDB connection string |
| `SECRET_KEY` | Generated secret key |
| `CORS_ORIGINS` | Leave empty for now |
| `GOOGLE_CLIENT_ID` | (Optional) Leave empty |
| `GOOGLE_CLIENT_SECRET` | (Optional) Leave empty |
| `GOOGLE_REDIRECT_URI` | (Optional) Leave empty |

### Step 3: Deploy
1. Click **Apply**
2. Wait 10-15 minutes for both services to build
3. Both services should show **Live** status

### Step 4: Get URLs
**Backend URL:**
- Go to `smart-ml-backend` service
- Copy URL (e.g., `https://smart-ml-backend.onrender.com`)

**Frontend URL:**
- Go to `smart-ml-frontend` service
- Copy URL (e.g., `https://smart-ml-frontend.onrender.com`)

### Step 5: Update CORS
1. Go to `smart-ml-backend` service
2. Click **Environment** tab
3. Edit `CORS_ORIGINS`
4. Set to: `https://smart-ml-frontend.onrender.com`
5. Click **Save Changes** (auto-redeploys)

### Step 6: Test
Visit your frontend URL and test:
- [ ] Page loads
- [ ] Can register account
- [ ] Can login
- [ ] Can create chat
- [ ] Backend health: `https://smart-ml-backend.onrender.com/health`

## Done!

Your app is live at: `https://smart-ml-frontend.onrender.com`

## Common Issues

**Backend won't start?**
- Check logs in Render dashboard
- Verify MongoDB connection string

**Frontend can't connect?**
- Ensure CORS_ORIGINS is set
- Check backend is live at `/health`

**First request slow?**
- Normal! Free tier has 30-60 second cold start
- Upgrade to $7/month Starter plan to remove cold starts

## Optional: Google OAuth

If you want Google Sign-In:

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create OAuth 2.0 credentials
3. Add redirect URI: `https://smart-ml-frontend.onrender.com/auth/callback`
4. In Render backend environment, set:
   - `GOOGLE_CLIENT_ID`: Your client ID
   - `GOOGLE_CLIENT_SECRET`: Your client secret
   - `GOOGLE_REDIRECT_URI`: `https://smart-ml-frontend.onrender.com/auth/callback`

## Automatic Updates

Every time you push to GitHub:
```bash
git add .
git commit -m "New feature"
git push
```
Render automatically rebuilds and redeploys both services.

## Monitoring

**View logs:**
- Render Dashboard → Service → Logs

**Check health:**
- Visit: `https://smart-ml-backend.onrender.com/health`

**Set alerts:**
- Service → Settings → Alerting

## Costs

**Current setup: $0/month**
- Free tier includes both services
- MongoDB Atlas free tier (512MB)

**To eliminate cold starts: $7/month**
- Upgrade backend to Starter plan
- Always-on, no spin-down

## Need Help?

- Full guide: See `RENDER_BLUEPRINT_DEPLOY.md`
- Environment template: See `.env.render.template`
- Render docs: [render.com/docs](https://render.com/docs)
- Community: [community.render.com](https://community.render.com)

---

**Total deployment time: ~30 minutes**

Share your app: `https://smart-ml-frontend.onrender.com`
