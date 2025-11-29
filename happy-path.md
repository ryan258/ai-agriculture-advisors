# Happy Path - Quick Start Guide

This guide walks you through the fastest path to get the AI Agriculture Advisors application running successfully on your local machine.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Node.js** (v14 or later) installed - `node --version`
- [ ] **npm** installed (comes with Node.js) - `npm --version`
- [ ] **OpenRouter API Key** - [Get one free here](https://openrouter.ai/keys)

## Step 1: Install Dependencies

```bash
npm install
```

**Expected output:** You should see dependency installation logs with no errors.

## Step 2: Get Your OpenRouter API Key

1. Go to [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Sign up or log in (supports GitHub OAuth)
3. Create a new API key
4. Copy the key (starts with `sk-or-v1-...`)

**Free tier includes:**
- $1 of free credits to start
- Access to several free models (including Llama 3.1)
- No credit card required for testing

## Step 3: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file and add your OpenRouter API key:

```env
PORT=3000
MONGODB_URI=mongodb://localhost:27017/ai-agriculture-advisors
NODE_ENV=development

# Add your actual API key here
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_MODEL_NAME=meta-llama/llama-3.1-8b-instruct:free
```

**Note:** MongoDB is optional for basic functionality. If you don't have MongoDB installed, the app will still work (you'll see a connection warning, but you can ignore it).

## Step 4: Start the Application

**Development mode (recommended - auto-reloads on changes):**
```bash
npm run dev
```

**Production mode:**
```bash
npm start
```

**Expected output:**
```
Server running on port 3000
MongoDB connection error (this is OK if you don't have MongoDB)
```

**Important:** Make sure you see no errors about missing `OPENROUTER_API_KEY`. If you do, double-check your `.env` file.

## Step 5: Verify It's Working

### Option A: Use the Web Interface

1. Open your browser and navigate to: **http://localhost:3000**
2. You should see the AI Agriculture Advisors interface
3. Select one or more experts from the sidebar (e.g., "Agricultural Science Expert")
4. Enter a test query: `What are the benefits of crop rotation?`
5. Click **"Submit Query"**
6. Wait 5-10 seconds for the AI response

**Success indicator:** You should see formatted responses from the selected experts.

### Option B: Test the API with curl

```bash
curl -X POST http://localhost:3000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the best practices for soil conservation?",
    "expertRoles": ["agriculture"]
  }'
```

**Expected output:** JSON response with expert advice.

## Step 6: Try a Roundtable Discussion (Optional)

This is a more advanced feature where multiple experts collaborate:

1. In the web interface, select 2-3 experts:
   - Agricultural Science Expert
   - Climate Change Impact Analyst
   - Soil Health Specialist

2. Enter a complex query:
   ```
   How can we adapt farming practices to mitigate climate change impacts while maintaining soil health?
   ```

3. Click **"Round Table Discussion"**

4. Wait 15-30 seconds for the collaborative discussion

**Success indicator:** You should see a transcript of the discussion between experts, followed by a synthesized final answer.

## Common "Happy Path" Workflows

### Workflow 1: Quick Expert Consultation
1. Navigate to http://localhost:3000
2. Select **one expert** (faster response)
3. Ask a specific question
4. Get instant advice

**Use case:** "What's the optimal pH level for tomato plants?" → Soil Health Specialist

### Workflow 2: Multi-Expert Comparison
1. Select **2-4 related experts**
2. Ask a broad question
3. Compare different perspectives side-by-side

**Use case:** "What are the pros and cons of organic farming?" → Select Organic Farming Consultant + Agricultural Economics Advisor

### Workflow 3: Deep Dive with Roundtable
1. Select **3+ experts** with complementary expertise
2. Ask a complex, multi-faceted question
3. Use "Round Table Discussion" button
4. Review the collaborative discussion

**Use case:** "Design a sustainable irrigation strategy for drought-prone regions" → Irrigation Specialist + Climate Analyst + Agricultural Science Expert

## Quick Troubleshooting

### Issue: "OPENROUTER_API_KEY is not set in environment variables"

**Fix:**
1. Make sure you created a `.env` file (not just using `.env.example`)
2. Verify your API key is set correctly in `.env`:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   ```
3. Restart the server after updating `.env`

### Issue: "Failed to generate response from LLM via OpenRouter"

**Common causes:**
1. **Invalid API key** - Double-check your key at https://openrouter.ai/keys
2. **Out of credits** - Check your balance at https://openrouter.ai/account
3. **Network issues** - Verify you can access https://openrouter.ai

**Test your connection:**
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Issue: Port 3000 already in use

**Fix:** Change the port in `.env`:
```env
PORT=3001
```
Then restart the server and access http://localhost:3001

### Issue: Slow responses (> 30 seconds)

**Fix:** Switch to a faster model in `.env`:
```env
# Faster free option:
OPENROUTER_MODEL_NAME=google/gemini-flash-1.5

# Or a smaller Llama model:
OPENROUTER_MODEL_NAME=meta-llama/llama-3.1-8b-instruct:free
```

### Issue: MongoDB connection warnings

**Fix:** This is safe to ignore if you're not using database features. To suppress warnings, you can comment out the MongoDB connection in `src/server.js`:
```javascript
// Comment this line:
// connectDB();
```

### Issue: Rate limiting or quota exceeded

**Fix:**
1. Check your usage at https://openrouter.ai/activity
2. Add credits to your account if needed
3. Switch to a free model:
   ```env
   OPENROUTER_MODEL_NAME=meta-llama/llama-3.1-8b-instruct:free
   ```

## Next Steps

Once everything is working:

1. **Explore all 10 experts** - Each has unique specialized knowledge
2. **Try complex queries** - Test multi-expert roundtables
3. **Experiment with models** - Try different OpenRouter models (Claude, GPT-4, Gemini, etc.)
4. **Read the full docs** - Check [README.md](README.md) for API details
5. **Check the roadmap** - See planned features in [ROADMAP.md](ROADMAP.md)
6. **Monitor costs** - Keep an eye on your OpenRouter usage and credits

## Success Indicators Summary

You're on the happy path when:

- ✅ Server starts without errors on port 3000
- ✅ Web interface loads at http://localhost:3000
- ✅ No errors about missing OPENROUTER_API_KEY
- ✅ Sample queries return AI-generated responses
- ✅ Multiple experts can be queried simultaneously
- ✅ Roundtable discussions complete successfully

## Pro Tips for the Happy Path

1. **Start with free models** - Use `meta-llama/llama-3.1-8b-instruct:free` to avoid charges
2. **Monitor your usage** - Check https://openrouter.ai/activity to track API calls and costs
3. **MongoDB is optional** - Skip it if you're just testing the AI features
4. **Test with one expert first** - Verify basic functionality before trying roundtables
5. **Check the logs** - Watch `combined.log` for debugging (created automatically)
6. **Try different models** - OpenRouter supports 100+ models - experiment to find the best fit

---

**Happy farming! 🌾** (if that's your thing - otherwise, happy coding!)
