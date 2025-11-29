# AI Agriculture Advisors — Roadmap

Personal project enhancement plan.

**Last Updated:** November 29, 2025
**Current Version:** 1.1.0
**Status:** Stable, ready for enhancements

> See [CHANGELOG.md](CHANGELOG.md) for completed features and release history.

---

## 🎯 Now (Worth doing soon)

### Testing & Code Quality
- [x] **Add basic tests**: Test core functionality (Jest)
  - Test llamaService with different providers
  - Test expert registry
  - Test API endpoints with sample queries
- [x] **Add ESLint**: Keep code clean and consistent
  - Use eslint-config-standard or airbnb
  - Auto-fix on save

### LLM Provider Flexibility
- [x] **LLM provider abstraction**: Switch between OpenRouter, Anthropic, OpenAI easily
  - Support multiple providers in config
  - Fallback to backup provider on failure
  - Easy provider switching via .env

### Mobile Experience
- [x] **Make it mobile responsive**: Use on phone/tablet
  - Responsive layout
  - Touch-friendly controls
  - Mobile-optimized sidebar

---

## 🔧 Next (Nice improvements)

### Data & Context
- [ ] **Weather API integration**: Give experts real-time weather context
  - OpenWeatherMap API
  - Location-based forecasts
  - Include in expert prompts
- [ ] **Commodity prices**: Real-time market data
  - Simple price feed integration
  - Display in expert responses
- [ ] **Populate data files**: Add real agricultural data to JSON files
  - Crop characteristics
  - Climate zones
  - Basic market data

### Response Improvements
- [ ] **Streaming responses**: See LLM output as it generates
  - Server-sent events (SSE)
  - Progressive rendering
  - Better perceived performance
- [ ] **Response caching**: Cache similar queries to save API costs
  - Simple in-memory cache
  - Semantic similarity matching
  - Cost savings tracking
- [ ] **Model selection UI**: Choose model speed/quality tradeoff
  - Dropdown for different models
  - Show cost/speed info
  - Remember preference

### User Experience
- [ ] **PDF export**: Export responses as PDF
  - jsPDF integration
  - Nice formatting
- [ ] **Better visualizations**: Render tables, charts nicely
  - Table formatting
  - Basic chart support
- [ ] **Query history with search**: Find old queries easily
  - Searchable history
  - Organize by date/topic
  - Export history

---

## 💾 Later (If useful)

### Optional Features
- [ ] **MongoDB activation**: Store query history in database instead of localStorage
  - Query history
  - Analytics on usage
  - Better search
- [ ] **Redis caching**: Faster caching layer
  - Cache LLM responses
  - Reduce API costs
  - Session storage
- [ ] **Multi-turn conversations**: Context-aware follow-up questions
  - Conversation threads
  - Reference previous responses
  - Smarter experts

### Advanced Capabilities
- [ ] **Image analysis**: Upload crop photos for pest/disease ID
  - Vision model integration
  - Image upload UI
  - Combined text + image queries
- [ ] **Voice interface**: Hands-free queries
  - Web Speech API
  - Voice input
  - Audio responses
- [ ] **RAG (Retrieval-Augmented Generation)**: Knowledge base integration
  - Vector database (Pinecone/Weaviate)
  - Agricultural knowledge base
  - Better factual accuracy

---

## 🗂️ Cleanup (Eventually)

### Code Cleanup
- [ ] **Remove unused files**: Clean up placeholders
  - Remove or implement: dataCollectionService.js, insightGenerationService.js, llamaHelper.js, dataPreprocessor.js
  - Decide on MongoDB models (use or remove)
  - Clean up empty data files
- [ ] **TypeScript migration**: Add type safety (if interested)
  - Gradual conversion
  - Better IDE support
  - Fewer bugs

### Refactoring
- [ ] **Standardize response formats**: Consistent API structure
- [ ] **Extract configuration**: Centralize all config
- [ ] **Reduce duplication**: DRY up the code

---

## 🚀 Deployment (When ready to host)

### Simple Deployment
- [ ] **Dockerfile**: Easy deployment anywhere
  - Single container
  - docker-compose for MongoDB/Redis
- [ ] **Deploy to cloud**: Get it online
  - Heroku (easiest)
  - Railway
  - Fly.io
  - Digital Ocean
- [ ] **Environment configs**: Dev vs production settings

---

## 🌟 Fun Ideas (Maybe someday)

### Interesting Experiments
- [ ] **Different LLM comparisons**: Run same query on multiple models, compare
- [ ] **Agent-based planning**: Let experts plan multi-step agricultural projects
- [ ] **Geolocation features**: Location-aware recommendations
- [ ] **Offline PWA**: Work without internet
- [ ] **Different domains**: Adapt to other fields beyond agriculture
  - Medical advisors
  - Financial advisors
  - Legal advisors
  - etc.

---

## 📈 Current Stats

**What works well:**
- ✅ 10 expert advisors responding reliably
- ✅ Roundtable discussions with multi-expert collaboration
- ✅ Clean, usable UI with dark mode
- ✅ Query history and export
- ✅ OpenRouter integration with 100+ model options
- ✅ Rate limiting and security basics

**Current metrics:**
- Response time: ~2-10 seconds (model dependent)
- API latency: < 200ms (excluding LLM)
- Memory: ~150MB baseline
- Concurrent queries: Tested up to 50

**Known issues:**
- No mobile optimization yet
- No response streaming (feels slow)
- No tests (risky to refactor)
- MongoDB connected but not really used
- Some placeholder files not implemented

---

## 🎯 Recommended Next Actions

If I were to work on this project next, I'd focus on:

1. **Mobile responsive design** - Make it usable on phone (quick win)
2. **Streaming responses** - Much better UX, feels faster
3. **Basic tests** - So you can refactor without fear
4. **Response caching** - Save money on API calls
5. **Clean up unused code** - Remove clutter

**Low effort, high value:**
- Mobile responsiveness (few hours)
- ESLint setup (30 minutes)
- Remove unused placeholder files (30 minutes)

**Higher effort, worth it:**
- Streaming responses (few hours, big UX improvement)
- Response caching (few hours, saves money)
- LLM provider abstraction (few hours, more flexibility)

---

**Note:** Since this is a personal project, skip the enterprise stuff (authentication, user management, CI/CD complexity, community features, etc.). Focus on what makes it useful and fun for you!
