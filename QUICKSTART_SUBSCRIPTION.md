# 🚀 Quick Start: Subscription System

## Get Your Subscription System Running in 10 Minutes

---

## Step 1: Install Razorpay (30 seconds)

```bash
cd backend
pip install razorpay
```

---

## Step 2: Get Razorpay Keys (2 minutes)

1. Go to https://dashboard.razorpay.com/signup
2. Sign up (use Google for fastest signup)
3. After login, go to **Settings** → **API Keys**
4. Click **Generate Test Keys**
5. Copy:
   - Key ID (starts with `rzp_test_`)
   - Key Secret

---

## Step 3: Update .env File (1 minute)

Open `backend/.env` and add:

```env
# Add these lines at the end
RAZORPAY_KEY_ID=rzp_test_YOUR_KEY_ID_HERE
RAZORPAY_KEY_SECRET=YOUR_KEY_SECRET_HERE
RAZORPAY_WEBHOOK_SECRET=optional_for_now
```

Save the file.

---

## Step 4: Initialize Database (30 seconds)

```bash
cd backend
python -m app.scripts.init_subscription_plans
```

You should see:
```
✓ Created Free Plan
✓ Created Pro Plan
✓ Created Advanced Plan
✅ Subscription plans initialized successfully!
✅ Database indexes created!
```

---

## Step 5: Start Backend (10 seconds)

```bash
uvicorn app.main:app --reload
```

Server should start on http://localhost:8000

---

## Step 6: Test API (1 minute)

Open browser and visit:
```
http://localhost:8000/api/subscriptions/plans
```

You should see 3 plans with details:
```json
[
  {
    "plan": "free",
    "name": "Free Plan",
    "price_monthly": 0,
    ...
  },
  {
    "plan": "pro",
    "name": "Pro Plan",
    "price_monthly": 499,
    ...
  },
  {
    "plan": "advanced",
    "name": "Advanced Plan",
    "price_monthly": 1999,
    ...
  }
]
```

---

## Step 7: Test Frontend (2 minutes)

### Add Razorpay Script

Add to `frontend/client/index.html`:

```html
<head>
  <!-- Add this line -->
  <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
</head>
```

### Create a Test Page

Create `frontend/client/src/pages/TestSubscription.tsx`:

```tsx
import SubscriptionPlans from '@/components/SubscriptionPlans';
import UsageDashboard from '@/components/UsageDashboard';

export default function TestSubscription() {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Subscription Test</h1>

      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Available Plans</h2>
        <SubscriptionPlans currentPlan="free" />
      </div>

      <div>
        <h2 className="text-2xl font-semibold mb-4">Usage Dashboard</h2>
        <UsageDashboard />
      </div>
    </div>
  );
}
```

### Add Route

Update your router to include this page.

---

## Step 8: Test Payment (3 minutes)

### Login First

1. Start frontend: `npm run dev`
2. Login to your app
3. Navigate to subscription/billing page

### Test Payment

1. Click "Upgrade Now" on Pro plan
2. Razorpay modal opens
3. Use test card:
   - **Card**: 4111 1111 1111 1111
   - **CVV**: 123
   - **Expiry**: Any future date
   - **Name**: Any name

4. Or test with UPI:
   - UPI ID: `success@razorpay`

5. Complete payment
6. You should see success message
7. Page reloads with Pro plan active

---

## Step 9: Verify Upgrade

Check MongoDB:

```bash
# Connect to your MongoDB
# Check subscriptions collection
db.subscriptions.find({}).pretty()

# Check users collection
db.users.find({}, {email: 1, current_plan: 1, subscription_id: 1})

# Check usage_records
db.usage_records.find({}).pretty()

# Check payments
db.payments.find({}).pretty()
```

You should see:
- ✅ Subscription record created
- ✅ User's `current_plan` = "pro"
- ✅ UsageRecord created/reset
- ✅ Payment recorded

---

## Step 10: Test Limits

### Test Model Training Limit

```bash
# Login and get your token
TOKEN="your_jwt_token"

# Try training 4 models (pro limit is 25/day)
# This should succeed 25 times, fail on 26th

for i in {1..26}; do
  echo "Training attempt $i"
  curl -X POST "http://localhost:8000/api/automl/train/DATASET_ID?chat_id=CHAT_ID" \
    -H "Authorization: Bearer $TOKEN"
done
```

