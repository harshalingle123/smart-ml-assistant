# 📘 Subscription API Reference

Quick reference for all subscription-related API endpoints.

---

## 🔑 Authentication

All endpoints require JWT authentication:

```bash
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## 📋 Endpoints

### 1. Get All Plans

```http
GET /api/subscriptions/plans
```

**Auth**: Not required (public)

**Response**:
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "plan": "free",
    "name": "Free Plan",
    "description": "Get started with basic AutoML features",
    "price_monthly": 0,
    "currency": "INR",
    "api_hits_per_month": 500,
    "model_generation_per_day": 3,
    "dataset_size_mb": 50,
    "azure_storage_gb": 0.1,
    "training_time_minutes_per_model": 5,
    "concurrent_trainings": 1,
    "features": ["Basic AutoML training", "..."],
    "priority_support": false,
    "razorpay_plan_id": null,
    "is_active": true
  }
]
```

**Example**:
```bash
curl http://localhost:8000/api/subscriptions/plans
```

---

### 2. Get Current Subscription

```http
GET /api/subscriptions/current
```

**Auth**: Required

**Response**:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f191e810c19729de860ea",
  "plan": "pro",
  "provider": "razorpay",
  "status": "active",
  "period_start": "2025-01-15T00:00:00Z",
  "period_end": "2025-02-14T00:00:00Z",
  "cancel_at_period_end": false,
  "canceled_at": null,
  "amount": 499,
  "currency": "INR",
  "last_payment_at": "2025-01-15T10:30:00Z",
  "next_billing_date": "2025-02-14T00:00:00Z",
  "razorpay_subscription_id": "sub_abc123"
}
```

**Error** (No subscription):
```json
{
  "detail": "No active paid subscription found. User is on free plan."
}
```

**Example**:
```bash
curl http://localhost:8000/api/subscriptions/current \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3. Create Order (Initiate Payment)

```http
POST /api/subscriptions/create-order
```

**Auth**: Required

**Request**:
```json
{
  "plan": "pro"
}
```

**Response**:
```json
{
  "order_id": "order_abc123xyz",
  "amount": 499,
  "currency": "INR",
  "key_id": "rzp_test_***",
  "plan": "pro",
  "plan_name": "Pro Plan"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/subscriptions/create-order \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan": "pro"}'
```

**Frontend Usage**:
```javascript
// After getting order details
const options = {
  key: response.key_id,
  amount: response.amount * 100,
  currency: response.currency,
  order_id: response.order_id,
  handler: function(payment) {
    // Verify payment
    verifyPayment(payment);
  }
};

const razorpay = new Razorpay(options);
razorpay.open();
```

---

### 4. Verify Payment

```http
POST /api/subscriptions/verify-payment
```

**Auth**: Required

**Request**:
```json
{
  "razorpay_order_id": "order_abc123",
  "razorpay_payment_id": "pay_xyz456",
  "razorpay_signature": "signature_hash",
  "plan": "pro"
}
```

**Response**:
```json
{
  "success": true,
  "subscription_id": "507f1f77bcf86cd799439011",
  "plan": "pro",
  "message": "Subscription activated successfully"
}
```

**Error Response**:
```json
{
  "detail": "Invalid payment signature"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/subscriptions/verify-payment \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "razorpay_order_id": "order_abc123",
    "razorpay_payment_id": "pay_xyz456",
    "razorpay_signature": "signature_hash",
    "plan": "pro"
  }'
```

---

### 5. Get Usage Statistics

```http
GET /api/subscriptions/usage
```

**Auth**: Required

**Response**:
```json
{
  "user_id": "507f191e810c19729de860ea",
  "subscription_id": "507f1f77bcf86cd799439011",
  "plan": "pro",
  "api_hits_used": 234,
  "api_hits_limit": 5000,
  "models_trained_today": 8,
  "models_limit_per_day": 25,
  "azure_storage_used_mb": 1250.5,
  "azure_storage_limit_gb": 5,
  "billing_cycle_start": "2025-01-15T00:00:00Z",
  "billing_cycle_end": "2025-02-14T00:00:00Z",
  "usage_percentage": {
    "api_hits": 4.68,
    "models": 32.0,
    "storage": 24.41
  }
}
```

**Example**:
```bash
curl http://localhost:8000/api/subscriptions/usage \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 6. Cancel Subscription

```http
POST /api/subscriptions/cancel
```

**Auth**: Required

**Request**:
```json
{
  "cancel_at_period_end": true,
  "reason": "Too expensive"
}
```

**Response** (Cancel at period end):
```json
{
  "success": true,
  "message": "Subscription will be canceled at period end",
  "cancel_at_period_end": true,
  "period_end": "2025-02-14T00:00:00Z"
}
```

**Response** (Cancel immediately):
```json
{
  "success": true,
  "message": "Subscription canceled",
  "cancel_at_period_end": false,
  "period_end": "2025-01-20T10:30:00Z"
}
```

**Example**:
```bash
# Cancel at period end
curl -X POST http://localhost:8000/api/subscriptions/cancel \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cancel_at_period_end": true}'

# Cancel immediately
curl -X POST http://localhost:8000/api/subscriptions/cancel \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cancel_at_period_end": false}'
```

---

### 7. Get Payment History

```http
GET /api/subscriptions/payment-history
```

**Auth**: Required

**Response**:
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "amount": 499,
    "currency": "INR",
    "status": "success",
    "payment_method": "upi",
    "razorpay_payment_id": "pay_abc123",
    "description": "Subscription: Pro Plan",
    "created_at": "2025-01-15T10:30:00Z"
  },
  {
    "id": "507f1f77bcf86cd799439012",
    "amount": 499,
    "currency": "INR",
    "status": "failed",
    "payment_method": "card",
    "razorpay_payment_id": "pay_xyz456",
    "description": "Subscription: Pro Plan",
    "created_at": "2025-01-10T14:20:00Z"
  }
]
```

