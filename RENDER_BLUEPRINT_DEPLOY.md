# Deploy to Render Using Blueprint (render.yaml)

This guide walks you through deploying your Smart ML Assistant application using Render's Blueprint feature for automated, streamlined deployment.

## What is Render Blueprint?

Render Blueprint allows you to define your entire infrastructure as code using a `render.yaml` file. Instead of manually creating each service, Render reads this file and automatically provisions all your services with the correct configuration.

## Prerequisites

Before you begin, ensure you have:

1. **GitHub Account** - Your code repository
2. **Render Account** - Sign up at [render.com](https://render.com) (free tier available)
3. **MongoDB Atlas Account** - Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) (free tier available)

## Step 1: Set Up MongoDB Atlas (5-10 minutes)

### Create Your Database

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) and sign up
2. Create a new project (e.g., "Smart ML Assistant")
3. Build a database cluster:
   - Choose **FREE** tier (M0)
   - Select a cloud provider and region closest to you
   - Click **Create Cluster**

### Create Database User

1. Go to **Database Access** in the left sidebar
2. Click **Add New Database User**
3. Choose **Password** authentication method
4. Set username: `ml_admin` (or your choice)
5. Generate a secure password and **SAVE IT SECURELY**
6. Set **Database User Privileges**: `Read and write to any database`
7. Click **Add User**

### Configure Network Access

1. Go to **Network Access** in the left sidebar
2. Click **Add IP Address**
3. Click **Allow Access from Anywhere** (adds 0.0.0.0/0)
   - This is required for Render's dynamic IP addresses
4. Click **Confirm**

### Get Your Connection String

1. Go to **Database** in the left sidebar
2. Click **Connect** on your cluster
3. Select **Connect your application**
4. Choose **Driver**: Python, **Version**: 3.11 or later
5. Copy the connection string (looks like):
   ```
   mongodb+srv://ml_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
6. Replace `<password>` with your actual password
7. Add your database name before the `?` (e.g., `smart_ml_assistant`):
   ```
   mongodb+srv://ml_admin:YourPassword@cluster0.xxxxx.mongodb.net/smart_ml_assistant?retryWrites=true&w=majority
   ```
8. **SAVE THIS CONNECTION STRING** - you'll need it for Render

## Step 2: Prepare Your GitHub Repository (2-5 minutes)

### Option A: If You Haven't Pushed to GitHub Yet

```bash
# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Commit your changes
git commit -m "Initial commit - Ready for Render deployment"

# Create a new repository on GitHub (via web interface)
# Then connect it:
git remote add origin https://github.com/YOUR_USERNAME/smart-ml-assistant.git
git branch -M main
git push -u origin main
```

### Option B: If Already on GitHub

```bash
# Ensure all changes are committed and pushed
git add .
git commit -m "Prepare for Render Blueprint deployment"
git push
```

### Verify render.yaml Exists

Make sure your repository has the `render.yaml` file in the root directory. The file should look like this:

```yaml
services:
  # Backend API Service
  - type: web
    name: smart-ml-backend
    runtime: python
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: MONGO_URI
        sync: false
      # ... (other variables)
    healthCheckPath: /health

  # Frontend Static Site
  - type: web
    name: smart-ml-frontend
    runtime: static
    buildCommand: cd frontend && npm install && npm run build
    staticPublishPath: ./frontend/dist/public
    # ... (other configuration)
