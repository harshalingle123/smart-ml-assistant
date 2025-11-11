# Pre-Deployment Checklist

Before deploying to Render, make sure you complete these steps:

## 1. MongoDB Atlas Setup ✓
- [ ] Create MongoDB Atlas account
- [ ] Create free M0 cluster
- [ ] Create database user with read/write permissions
- [ ] Whitelist all IPs (0.0.0.0/0)
- [ ] Get connection string
- [ ] Test connection string locally

## 2. GitHub Repository ✓
- [ ] Initialize git repository
- [ ] Add all files to git
- [ ] Create repository on GitHub
- [ ] Push code to GitHub
- [ ] Verify all files are pushed

## 3. Environment Variables Preparation ✓
Prepare these values before deployment:

### Required:
- [ ] `MONGO_URI` - Your MongoDB Atlas connection string
- [ ] `SECRET_KEY` - Generate using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] `ALGORITHM` - Use: `HS256`
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` - Use: `30`
- [ ] `ENVIRONMENT` - Use: `production`

### Optional (for Google OAuth):
- [ ] `GOOGLE_CLIENT_ID`
- [ ] `GOOGLE_CLIENT_SECRET`
- [ ] `GOOGLE_REDIRECT_URI`

## 4. Code Review ✓
- [x] API URL is configurable (uses VITE_API_URL)
- [x] CORS settings are ready for production
- [x] No hardcoded secrets in code
- [x] .env files are in .gitignore
- [x] Build commands are correct

## 5. Render Account ✓
- [ ] Create Render account at render.com
- [ ] Connect GitHub account to Render
- [ ] Verify email

## 6. Deployment Steps

### Backend Deployment:
1. [ ] Create Web Service on Render
2. [ ] Connect GitHub repository
3. [ ] Configure root directory: `backend`
4. [ ] Set build command: `pip install -r requirements.txt`
5. [ ] Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. [ ] Add all environment variables
7. [ ] Deploy and wait for completion
8. [ ] Test health endpoint: `https://your-backend.onrender.com/health`
9. [ ] Save backend URL

### Frontend Deployment:
1. [ ] Create Static Site on Render
2. [ ] Connect same GitHub repository
3. [ ] Configure root directory: `frontend`
4. [ ] Set build command: `npm install && npm run build`
5. [ ] Set publish directory: `dist/public`
6. [ ] Add environment variable: `VITE_API_URL` = your backend URL
7. [ ] Deploy and wait for completion
8. [ ] Save frontend URL

### Final Configuration:
1. [ ] Update backend `CORS_ORIGINS` with frontend URL
2. [ ] Wait for backend to redeploy
3. [ ] Test frontend at your-frontend.onrender.com
4. [ ] Test all features (login, register, chat, datasets)

## 7. Post-Deployment Testing ✓
- [ ] Can access frontend
- [ ] Can register new account
- [ ] Can login
- [ ] Can create chat
- [ ] Can upload dataset
- [ ] Can fine-tune model
- [ ] Google OAuth works (if configured)

## 8. Optional Enhancements
- [ ] Set up custom domain
- [ ] Configure monitoring alerts
- [ ] Set up automatic deployments
- [ ] Add health check monitoring
- [ ] Consider upgrading backend ($7/month removes cold starts)

## Quick Command Reference

### Generate SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Test Backend Locally:
```bash
cd backend
uvicorn app.main:app --reload
```

### Test Frontend Locally:
```bash
cd frontend
npm run dev
```

### Build Frontend:
```bash
cd frontend
npm run build
```

## Troubleshooting Quick Fixes

### Backend won't start:
- Check logs in Render dashboard
- Verify MONGO_URI is correct
- Ensure all required env vars are set

### Frontend can't connect:
- Verify VITE_API_URL is correct
- Check CORS_ORIGINS includes frontend URL
- Ensure backend is running

### Database connection fails:
- Check MongoDB Atlas IP whitelist
- Verify connection string format
- Ensure database user has permissions

## Estimated Deployment Time
- MongoDB setup: 10 minutes
- GitHub setup: 5 minutes
- Backend deployment: 10 minutes
- Frontend deployment: 10 minutes
- Testing: 10 minutes
**Total: ~45 minutes**

---

Follow the detailed instructions in `DEPLOYMENT_GUIDE.md` for step-by-step guidance.
