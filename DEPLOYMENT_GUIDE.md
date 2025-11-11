# Render Deployment Guide - Smart ML Assistant

This guide will walk you through deploying your full-stack application on Render.

## Prerequisites

1. **GitHub Account** - Your code should be on GitHub
2. **Render Account** - Sign up at [render.com](https://render.com) (free)
3. **MongoDB Atlas Account** - Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) (free)

## Step 1: Set Up MongoDB Atlas (Database)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Create a free cluster (M0 - 512MB storage)
3. Create a database user:
   - Go to **Database Access** → **Add New Database User**
   - Username: `your_username`
   - Password: `your_secure_password` (save this!)
   - User Privileges: **Read and write to any database**
4. Set up network access:
   - Go to **Network Access** → **Add IP Address**
   - Click **Allow Access from Anywhere** (0.0.0.0/0)
   - Confirm
5. Get your connection string:
   - Go to **Database** → **Connect** → **Connect your application**
   - Copy the connection string (looks like):
     ```
     mongodb+srv://username:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
     ```
   - Replace `<password>` with your actual password
   - Add your database name before the `?`:
     ```
     mongodb+srv://username:password@cluster.mongodb.net/smart_ml_assistant?retryWrites=true&w=majority
     ```

## Step 2: Push Your Code to GitHub

```bash
# Initialize git if you haven't
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - ready for deployment"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/smart-ml-assistant.git
git branch -M main
git push -u origin main
```

## Step 3: Deploy Backend on Render

1. **Go to Render Dashboard**
   - Visit [dashboard.render.com](https://dashboard.render.com)
   - Click **New +** → **Web Service**

2. **Connect Your Repository**
   - Select **Connect GitHub**
   - Choose your `smart-ml-assistant` repository

3. **Configure Backend Service**
   - **Name**: `smart-ml-backend` (or any name you prefer)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: **Free**

4. **Add Environment Variables**
   Click **Advanced** → **Add Environment Variable**:

   | Key | Value |
   |-----|-------|
   | `MONGO_URI` | Your MongoDB connection string from Step 1 |
   | `SECRET_KEY` | Generate a random string (32+ characters) or let Render auto-generate |
   | `ALGORITHM` | `HS256` |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
   | `ENVIRONMENT` | `production` |
   | `CORS_ORIGINS` | Leave empty for now (we'll update after frontend deployment) |
   | `GOOGLE_CLIENT_ID` | (Optional) Your Google OAuth client ID |
   | `GOOGLE_CLIENT_SECRET` | (Optional) Your Google OAuth client secret |

   **Generate SECRET_KEY** (if needed):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Create Service**
   - Click **Create Web Service**
   - Wait 5-10 minutes for deployment
   - Once deployed, you'll get a URL like: `https://smart-ml-backend.onrender.com`
   - **Save this URL!**

6. **Test Backend**
   - Visit: `https://smart-ml-backend.onrender.com/health`
   - Should return: `{"status": "healthy"}`

## Step 4: Deploy Frontend on Render

1. **Create New Static Site**
   - Go to Render Dashboard
   - Click **New +** → **Static Site**
   - Select your `smart-ml-assistant` repository

2. **Configure Frontend Service**
   - **Name**: `smart-ml-frontend`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**:
     ```bash
     npm install && npm run build
     ```
   - **Publish Directory**: `dist/public`

3. **Add Environment Variables**
   - **Key**: `VITE_API_URL`
   - **Value**: Your backend URL (e.g., `https://smart-ml-backend.onrender.com`)

4. **Create Static Site**
   - Click **Create Static Site**
   - Wait 5-10 minutes for deployment
   - You'll get a URL like: `https://smart-ml-frontend.onrender.com`

## Step 5: Update CORS Settings

Now that both services are deployed, update the backend CORS settings:

1. Go to your backend service on Render
2. Navigate to **Environment**
3. Update the `CORS_ORIGINS` variable:
   ```
   https://smart-ml-frontend.onrender.com
   ```
4. Click **Save Changes**
5. Your backend will automatically redeploy

## Step 6: Update Google OAuth Redirect URI (If Using)

If you're using Google OAuth:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project
3. Go to **APIs & Services** → **Credentials**
4. Edit your OAuth 2.0 Client ID
5. Add to **Authorized redirect URIs**:
   ```
   https://smart-ml-frontend.onrender.com/auth/callback
   ```
6. Update the `GOOGLE_REDIRECT_URI` environment variable in your backend service on Render

## Step 7: Test Your Deployment

1. Visit your frontend URL: `https://smart-ml-frontend.onrender.com`
2. Try to:
   - Register a new account
   - Login
   - Create a chat
   - Upload a dataset
   - Use all features

## Important Notes

### Free Tier Limitations

- **Backend**: Spins down after 15 minutes of inactivity
  - First request after spin-down takes ~30 seconds (cold start)
  - Subsequent requests are fast
- **Frontend**: Always online, no cold starts
- **Database**: MongoDB Atlas free tier (512MB storage)

### Upgrade When Needed

When your app gets more traffic:
1. Upgrade backend to Starter ($7/month) - removes cold starts
2. Keep frontend free (static sites don't need upgrades usually)
3. MongoDB Atlas free tier is enough for ~10,000 users

### Monitoring

- **View Logs**: Render Dashboard → Your Service → Logs
- **Monitor Health**: Visit `/health` endpoint regularly
- **Set Up Alerts**: Render Dashboard → Service → Alerts

### Custom Domain (Optional)

To add your own domain:
1. Go to your service on Render
2. Click **Settings** → **Custom Domain**
3. Add your domain and configure DNS as instructed

## Troubleshooting

### Backend Won't Start
- Check logs in Render dashboard
- Verify all environment variables are set correctly
- Ensure MongoDB connection string is correct

### Frontend Can't Connect to Backend
- Verify `VITE_API_URL` is set correctly
- Check backend is running (visit /health endpoint)
- Ensure CORS_ORIGINS includes your frontend URL

### Database Connection Issues
- Verify MongoDB Atlas IP whitelist includes 0.0.0.0/0
- Check your connection string format
- Ensure database user has correct permissions

### Google OAuth Not Working
- Verify redirect URIs in Google Console
- Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set
- Ensure GOOGLE_REDIRECT_URI matches your frontend domain

## Alternative: Deploy Using render.yaml

You can also use the included `render.yaml` file for automated deployment:

1. Push your code to GitHub
2. Go to Render Dashboard
3. Click **New +** → **Blueprint**
4. Connect your repository
5. Render will automatically detect `render.yaml` and create both services
6. Add environment variables as prompted

## Next Steps

- Set up monitoring and alerts
- Configure custom domain
- Set up CI/CD for automatic deployments
- Monitor logs and performance
- Consider upgrading backend when needed ($7/month removes cold starts)

## Support

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **MongoDB Atlas Docs**: [docs.atlas.mongodb.com](https://www.mongodb.com/docs/atlas/)
- **Community**: [community.render.com](https://community.render.com)

---

Your app is now live! Share your frontend URL with users.