```

## Step 3: Generate Required Secrets (2 minutes)

### Generate SECRET_KEY

Run this command to generate a secure secret key:

**On Windows (PowerShell):**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**On macOS/Linux:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**SAVE THE OUTPUT** - you'll need it for Render.

Example output: `Xk9vR3mN2pQ8wL5zA7yC1bF4tH6sD0eJ9uI3oP8qW2gV5nM7xK`

## Step 4: Prepare Environment Variables

Create a text file with these values ready (you'll paste them into Render):

### Required Environment Variables:

```
MONGO_URI=mongodb+srv://ml_admin:YourPassword@cluster0.xxxxx.mongodb.net/smart_ml_assistant?retryWrites=true&w=majority
SECRET_KEY=Xk9vR3mN2pQ8wL5zA7yC1bF4tH6sD0eJ9uI3oP8qW2gV5nM7xK
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
CORS_ORIGINS=https://smart-ml-frontend.onrender.com
```

### Optional (for Google OAuth):

```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://smart-ml-frontend.onrender.com/auth/callback
```

**Note:** You'll update `CORS_ORIGINS` with your actual frontend URL after deployment.

## Step 5: Deploy Using Render Blueprint (10-15 minutes)

### Connect Render to GitHub

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Sign up or log in
3. If first time, connect your GitHub account:
   - Click your profile icon
   - Go to **Account Settings**
   - Under **GitHub**, click **Connect**
   - Authorize Render to access your repositories

### Deploy with Blueprint

1. From Render Dashboard, click **New +** in the top navigation
2. Select **Blueprint**
3. You'll see "Create a new Blueprint Instance"
4. Click **Connect a repository**
5. Find and select your `smart-ml-assistant` repository
6. Click **Connect**

### Configure Environment Variables

Render will detect your `render.yaml` file and show a configuration screen.

1. **For smart-ml-backend service:**

   You'll see prompts for each environment variable marked with `sync: false`:

   - **MONGO_URI**: Paste your MongoDB connection string
   - **CORS_ORIGINS**: Leave empty for now (we'll update after frontend deploys)
   - **GOOGLE_CLIENT_ID**: (Optional) Your Google OAuth client ID
   - **GOOGLE_CLIENT_SECRET**: (Optional) Your Google OAuth secret
   - **GOOGLE_REDIRECT_URI**: (Optional) Your OAuth redirect URI

2. Click **Apply**

3. Render will automatically:
   - Create both services (backend and frontend)
   - Install dependencies
   - Build both applications
   - Deploy them

### Monitor Deployment

1. You'll see both services being created
2. Click on each service to view deployment logs
3. Backend typically takes 5-10 minutes
4. Frontend typically takes 5-10 minutes
5. Wait for both to show **Live** status (green indicator)

## Step 6: Get Your Service URLs (1 minute)

### Backend URL

1. Click on `smart-ml-backend` service
2. Copy the URL at the top (e.g., `https://smart-ml-backend.onrender.com`)
3. **SAVE THIS URL**

### Frontend URL

1. Click on `smart-ml-frontend` service
2. Copy the URL at the top (e.g., `https://smart-ml-frontend.onrender.com`)
3. **SAVE THIS URL**

### Test Backend

Visit your backend URL with `/health` appended:
```
https://smart-ml-backend.onrender.com/health
```

You should see:
```json
{"status": "healthy"}
```

## Step 7: Update CORS Configuration (5 minutes)

Now that you have your frontend URL, update the backend's CORS settings:

1. Go to your `smart-ml-backend` service in Render
2. Click **Environment** in the left sidebar
3. Find the `CORS_ORIGINS` variable
4. Click **Edit** (pencil icon)
5. Set the value to your frontend URL:
   ```
   https://smart-ml-frontend.onrender.com
   ```
6. Click **Save Changes**
7. Your backend will automatically redeploy (takes 2-3 minutes)

## Step 8: Configure Google OAuth (Optional, 5-10 minutes)

If you're using Google OAuth for authentication:

### Update Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project (or create one)
3. Navigate to **APIs & Services** > **Credentials**
4. Create OAuth 2.0 Client ID (if not already created):
   - Application type: **Web application**
   - Name: `Smart ML Assistant - Production`
5. Under **Authorized redirect URIs**, add:
   ```
   https://smart-ml-frontend.onrender.com/auth/callback
   ```
6. Save and copy your **Client ID** and **Client Secret**

### Update Render Environment Variables

1. Go to `smart-ml-backend` service in Render
2. Click **Environment**
3. Update these variables:
   - `GOOGLE_CLIENT_ID`: Your client ID
   - `GOOGLE_CLIENT_SECRET`: Your client secret
   - `GOOGLE_REDIRECT_URI`: `https://smart-ml-frontend.onrender.com/auth/callback`
4. Click **Save Changes**
5. Wait for redeploy

## Step 9: Test Your Deployment (10 minutes)

### Access Your Application

1. Open your frontend URL: `https://smart-ml-frontend.onrender.com`

