# Direct Access API - Quick Start Guide

## Installation

1. Install the new dependency:
```bash
cd backend
pip install vaderSentiment==3.3.2
```

2. Start the server:
```bash
cd backend
uvicorn app.main:app --reload
```

## Quick Test Flow

### Step 1: Login and Get JWT Token

```bash
# Register (if needed)
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "password123"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Save the access_token from response
```

### Step 2: Request Direct API Access

```bash
curl -X POST http://localhost:8000/api/direct-access \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "sentiment",
    "subtask": "reviews",
    "usage": "testing",
    "language": "en",
    "priority": "speed"
  }'

# Save the api_key from response (starts with sk_live_)
```

### Step 3: Make Your First Prediction

```bash
curl -X POST http://localhost:8000/v1/sentiment/vader \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This product is absolutely amazing! I love it!"
  }'
```

Expected response:
```json
{
  "text": "This product is absolutely amazing! I love it!",
  "sentiment": {
    "label": "POSITIVE",
    "compound": 0.9468,
    "pos": 0.623,
    "neu": 0.377,
    "neg": 0.0
  },
  "confidence": 0.95,
  "latency_ms": 7,
  "timestamp": "2025-11-14T12:30:00Z",
  "request_id": "req_abc123",
  "usage": {
    "requests_used": 1,
    "requests_remaining": 9999,
    "reset_date": "2025-12-01"
  }
}
```

### Step 4: Try Batch Predictions

```bash
curl -X POST http://localhost:8000/v1/sentiment/vader/batch \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Great product!",
      "Terrible quality!",
      "It is okay."
    ]
  }'
```

### Step 5: Check Your Usage

```bash
curl -X GET "http://localhost:8000/api/dashboard/usage?timeframe=24h" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Python Testing Script

Run the comprehensive test suite:

```bash
cd backend
python test_direct_access.py
```

This will test:
- Listing available models
- Requesting API access
- Making single predictions
- Batch predictions
- Rate limiting
- Usage statistics
- Cost calculations
- Error handling

## Available Endpoints

### User Authenticated (JWT Token)

1. **POST /api/direct-access** - Request API access
2. **GET /api/direct-access/models** - List available models
3. **GET /api/direct-access/keys** - List your API keys
4. **DELETE /api/direct-access/keys/{key_id}** - Revoke API key
5. **GET /api/dashboard/usage** - Usage statistics
6. **GET /api/dashboard/costs** - Cost breakdown
7. **GET /api/dashboard/summary** - Dashboard summary
8. **POST /api/dashboard/alerts** - Configure alerts
9. **GET /api/dashboard/alerts** - List alerts
10. **DELETE /api/dashboard/alerts/{alert_id}** - Delete alert

### Model API (API Key Authentication)

1. **POST /v1/sentiment/vader** - VADER prediction
2. **POST /v1/sentiment/vader/batch** - VADER batch prediction
3. **POST /v1/sentiment/distilbert** - DistilBERT prediction (mock)
4. **POST /v1/sentiment/roberta** - RoBERTa prediction (mock)

## Common Use Cases

### Use Case 1: Analyze Customer Reviews

```python
import requests

API_KEY = "sk_live_your_key_here"
reviews = [
    "Excellent product, highly recommend!",
    "Product broke after one week, waste of money",
    "It's okay for the price",
    "Amazing quality and fast shipping",
    "Would not buy again"
]

response = requests.post(
    "http://localhost:8000/v1/sentiment/vader/batch",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"texts": reviews}
)

results = response.json()
for review, sentiment in zip(reviews, results['sentiments']):
    print(f"{review}")
    print(f"  → {sentiment['label']} ({sentiment['compound']:.2f})")
    print()
```

### Use Case 2: Real-time Sentiment Monitor

```python
import requests
import time

API_KEY = "sk_live_your_key_here"

def analyze_sentiment(text):
    response = requests.post(
        "http://localhost:8000/v1/sentiment/vader",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"text": text}
    )
    return response.json()

# Monitor incoming messages
messages = [
    "I love this service!",
    "This is frustrating",
    "Works as expected"
]

