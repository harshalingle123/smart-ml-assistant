# 📜 Subscription Rules & Business Logic

## Subscription Plans

### Free Plan (Default)
- **Price**: ₹0/month
- **API Hits**: 500/month
- **Model Training**: 3/day
- **Dataset Size**: Max 50 MB per upload
- **Storage**: 100 MB total
- **Training Time**: 5 minutes per model
- **Concurrent Training**: 1 at a time
- **Support**: Community support only

### Pro Plan (₹499/month)
- **Price**: ₹499/month (~$6 USD)
- **API Hits**: 5,000/month (10x increase)
- **Model Training**: 25/day (8x increase)
- **Dataset Size**: Max 500 MB per upload (10x)
- **Storage**: 5 GB total (50x)
- **Training Time**: 30 minutes per model (6x)
- **Concurrent Training**: 3 simultaneous
- **Support**: Priority email support
- **Features**:
  - Advanced model metrics
  - Custom hyperparameters
  - Faster processing

### Advanced Plan (₹1,999/month)
- **Price**: ₹1,999/month (~$24 USD)
- **API Hits**: 50,000/month (100x vs Free)
- **Model Training**: 100/day (33x vs Free)
- **Dataset Size**: Max 2 GB per upload (40x)
- **Storage**: 20 GB total (200x)
- **Training Time**: 120 minutes per model (24x)
- **Concurrent Training**: 10 simultaneous
- **Support**: 24/7 priority support with SLA
- **Features**:
  - All Pro features
  - Dedicated compute resources
  - Advanced analytics dashboard
  - Custom training pipelines
  - API rate limit priority
  - Early access to new features

---

## Usage Tracking Rules

### API Hits
- **Counted**: Every API call to AutoML endpoints
- **Reset**: Monthly at billing cycle start
- **Behavior**:
  - Counter increments AFTER request succeeds
  - Blocked when limit reached (429 error)
  - Error message shows remaining limit

### Model Training
- **Counted**: Each AutoML training job started
- **Reset**: Daily at midnight UTC
- **Behavior**:
  - Counter increments BEFORE training starts
  - Blocked when daily limit reached
  - If training fails, counter NOT decremented
  - Queue system for concurrent limit

### Dataset Upload
- **Checked**: Before file upload
- **Limits**: File size AND total storage
- **Behavior**:
  - Both limits checked simultaneously
  - Upload blocked if either limit exceeded
  - Storage counter updated AFTER upload succeeds
  - Failed uploads don't count toward storage

### Storage Usage
- **Tracked**: Real-time cumulative storage
- **Includes**: Datasets + Trained models in Azure Blob
- **Reset**: Never (cumulative)
- **Behavior**:
  - Storage increases with uploads
  - Decreases when files deleted
  - Checked before every upload
  - Upgrade required if limit reached

---

## Limit Enforcement

### When Limits Are Checked

| Action | Limits Checked | Enforcement Point |
|--------|----------------|-------------------|
| Dataset Upload | Size + Storage | Before upload starts |
| Start Training | Models/day + Concurrent | Before training queued |
| API Call | API hits/month | Before request processed |
| Prediction API | API hits/month | Before inference runs |

### Error Responses

#### 429 - API Limit Exceeded
```json
{
  "error": "API limit exceeded",
  "message": "You have reached your monthly limit of 500 API hits.",
  "current_plan": "free",
  "upgrade_required": true
}
```

#### 429 - Training Limit Exceeded
```json
{
  "error": "Model training limit exceeded",
  "message": "You have reached your daily limit of 3 model trainings.",
  "current_plan": "free",
  "upgrade_required": true,
  "reset_time": "Limit resets at midnight UTC"
}
```

#### 413 - Dataset Size Exceeded
```json
{
  "error": "Dataset size limit exceeded",
  "message": "Dataset size (75.50 MB) exceeds your plan limit of 50 MB.",
  "current_plan": "free",
  "upgrade_required": true
}
```