### Test Core Features

- **Registration**: Create a new account
- **Login**: Sign in with your credentials
- **Dashboard**: Navigate to the dashboard
- **Chat**: Create a new chat and send messages
- **Dataset Upload**: Upload a CSV file
- **Model Training**: Try fine-tuning a model
- **Google OAuth**: (If configured) Test "Sign in with Google"

### Check Backend Health

Periodically visit:
```
https://smart-ml-backend.onrender.com/health
```

Should always return:
```json
{"status": "healthy"}
```

## Understanding Render's Free Tier

### Backend Service Limitations

- **Cold Starts**: Service spins down after 15 minutes of inactivity
- **First Request**: Takes 30-60 seconds to wake up (cold start)
- **Subsequent Requests**: Fast and responsive
- **Automatic Sleep**: No requests = automatic shutdown

### Frontend Service

- **Always Available**: Static sites don't sleep
- **Instant Loading**: No cold starts
- **CDN Delivery**: Fast global access

### Database (MongoDB Atlas)

- **Storage**: 512MB on free tier
- **Bandwidth**: Sufficient for ~10,000 users
- **Always On**: No cold starts

### Tips to Minimize Cold Starts

1. **Keep Alive Service**: Set up a free uptime monitoring service (like UptimeRobot) to ping your backend every 10 minutes
2. **Upgrade**: Consider Render's Starter plan ($7/month) to eliminate cold starts
3. **User Communication**: Inform users first request may be slow

## Troubleshooting

### Backend Won't Deploy

**Check the logs:**
1. Go to `smart-ml-backend` service
2. Click **Logs** tab
3. Look for error messages

**Common issues:**
- Missing environment variables
- Invalid MongoDB connection string
- Python dependency conflicts

**Solutions:**
- Verify all required env vars are set
- Test MongoDB connection string locally
- Check `requirements.txt` for version conflicts

### Frontend Build Fails

**Check the logs:**
1. Go to `smart-ml-frontend` service
2. Click **Logs** tab
3. Look for build errors

**Common issues:**
- Node.js version mismatch
- Missing dependencies
- Build command errors

**Solutions:**
- Verify `NODE_VERSION` is set correctly (20.11.0)
- Ensure `package.json` has all dependencies
- Test build locally: `cd frontend && npm run build`

### Frontend Can't Connect to Backend

**Symptoms:**
- API requests fail
- "Network Error" in console
- CORS errors

**Solutions:**
1. Verify `VITE_API_URL` environment variable in frontend (not needed for Blueprint, but check if added)
2. Ensure `CORS_ORIGINS` in backend includes your frontend URL
3. Test backend health endpoint
4. Check browser console for specific errors

### Database Connection Issues

**Symptoms:**
- "MongoServerError" in logs
- "Authentication failed"
- "Could not connect to MongoDB"

**Solutions:**
1. Verify MongoDB Atlas IP whitelist includes `0.0.0.0/0`
2. Check connection string format is correct
3. Ensure database user has read/write permissions
4. Test connection string locally

### Google OAuth Not Working

**Symptoms:**
- "Redirect URI mismatch"
- OAuth flow fails
- Can't sign in with Google

**Solutions:**
1. Verify redirect URI in Google Console matches exactly
2. Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
3. Ensure `GOOGLE_REDIRECT_URI` matches your frontend URL
4. Clear browser cookies and try again

## Monitoring and Maintenance

### View Logs

**Real-time logs:**
1. Go to your service
2. Click **Logs** tab
3. Watch live deployment and runtime logs

**Search logs:**
- Use the search bar to find specific errors
- Filter by date/time

### Set Up Alerts

1. Go to your service
2. Click **Settings** tab
3. Scroll to **Alerting**
4. Add email for deploy failures

### Monitor Performance

1. Go to **Metrics** tab
2. View:
   - CPU usage
   - Memory usage
   - Request count
   - Response times

### Health Checks

Render automatically monitors your `/health` endpoint. If it fails:
- Service marked as unhealthy
- Automatic restart attempted
- You receive email notification (if configured)

## Updating Your Application

### Automatic Deployments

Blueprint instances auto-deploy when you push to GitHub:

1. Make changes to your code
2. Commit and push to `main` branch:
   ```bash
   git add .
   git commit -m "Update feature X"
   git push
   ```
3. Render automatically detects the push
4. Both services rebuild and redeploy
5. Check deployment status in dashboard

### Manual Deployments

To force a redeploy without code changes:

1. Go to your service
2. Click **Manual Deploy** dropdown
3. Select **Deploy latest commit**
4. Click **Deploy**

### Update Environment Variables

1. Go to service > **Environment**
2. Edit the variable
3. Click **Save Changes**
4. Service automatically redeploys

## Scaling and Upgrades

### When to Upgrade

Consider upgrading when:
- Cold starts impact user experience
- Need guaranteed uptime
- Traffic exceeds free tier limits
- Need more CPU/memory

### Backend Upgrade Options

**Starter ($7/month):**
- No cold starts
- Always-on instance
- 512MB RAM
- Perfect for small-medium apps

**Standard ($25/month):**
- More resources
- Better performance
- Higher traffic capacity

### Frontend Scaling

Static sites on free tier handle significant traffic. Upgrade only if:
- Need custom domains
- Want higher bandwidth
- Require advanced features

### Database Scaling

MongoDB Atlas free tier (512MB) is sufficient for:
- ~10,000 users
- Moderate chat/dataset storage

Upgrade when storage needs exceed 512MB.

## Custom Domain (Optional)

### Add Custom Domain to Frontend

1. Go to `smart-ml-frontend` service
2. Click **Settings** > **Custom Domains**
3. Click **Add Custom Domain**
4. Enter your domain (e.g., `app.yourdomain.com`)
5. Follow DNS configuration instructions
6. Update your DNS provider:
   - Add CNAME record
   - Point to Render's domain
7. Wait for DNS propagation (5-60 minutes)
8. Render auto-provisions SSL certificate

### Update Backend CORS

After adding custom domain:
1. Update `CORS_ORIGINS` to include your custom domain
2. If using Google OAuth, update redirect URI

## Best Practices

### Security

- **Never commit secrets**: Keep `.env` files in `.gitignore`
- **Use environment variables**: Store all secrets in Render's environment
- **Regular updates**: Keep dependencies updated
- **Monitor logs**: Check for suspicious activity

### Performance

- **Optimize builds**: Remove unnecessary dependencies
- **Enable caching**: Render automatically caches builds
- **Monitor metrics**: Watch CPU/memory usage
- **Database indexing**: Add indexes to frequently queried fields

### Reliability

- **Health checks**: Ensure `/health` endpoint works
- **Error handling**: Implement proper error responses
- **Logging**: Add detailed logging for debugging
- **Backups**: Regularly backup MongoDB data

### Cost Optimization

- **Start free**: Use free tier for development/testing
- **Upgrade gradually**: Only upgrade when needed
- **Monitor usage**: Track resource consumption
- **Optimize code**: Reduce unnecessary API calls

## Next Steps

Now that your application is deployed:

1. **Share your app**: Give users your frontend URL
2. **Set up monitoring**: Configure uptime monitoring (UptimeRobot, Pingdom)
3. **Plan scaling**: Monitor usage and plan upgrades
4. **Add features**: Continue development with automatic deployments
5. **Gather feedback**: Collect user feedback for improvements

## Support Resources

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **Render Community**: [community.render.com](https://community.render.com)
- **MongoDB Atlas Docs**: [docs.atlas.mongodb.com](https://www.mongodb.com/docs/atlas/)
- **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

## Deployment Summary

**Your URLs:**
- **Frontend**: `https://smart-ml-frontend.onrender.com`
- **Backend**: `https://smart-ml-backend.onrender.com`
- **Health Check**: `https://smart-ml-backend.onrender.com/health`

**Total Deployment Time:**
- MongoDB setup: 10 minutes
- GitHub preparation: 5 minutes
- Render Blueprint deployment: 15 minutes
- Configuration: 10 minutes
- Testing: 10 minutes
- **Total: ~50 minutes**

**Monthly Cost:**
- Free tier: $0/month
- With backend upgrade: $7/month
- With custom domain: $0 extra

---

Congratulations! Your Smart ML Assistant is now live and accessible to users worldwide.
