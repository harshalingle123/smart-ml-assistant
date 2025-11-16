# Quick Start Guide - Gemini AI Agent 🚀

## ⚡ Start Everything in 3 Steps

### Step 1: Start Backend (Already Running!)
```bash
# Backend is running on http://localhost:8000
# Check: http://localhost:8000/docs
```

### Step 2: Start Frontend
```bash
cd frontend/client
npm run dev
```

### Step 3: Test the Agent
```
1. Open http://localhost:5173
2. Login or Register
3. Go to Chat
4. Make sure "AI Agent Mode" toggle is ON
5. Try this: "I need a dataset to predict house prices"
```

---

## 🎯 What to Expect

### Query: "I need a dataset to predict house prices"

**Agent Will:**
1. ✅ Interpret: Regression task, house prices topic
2. ✅ Search: Kaggle + HuggingFace datasets
3. ✅ Suggest: XGBoost, AutoGluon, Linear Regression
4. ✅ Return: 5-8 dataset cards + model recommendations

**You'll See:**
```
🤖 Smart ML Assistant:

For predicting house prices (regression task), I found 5 datasets:

📊 Suggested Datasets from Kaggle:
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ House Prices  │ │ Real Estate   │ │ Boston        │
│ 2.5MB         │ │ 5.1MB         │ │ Housing       │
│ 50K downloads │ │ 30K downloads │ │ 1.2MB         │
│ [Add to DB]   │ │ [Add to DB]   │ │ 20K downloads │
└───────────────┘ └───────────────┘ │ [Add to DB]   │
                                    └───────────────┘

🤖 I recommend XGBoost because...
💰 Cost: $15-20
⏱️ Time: 2-3 hours
📈 Accuracy: 85-92%
```

---

## 🧪 Test Queries

Copy-paste these:

### Dataset Finding
```
I need a dataset to predict house prices
Find me sentiment analysis datasets
Show me image classification datasets
```

### With Constraints
```
Classify customer support tickets with <200ms latency and $100 budget
```

### Model Help
```
What's the best model for text classification?
Suggest models for time series forecasting
```

---

## 🎮 UI Controls

### Agent Mode Toggle
```
┌──────────────────────────────────────┐
│ ✨ AI Agent Mode         [ON] ←──── Toggle this
│ Agent will automatically find datasets
└──────────────────────────────────────┘
```

**ON** = Agent uses function calling (smart)
**OFF** = Regular chat (simple Q&A)

---

## 📊 Backend Endpoints

| Endpoint | Purpose | Agent Uses? |
|----------|---------|-------------|
| `/api/messages/chat` | Regular chat | When OFF |
| `/api/messages/agent` | AI Agent | When ON ✅ |
| `/docs` | API documentation | - |

Test directly:
- http://localhost:8000/docs

---

## 🔍 How to Debug

### Check Backend
```bash
# View logs
cat backend.log

# Or tail in real-time
tail -f backend.log
```

### Check Frontend
1. Open browser console (F12)
2. Network tab
3. Look for `/api/messages/agent` calls
4. Check response

### Common Issues

**Issue: "Not authenticated"**
- Solution: Login first, then go to Chat

**Issue: "Agent Mode toggle missing"**
- Solution: Refresh page (Ctrl+R)

**Issue: "No datasets shown"**
- Solution: Check Kaggle API credentials in backend/.env

**Issue: "429 Rate limit"**
- Solution: Wait 60 seconds (Gemini free tier = 10 req/min)

---

## 🎯 Success Criteria

✅ You should see:
1. Agent Mode toggle in Chat header
2. Welcome message mentioning "Agent Mode"
3. Datasets appear as cards
4. Model recommendations in response
5. "Add to Collection" buttons on datasets

---

## 📁 Key Files to Check

```
backend/
  ├── app/services/gemini_agent_service.py  ← Agent logic
  ├── app/routers/messages.py               ← /agent endpoint
  └── .env                                   ← API keys

frontend/client/src/
  ├── lib/api.ts                            ← sendMessageToAgent()
  └── pages/Chat.tsx                        ← UI + toggle
```

---

## 🚀 What's Working

✅ Backend:
- Gemini agent service with 3 tools
- `/api/messages/agent` endpoint
- Kaggle integration
- HuggingFace mapping
- Function calling (interpret → find → suggest)

✅ Frontend:
- Agent mode toggle
- Automatic routing
- Dataset cards display
- Model recommendations
- Error handling

---

## 📈 Next Actions

1. **Test it now!**
   - Start frontend: `cd frontend/client && npm run dev`
   - Open: http://localhost:5173
   - Ask: "I need house price datasets"

2. **Try different queries**
   - See FRONTEND_INTEGRATION_COMPLETE.md

3. **Customize**
   - Add more HuggingFace datasets in `gemini_agent_service.py:186-206`
   - Add more models in `gemini_agent_service.py:232-354`
   - Style the toggle in `Chat.tsx`

---

## 🎉 You're Ready!

**Backend**: ✅ Running on port 8000
**Frontend**: Ready to start
**Agent**: Configured and tested
**Datasets**: Kaggle + HuggingFace
**Models**: 15+ recommendations ready

Just run `npm run dev` in frontend and you're live! 🚀

---

## 📞 Quick Help

**Backend not starting?**
```bash
backend/venv/Scripts/python.exe backend/run.py
```

**Frontend errors?**
```bash
cd frontend/client
npm install
npm run dev
```

**Want to test without frontend?**
```bash
python test_gemini_agent.py
```

---

**Happy Testing! 🎊**