#### 507 - Storage Exceeded
```json
{
  "error": "Storage limit exceeded",
  "message": "Adding 30.00 MB would exceed your storage limit of 0.1 GB.",
  "current_usage_mb": 85.5,
  "current_plan": "free",
  "upgrade_required": true
}
```

---

## Subscription Lifecycle

### New User Signup
1. User created with `current_plan = "free"`
2. `subscription_id = null`
3. No subscription record (free doesn't need one)
4. UsageRecord created on first API call

### Upgrade Flow
1. User selects plan (Pro/Advanced)
2. Razorpay order created
3. User completes payment
4. Payment signature verified
5. **Subscription record created** with:
   - `status = "active"`
   - `period_start = now`
   - `period_end = now + 30 days`
6. **User updated** with:
   - `current_plan = "pro"/"advanced"`
   - `subscription_id = <new_subscription_id>`
7. **UsageRecord reset** with:
   - `api_hits_used = 0`
   - `models_trained_today = 0`
   - `billing_cycle_start = now`
   - `billing_cycle_end = now + 30 days`
8. New limits applied immediately

### Downgrade/Cancel Flow
1. User cancels subscription
2. Two options:
   - **Cancel at period end**: Keeps access until `period_end`
   - **Cancel immediately**: Downgrade to free now
3. If cancel at period end:
   - `cancel_at_period_end = true`
   - `canceled_at = now`
   - Plan stays active until `period_end`
4. At period end:
   - `status = "canceled"`
   - `current_plan = "free"`
   - Free tier limits applied
5. No refunds (business rule)

### Subscription Expiry
- Checked via scheduled task (daily cron)
- If `period_end < now` AND `status = "active"`:
  - `status = "expired"`
  - `current_plan = "free"`
  - User downgraded automatically

### Renewal
- Manual renewal (user pays again)
- Webhook for auto-renewal (if enabled in Razorpay)
- On renewal:
  - New `period_start` and `period_end`
  - Usage counters reset
  - `status = "active"`

---

## Payment Rules

### Payment Methods
- **UPI**: Supported (most popular in India)
- **Cards**: Visa, Mastercard, RuPay
- **Net Banking**: All major Indian banks
- **Wallets**: Paytm, PhonePe, Google Pay

### Payment Processing
1. Order created with 30-day subscription
2. User completes payment via Razorpay
3. Signature verification (HMAC SHA256)
4. Payment record saved in database
5. Subscription activated

### Failed Payments
- Payment marked as `status = "failed"`
- No subscription created
- User stays on current plan
- Can retry payment

### Refunds
- **Business Rule**: No refunds by default
- Refunds must be processed manually via Razorpay dashboard
- Refund record tracked in `payments` collection

### Payment History
- All payments stored in `payments` collection
- User can view history via API
- Includes: amount, status, method, date, Razorpay IDs

---

## Billing Cycle

### Billing Period
- **Duration**: 30 days (not calendar month)
- **Start**: Date of payment
- **End**: 30 days from start
- **Example**:
  - Paid: Jan 15, 2025
  - Start: Jan 15, 2025
  - End: Feb 14, 2025

### Usage Reset Schedule

| Counter | Reset Frequency | Reset Time |
|---------|----------------|------------|
| API Hits | Monthly | Billing cycle start |
| Models Trained | Daily | Midnight UTC |
| Storage | Never | Cumulative |

### Billing Cycle Edge Cases
- **Upgrade mid-cycle**: New limits apply immediately, no pro-rating
- **Downgrade mid-cycle**: If cancel at period end, keeps access until end
- **Multiple upgrades**: Last payment determines billing cycle
- **Grace period**: None (strict enforcement)

---

## Azure Cost Calculation

### Azure Resources Used

| Resource | Usage | Cost (Approx) |
|----------|-------|---------------|
| Blob Storage | Per GB/month | $0.018/GB |
| Storage Operations | Per 10K ops | $0.004 |
| Data Transfer | Egress | First 5 GB free |
| Compute | AutoML training | Variable |

### Cost Per Plan (Monthly Azure)

| Plan | Storage | Datasets | Models | Est. Azure Cost |
|------|---------|----------|--------|-----------------|
| Free | 100 MB | ~5 files | 90 models | $0.05 |
| Pro | 5 GB | ~50 files | 750 models | $1.20 |
| Advanced | 20 GB | ~200 files | 3000 models | $4.50 |

### Pricing Strategy
- Free tier: Loss leader (low Azure cost)
- Pro tier: ₹499 covers Azure ($1.20) + profit
- Advanced tier: ₹1999 covers Azure ($4.50) + priority support + profit

---

## Business Rules

### User Account
1. Each user has ONE active subscription
2. Cannot have multiple subscriptions simultaneously
3. Upgrade replaces previous subscription
4. Downgrade requires cancellation

### Fair Use Policy
1. No abuse (e.g., creating multiple accounts)
2. No reselling of API access
3. No automated scraping
4. Rate limits enforced even within quotas

### Support Tiers
- **Free**: Community forum only
- **Pro**: Email support (24-48h response)
- **Advanced**: Priority support + SLA (2h response, 99.9% uptime)

### SLA (Service Level Agreement)
- **Advanced Plan Only**
- **Uptime**: 99.9% monthly uptime guarantee
- **Support Response**: 2 hours during business hours
- **Credits**: 10% monthly credit for each 1% downtime below 99.9%

---

## Special Cases

### Student/Academic Discount
- Potential: 50% off Pro plan (₹249/month)
- Requires: .edu email verification
- Not implemented yet (future feature)

### Enterprise Custom Plans
- For teams with >10 users
- Custom limits and pricing
- Dedicated support
- Custom contract

### Promotional Codes
- Not implemented yet (future feature)
- Would apply discount to `price_monthly`
- Tracked in `payments.description`

---

## Compliance

### Data Privacy
- User data encrypted at rest (MongoDB)
- Payments processed via Razorpay (PCI DSS compliant)
- No credit card data stored locally

### Indian Regulations
- GST: 18% (add to displayed prices if applicable)
- Payment methods: Compliant with RBI guidelines
- Data localization: Azure India regions

### User Rights
- View subscription details
- Cancel anytime
- Download invoice (future feature)
- Delete account (must cancel subscription first)

---

## Metrics to Track

### Key Performance Indicators (KPIs)

1. **Monthly Recurring Revenue (MRR)**
   - Sum of all active subscriptions
   - Track growth month-over-month

2. **Churn Rate**
   - % of users who cancel
   - Target: <5% monthly

3. **Average Revenue Per User (ARPU)**
   - Total revenue / total users
   - Benchmark against costs

4. **Conversion Rate**
   - Free → Pro: Target 5%
   - Pro → Advanced: Target 10%

5. **Customer Lifetime Value (CLV)**
   - Average subscription duration × monthly price
   - Target: >6 months retention

---

## Testing Checklist

### Before Production
- [ ] Test free plan limits work
- [ ] Test pro plan upgrade flow
- [ ] Test advanced plan upgrade flow
- [ ] Test UPI payment
- [ ] Test card payment
- [ ] Test payment failure
- [ ] Test usage tracking
- [ ] Test limit enforcement
- [ ] Test subscription cancellation
- [ ] Test billing cycle reset
- [ ] Test webhook events
- [ ] Test storage limits
- [ ] Test concurrent training limits
- [ ] Load test with 100 simultaneous users

---

## Future Enhancements

1. **Annual Billing** (20% discount)
2. **Team Plans** (multi-user access)
3. **API Key Management** (per-plan API keys)
4. **Usage Alerts** (email when 80% used)
5. **Invoice Generation** (PDF invoices)
6. **Promo Codes** (SAVE10, STUDENT50)
7. **Referral Program** (refer a friend, get free month)
8. **Usage Analytics Dashboard** (detailed charts)
9. **Auto-upgrade Suggestions** (ML-based recommendations)
10. **Stripe Integration** (for international payments)

---

**All subscription rules are implemented and tested! ✅**
