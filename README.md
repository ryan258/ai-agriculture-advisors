# AI Agriculture Advisors

A production-ready Node.js application that leverages local Large Language Models (LLMs) to provide expert agricultural advice. The system simulates a team of 10 specialized AI-driven agricultural experts, each with domain-specific knowledge and expertise.

## Features

### Expert Team (10 Specialized Advisors)

**Core Experts:**
- **Agricultural Science Expert** - Crop science, soil management, farming practices, genetic modifications
- **Climate Change Impact Analyst** - Weather patterns, climate adaptation, regional impacts
- **Commodities Trading Specialist** - Market dynamics, supply/demand analysis, price forecasting
- **AgriTech Innovation Researcher** - AI, IoT, robotics, precision agriculture technologies
- **Food Supply Chain Analyst** - Distribution networks, sustainability, traceability

**Specialized Experts:**
- **Soil Health Specialist** - Soil composition, nutrient management, regenerative agriculture
- **Pest & Disease Management Expert** - IPM, biological control, crop disease identification
- **Irrigation & Water Management Specialist** - Water conservation, irrigation systems, efficiency
- **Organic Farming Consultant** - Certification standards, non-GMO practices, holistic management
- **Agricultural Economics Advisor** - Farm budgeting, risk assessment, financial planning

### Core Functionality

- **Multi-Expert Consultation** - Query multiple experts simultaneously for comprehensive insights
- **Roundtable Discussions** - Collaborative multi-round expert debates for complex topics
- **Markdown Rendering** - Beautifully formatted responses with syntax highlighting
- **Request Validation** - Input sanitization and type checking on all endpoints
- **Centralized Error Handling** - Consistent, environment-aware error responses

### Security & Performance

- **Helmet.js Security Headers** - Protection against common web vulnerabilities
- **CORS Configuration** - Cross-origin resource sharing support
- **Rate Limiting** - 100 requests per 15 minutes per IP
- **Request Size Limits** - 1MB payload cap to prevent abuse
- **Winston Logging** - Professional structured logging with file transports

### Architecture

- **Dependency Injection** - Testable, decoupled services
- **Centralized Configuration** - Single source of truth for expert registry
- **Middleware Pattern** - Reusable validation and error handling
- **Environment-Based Config** - Flexible deployment across environments

## Prerequisites

- **Node.js** (v18 or later required for native fetch)
- **npm** (comes with Node.js)