26th attempt should return:
```json
{
  "error": "Model training limit exceeded",
  "message": "You have reached your daily limit of 25 model trainings."
}
```

---

## ✅ Success Checklist

- [x] Razorpay installed
- [x] API keys configured
- [x] Database plans initialized
- [x] Backend running
- [x] API endpoints responding
- [x] Frontend components working
- [x] Test payment successful
- [x] User upgraded to Pro
- [x] Usage limits enforced

---

## 🎯 What You Now Have

### Backend ✅
- ✅ Complete subscription management system
- ✅ Razorpay payment integration (UPI, Cards, NetBanking)
- ✅ Usage tracking and limits enforcement
- ✅ Webhook support for auto-renewal
- ✅ Payment verification and security

### Frontend ✅
- ✅ Beautiful subscription plans UI
- ✅ Real-time usage dashboard
- ✅ Razorpay checkout integration
- ✅ Upgrade/downgrade flow

### Database ✅
- ✅ 3 plans (Free, Pro, Advanced)
- ✅ Subscription tracking
- ✅ Usage monitoring
- ✅ Payment history

---

## 🧪 Testing Scenarios

### Scenario 1: Free User Tests Limits
```bash
# As free user, try:
1. Upload 51 MB dataset → Should fail (limit: 50 MB)
2. Train 4 models in one day → 4th should fail (limit: 3/day)
3. Make 501 API calls → 501st should fail (limit: 500/month)
```

### Scenario 2: Upgrade to Pro
```bash
1. Click "Upgrade Now" on Pro plan
2. Complete test payment
3. Verify new limits:
   - Upload 500 MB dataset → Should work
   - Train 25 models/day → Should work
   - Make 5000 API calls/month → Should work
```

### Scenario 3: Cancel Subscription
```bash
# Use API or UI to cancel
POST /api/subscriptions/cancel
{
  "cancel_at_period_end": true
}

# User keeps Pro access until period ends
# Then automatically downgraded to Free
```

---

## 📊 Monitor Your System

### Real-time Monitoring

```bash
# Watch MongoDB for new subscriptions
watch -n 2 'mongo YOUR_DB_URI --eval "db.subscriptions.find().count()"'

# Watch payments
watch -n 2 'mongo YOUR_DB_URI --eval "db.payments.find({status: \"success\"}).count()"'

# Watch usage
watch -n 5 'mongo YOUR_DB_URI --eval "db.usage_records.find({}, {api_hits_used: 1, models_trained_today: 1})"'
```

---

## 🔥 Common Issues

### Issue: Razorpay modal doesn't open
**Fix**: Check if Razorpay script is loaded:
```html
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
```

### Issue: Payment succeeds but subscription not created
**Fix**: Check backend logs for signature verification errors

### Issue: "Razorpay not configured"
**Fix**: Verify `.env` has correct `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`

### Issue: Limits not enforced
**Fix**: Check if middleware is imported in routes:
```python
from app.middleware.subscription_middleware import subscription_limits
await subscription_limits.check_model_training_limit(user_id)
```

---

## 📈 Next Steps

1. **Test thoroughly** with all 3 plans
2. **Add custom branding** to Razorpay checkout
3. **Set up webhooks** for auto-renewal
4. **Monitor usage patterns** and adjust limits
5. **Get live keys** from Razorpay for production

---

## 🎉 You're Done!

Your subscription system is now:
- ✅ Fully functional
- ✅ Secure (signature verification)
- ✅ Production-ready
- ✅ UPI, Cards, NetBanking supported
- ✅ Usage limits enforced
- ✅ Real-time tracking

**Time to go live!** 🚀

---

## 💡 Pro Tips

1. **Test Mode vs Live Mode**
   - Always test with `rzp_test_` keys first
   - Switch to `rzp_live_` only when ready

2. **Webhook Testing**
   - Use Razorpay webhook simulator
   - Or use ngrok for local testing

3. **User Experience**
   - Show usage warnings at 80% of limit
   - Offer upgrade CTA at 90% of limit
   - Email users when limits exceeded

4. **Pricing Strategy**
   - Start with current prices (₹499, ₹1999)
   - Adjust based on usage patterns
   - Offer annual discounts later

---

## 📞 Support

- **Razorpay Docs**: https://razorpay.com/docs/
- **Razorpay Support**: support@razorpay.com
- **Test Cards**: https://razorpay.com/docs/payments/payments/test-card-details/

---

**Happy Coding! 🎊**