**Example**:
```bash
curl http://localhost:8000/api/subscriptions/payment-history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 8. Webhook Handler (Razorpay)

```http
POST /api/subscriptions/webhook
```

**Auth**: Signature verification (not JWT)

**Headers**:
```
X-Razorpay-Signature: webhook_signature_hash
```

**Request** (example for payment.captured):
```json
{
  "event": "payment.captured",
  "payload": {
    "payment": {
      "entity": {
        "id": "pay_abc123",
        "amount": 49900,
        "currency": "INR",
        "status": "captured",
        "order_id": "order_xyz456",
        "method": "upi"
      }
    }
  }
}
```

**Response**:
```json
{
  "success": true
}
```

**Events Supported**:
- `payment.captured` - Payment successful
- `payment.failed` - Payment failed
- `subscription.charged` - Subscription renewed
- `subscription.cancelled` - Subscription canceled

**Example** (from Razorpay):
```bash
# Razorpay automatically sends webhooks
# No manual curl needed
```

---

## 🚨 Error Responses

### 400 - Bad Request
```json
{
  "detail": "Invalid plan. Choose 'pro' or 'advanced'."
}
```

### 401 - Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 - Not Found
```json
{
  "detail": "No active paid subscription found. User is on free plan."
}
```

### 429 - Limit Exceeded
```json
{
  "error": "Model training limit exceeded",
  "message": "You have reached your daily limit of 3 model trainings.",
  "current_plan": "free",
  "upgrade_required": true,
  "reset_time": "Limit resets at midnight UTC"
}
```

### 500 - Internal Server Error
```json
{
  "detail": "Payment order creation failed: Insufficient balance"
}
```

---

## 🧪 Testing with cURL

### Complete Flow

#### 1. Register User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "test123"
  }'
```

#### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }'

# Save the token from response
TOKEN="eyJhbGciOiJIUzI1NiIs..."
```

#### 3. Check Available Plans
```bash
curl http://localhost:8000/api/subscriptions/plans
```

#### 4. Create Payment Order
```bash
curl -X POST http://localhost:8000/api/subscriptions/create-order \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan": "pro"}'
```

#### 5. Complete Payment (use frontend)
```
Use Razorpay checkout with test card:
Card: 4111 1111 1111 1111
CVV: 123
Expiry: Any future date
```

#### 6. Check Usage
```bash
curl http://localhost:8000/api/subscriptions/usage \
  -H "Authorization: Bearer $TOKEN"
```

#### 7. Check Payment History
```bash
curl http://localhost:8000/api/subscriptions/payment-history \
  -H "Authorization: Bearer $TOKEN"
```

#### 8. Cancel Subscription
```bash
curl -X POST http://localhost:8000/api/subscriptions/cancel \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cancel_at_period_end": true}'
```

---

## 📊 Response Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 201 | Created | Subscription created |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Action not allowed |
| 404 | Not Found | Resource not found |
| 413 | Payload Too Large | Dataset size exceeded |
| 429 | Too Many Requests | Usage limit exceeded |
| 500 | Internal Server Error | Server error |
| 507 | Insufficient Storage | Storage limit exceeded |

---

## 🔒 Security Notes

### Request Signing
All payment verifications use HMAC SHA256:

```python
message = f"{order_id}|{payment_id}"
expected_signature = hmac.new(
    KEY_SECRET.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()
```

### Webhook Verification
```python
expected_signature = hmac.new(
    WEBHOOK_SECRET.encode(),
    request_body.encode(),
    hashlib.sha256
).hexdigest()

if not hmac.compare_digest(expected_signature, received_signature):
    raise HTTPException(400, "Invalid signature")
```

### Rate Limiting
- Authentication endpoints: 5 req/min per IP
- Payment endpoints: 10 req/min per user
- Webhook: 100 req/min (from Razorpay)

---

## 💡 Integration Examples

### Python (requests)
```python
import requests

TOKEN = "your_jwt_token"
BASE_URL = "http://localhost:8000"

# Get plans
response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
plans = response.json()

# Create order
response = requests.post(
    f"{BASE_URL}/api/subscriptions/create-order",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"plan": "pro"}
)
order = response.json()

# Get usage
response = requests.get(
    f"{BASE_URL}/api/subscriptions/usage",
    headers={"Authorization": f"Bearer {TOKEN}"}
)
usage = response.json()
print(f"API hits used: {usage['api_hits_used']}/{usage['api_hits_limit']}")
```

### JavaScript (axios)
```javascript
const axios = require('axios');

const TOKEN = 'your_jwt_token';
const BASE_URL = 'http://localhost:8000';

const headers = { Authorization: `Bearer ${TOKEN}` };

// Get plans
const plans = await axios.get(`${BASE_URL}/api/subscriptions/plans`);
console.log(plans.data);

// Create order
const order = await axios.post(
  `${BASE_URL}/api/subscriptions/create-order`,
  { plan: 'pro' },
  { headers }
);
console.log('Order ID:', order.data.order_id);

// Get usage
const usage = await axios.get(
  `${BASE_URL}/api/subscriptions/usage`,
  { headers }
);
console.log('Usage:', usage.data);
```

---

## 📝 Notes

- All dates in ISO 8601 format (UTC)
- All amounts in base currency units (INR, not paise)
- IDs are MongoDB ObjectId strings
- Pagination not implemented (returns all records)
- Caching: Plans cached for 5 minutes

---

**API Documentation Version**: 1.0.0
**Last Updated**: January 2025
**Base URL**: `http://localhost:8000` (development)
**Production URL**: `https://your-domain.com`