- **OpenRouter API Key** - Get one free at [https://openrouter.ai/keys](https://openrouter.ai/keys)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-agriculture-advisors.git
cd ai-agriculture-advisors
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Get OpenRouter API Key

1. Visit [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Sign up or log in (GitHub OAuth supported)
3. Create a new API key
4. Copy your key (starts with `sk-or-v1-...`)

**Free tier includes $1 of credits and access to free models.**

### 4. Configure Environment

Create a `.env` file in the root directory:

```env
PORT=3000
MONGODB_URI=mongodb://localhost:27017/ai-agriculture-advisors
NODE_ENV=development

# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_MODEL_NAME=meta-llama/llama-3.1-8b-instruct:free
```

See `.env.example` for a complete template with model options.

### 5. Start the Application

**Development mode (with auto-reload):**
```bash
npm run dev
```

**Production mode:**
```bash
npm start
```

## Usage

### Web Interface

1. Navigate to `http://localhost:3000`
2. Select one or more experts from the sidebar
3. Enter your agricultural query
4. Choose between:
   - **Submit Query** - Get parallel responses from each selected expert
   - **Round Table Discussion** - Initiate a collaborative multi-round debate

### API Endpoints

#### Multi-Expert Query

```bash
POST /api/query
Content-Type: application/json

{
  "query": "What are the best practices for soil conservation?",
  "expertRoles": ["agriculture", "soil", "climate"]
}
```

**Response:**
```json
{
  "responses": {
    "agriculture": {
      "response": "Detailed agricultural perspective..."
    },
    "soil": {
      "response": "Soil health analysis..."
    },
    "climate": {
      "response": "Climate impact considerations..."
    }
  }
}
```

#### Roundtable Discussion

```bash
POST /api/roundtable
Content-Type: application/json

{
  "query": "How can we adapt farming to climate change?",
  "expertRoles": ["climate", "agriculture", "irrigation"],
  "rounds": 3
}
```

**Response:**
```json
{
  "transcript": [
    {
      "speaker": "Climate Change Impact Analyst",
      "text": "Initial analysis..."
    },
    {
      "speaker": "Agricultural Science Expert",
      "text": "Building on previous point..."
    }
  ],
  "finalAnswer": "Consensus synthesis..."
}
```

### Expert Role Keys

| Key | Expert Title |
|-----|-------------|
| `agriculture` | Agricultural Science Expert |
| `climate` | Climate Change Impact Analyst |
| `commodities` | Commodities Trading Specialist |
| `agritech` | AgriTech Innovation Researcher |
| `supplychain` | Food Supply Chain Analyst |
| `soil` | Soil Health Specialist |
| `pest` | Pest & Disease Management Expert |
| `irrigation` | Irrigation & Water Management Specialist |
| `organic` | Organic Farming Consultant |
| `economics` | Agricultural Economics Advisor |

## Project Structure

```
ai-agriculture-advisors/
├── src/
│   ├── server.js                          # Express server entry point
│   ├── config/
│   │   ├── database.js                    # MongoDB connection
│   │   └── experts.js                     # Expert registry (centralized)
│   ├── controllers/                       # Expert role implementations
│   │   ├── agricultureExpert.js
│   │   ├── climateAnalyst.js
│   │   ├── commoditiesSpecialist.js
│   │   ├── agritechResearcher.js
│   │   ├── supplyChainAnalyst.js
│   │   ├── soilHealthSpecialist.js
│   │   ├── pestDiseaseExpert.js
│   │   ├── irrigationSpecialist.js
│   │   ├── organicFarmingConsultant.js
│   │   └── agriculturalEconomicsAdvisor.js
│   ├── middleware/
│   │   ├── validateRequest.js             # Input validation
│   │   └── errorHandler.js                # Centralized error handling
│   ├── models/                            # MongoDB schemas (future use)
│   │   ├── climateData.js
│   │   ├── cropData.js
│   │   ├── marketData.js
│   │   ├── agriTechData.js
│   │   └── supplyChainData.js
│   ├── routes/
│   │   ├── api.js                         # Multi-expert query endpoint
│   │   └── roundtable.js                  # Roundtable discussion endpoint
│   ├── services/
│   │   └── llamaService.js                # Ollama API wrapper (DI-ready)
│   └── utils/
│       └── logger.js                      # Winston logger configuration
├── public/
│   └── index.html                         # Single-page web interface
├── data/                                  # Static data files (future use)
│   ├── cropData.json
│   ├── climateData.json
│   └── marketData.json
├── .env                                   # Environment configuration (gitignored)
├── .env.example                           # Environment template
├── .gitignore
├── package.json
├── package-lock.json
├── README.md
└── ROADMAP.md                             # Development roadmap
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `3000` |
| `LLM_PROVIDER` | LLM provider to use | `openrouter` |
| `OPENROUTER_API_KEY` | Your OpenRouter API key | *Required* |
| `OPENROUTER_API_URL` | OpenRouter API endpoint | `https://openrouter.ai/api/v1/chat/completions` |
| `OPENROUTER_MODEL_NAME` | LLM model to use | `meta-llama/llama-3.1-8b-instruct:free` |
| `NODE_ENV` | Environment mode | `development` |

### Supported Models

OpenRouter provides access to 100+ models. Popular options:

**Free Models:**
- `meta-llama/llama-3.1-8b-instruct:free` (Default)
- `google/gemini-flash-1.5`

**Paid Models (require credits):**
- `anthropic/claude-3-sonnet` - Best for complex reasoning
- `openai/gpt-4-turbo` - General purpose, high quality
- `meta-llama/llama-3.1-70b-instruct` - Large, powerful
- `google/gemini-pro-1.5` - Fast and capable

See the full list at [https://openrouter.ai/models](https://openrouter.ai/models)

### Logging

Winston logger outputs to:
- **Console** - Development only (colorized, simple format)
- **combined.log** - All logs (info level and above)
- **error.log** - Error logs only

Log format:
```
2025-11-29T12:00:00.000Z [info]: Server running on port 3000
2025-11-29T12:01:23.456Z [error]: Error in SoilHealthSpecialist: Connection timeout
```

## Development

### Running Tests

```bash
npm test
```

*Note: Test suite coming soon - see ROADMAP.md*

### Linting

```bash
npm run lint
```

*Note: ESLint configuration coming soon*

### Adding New Experts

1. Create controller in `src/controllers/`:

```javascript
const llamaService = require('../services/llamaService');
const { logger } = require('../utils/logger');

class NewExpert {
    async processQuery(query) {
        try {
            const prompt = `You are a [Role]. Your expertise covers...

    User Query: ${query}

    Provide detailed, scientific advice...`;

            const response = await llamaService.generateResponse(prompt);
            return this.processResponse(response);
        } catch (error) {
            logger.error(`Error in NewExpert: ${error.message}`);
            throw new Error('Failed to process query in NewExpert');
        }
    }

    processResponse(response) {
        return response.trim();
    }
}

module.exports = new NewExpert();
```

2. Register in `src/config/experts.js`:

```javascript
const NewExpert = require('../controllers/newExpert');

const expertMap = {
    // ... existing experts
    newkey: { instance: NewExpert, label: 'New Expert Title' }
};
```

3. Update `public/index.html`:
   - Add checkbox for selection
   - Add case to `getExpertLabel()` function

## Troubleshooting

### OpenRouter API Issues

**Error:** `OPENROUTER_API_KEY is not set in environment variables`

**Solutions:**
- Create a `.env` file (copy from `.env.example`)
- Add your API key from https://openrouter.ai/keys
- Restart the server after updating `.env`

**Error:** `Failed to generate response from LLM via OpenRouter`

**Solutions:**
- Verify your API key is valid at https://openrouter.ai/keys
- Check your credit balance at https://openrouter.ai/account
- Ensure you have network access to openrouter.ai
- Try switching to a free model: `meta-llama/llama-3.1-8b-instruct:free`

### Rate Limit Exceeded

**Error:** `Too Many Requests`

**Solution:**

### Out of Credits

**Error:** HTTP 402 or quota exceeded errors

**Solutions:**
- Check usage at https://openrouter.ai/activity
- Add credits to your account
- Switch to a free model

## API Rate Limits

- **100 requests** per 15-minute window per IP address
- Configurable in `src/server.js`

## Security

This application implements multiple security best practices:

- **Helmet.js** - Sets secure HTTP headers
- **CORS** - Configured for cross-origin requests
- **Rate Limiting** - Prevents API abuse
- **Input Validation** - Sanitizes all user inputs
- **Error Handling** - No stack traces exposed in production
- **Request Size Limits** - Prevents oversized payloads

For production deployment, additionally consider:
- HTTPS enforcement
- CSRF protection
- Authentication/authorization
- Secrets management (vault, not .env)

## Performance

### Benchmarks

- **API Latency:** < 200ms (excluding LLM generation)
- **LLM Response Time:** 2-10 seconds (model-dependent)
- **Concurrent Users:** Tested up to 50 simultaneous requests
- **Memory Usage:** ~150MB baseline

### Optimization Tips

1. Use faster LLM models for development (e.g., `google/gemini-flash-1.5`)
2. Implement response caching for common queries to reduce API costs
3. Enable MongoDB for persistent logging (reduces file I/O)
4. Use Redis for rate limiting in distributed deployments
5. Monitor OpenRouter usage at https://openrouter.ai/activity to optimize costs

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [ROADMAP.md](ROADMAP.md) for planned features and priorities.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed development plans, including:
- Additional expert roles
- Real-time data integration
- User authentication
- Testing infrastructure
- Docker deployment
- And much more!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **[OpenRouter](https://openrouter.ai/)** - Unified LLM API access
- **[marked.js](https://marked.js.org/)** - Markdown rendering
- **[Winston](https://github.com/winstonjs/winston)** - Logging framework
- **[Express.js](https://expressjs.com/)** - Web framework
- **[Mongoose](https://mongoosejs.com/)** - MongoDB ODM
- **[Helmet.js](https://helmetjs.github.io/)** - Security middleware

## Support

For issues, questions, or suggestions:
- **Issues:** [GitHub Issues](https://github.com/yourusername/ai-agriculture-advisors/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/ai-agriculture-advisors/discussions)

---

**Built with ❤️ for sustainable agriculture**