for msg in messages:
    result = analyze_sentiment(msg)
    print(f"Message: {msg}")
    print(f"Sentiment: {result['sentiment']['label']}")
    print(f"Remaining: {result['usage']['requests_remaining']}")
    print()
    time.sleep(0.2)  # Respect rate limits
```

### Use Case 3: Compare Models

```python
import requests

API_KEY = "sk_live_your_key_here"
text = "This is an excellent product with outstanding quality!"

models = ["vader", "distilbert", "roberta"]

print(f"Text: {text}\n")
for model in models:
    response = requests.post(
        f"http://localhost:8000/v1/sentiment/{model}",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"text": text}
    )
    result = response.json()
    print(f"{model.upper()}:")
    print(f"  Label: {result['sentiment']['label']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Latency: {result['latency_ms']}ms")
    print()
```

## Testing Rate Limits

```python
import requests
import time

API_KEY = "sk_live_your_key_here"

# Test rate limit (10 req/sec)
print("Testing rate limit (10 req/sec)...")
for i in range(15):
    response = requests.post(
        "http://localhost:8000/v1/sentiment/vader",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"text": f"Test {i+1}"}
    )
    print(f"Request {i+1}: {response.status_code}")
    if response.status_code == 429:
        print("Rate limit exceeded!")
        print(response.json())
        break
```

## Monitoring Usage

```python
import requests

JWT_TOKEN = "your_jwt_token_here"

# Get usage stats
response = requests.get(
    "http://localhost:8000/api/dashboard/usage?timeframe=24h",
    headers={"Authorization": f"Bearer {JWT_TOKEN}"}
)

stats = response.json()
print(f"Total Requests: {stats['total_requests']}")
print(f"Success Rate: {stats['successful_requests']}/{stats['total_requests']}")
print(f"Average Latency: {stats['average_latency_ms']}ms")

# Get cost breakdown
response = requests.get(
    "http://localhost:8000/api/dashboard/costs",
    headers={"Authorization": f"Bearer {JWT_TOKEN}"}
)

costs = response.json()
print(f"\nCurrent Cost: ${costs['current_month']['total_cost']}")
print(f"Projected Cost: ${costs['projected_month']['estimated_cost']}")
```

## Troubleshooting

### Error: 401 Unauthorized
- Check that your API key is correct
- Make sure to include "Bearer " prefix
- Verify the API key hasn't been revoked

### Error: 429 Too Many Requests
- You've hit the rate limit (10 req/sec)
- Wait a moment before retrying
- Consider implementing exponential backoff

### Error: 400 Bad Request
- Check that text is not empty
- Ensure text is under 5000 characters
- Verify JSON format is correct

### Error: 500 Internal Server Error
- Check server logs
- Verify MongoDB connection
- Ensure vaderSentiment is installed

## Performance Tips

1. **Use Batch Predictions**: Process multiple texts in one request
2. **Implement Caching**: Cache frequent predictions
3. **Respect Rate Limits**: Add delays between requests
4. **Monitor Usage**: Check dashboard regularly
5. **Choose Right Model**: VADER for speed, DistilBERT for accuracy

## Next Steps

1. **Set Up Alerts**: Configure usage alerts at 80% threshold
2. **Test All Models**: Try VADER, DistilBERT, and RoBERTa
3. **Monitor Costs**: Check cost projections regularly
4. **Integrate**: Add to your application
5. **Scale**: Upgrade plan if needed

## Production Considerations

1. **API Key Security**:
   - Store keys in environment variables
   - Never commit keys to version control
   - Rotate keys regularly

2. **Error Handling**:
   - Implement retry logic with exponential backoff
   - Log all errors for debugging
   - Handle rate limit errors gracefully

3. **Performance**:
   - Use connection pooling
   - Implement request queuing
   - Cache frequent requests

4. **Monitoring**:
   - Track usage metrics
   - Set up alerts for high usage
   - Monitor costs daily

## Support

- API Documentation: `DIRECT_ACCESS_API_GUIDE.md`
- Test Script: `backend/test_direct_access.py`
- Server: http://localhost:8000
- API Docs: http://localhost:8000/docs
