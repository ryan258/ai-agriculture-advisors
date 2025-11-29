# API Documentation

Complete API reference for AI Agriculture Advisors.

## Base URL

```
http://localhost:3000
```

## Authentication

Currently, no authentication is required. This may change in future versions.

## Rate Limiting

- **Limit:** 100 requests per 15-minute window per IP address
- **Headers:** Standard rate limit headers are not currently implemented
- **Response:** `429 Too Many Requests` when limit exceeded

## Common Headers

### Request Headers

```
Content-Type: application/json
```

### Response Headers

```
Content-Type: application/json
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
```

## Error Responses

All errors return JSON in this format:

```json
{
    "message": "Error description",
    "error": "Detailed error (development only)"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request parameters |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error occurred |

## Endpoints

### 1. Multi-Expert Query

Query one or more experts simultaneously and receive parallel responses.

**Endpoint:** `POST /api/query`

**Request Body:**

```json
{
    "query": "string (required)",
    "expertRoles": ["string"] (required, non-empty array)
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | The question or query for the experts |
| `expertRoles` | array | Yes | Array of expert role keys (see Expert Roles below) |

**Example Request:**

```bash
curl -X POST http://localhost:3000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the best practices for organic pest control?",
    "expertRoles": ["agriculture", "pest", "organic"]
  }'
```

**Success Response (200 OK):**

```json
{
    "responses": {
        "agriculture": {
            "response": "From an agricultural science perspective, integrated pest management (IPM) combines biological, cultural, and mechanical control methods..."
        },
        "pest": {
            "response": "As a pest management expert, I recommend focusing on prevention through crop rotation, companion planting, and natural predators..."
        },
        "organic": {
            "response": "For organic certification compliance, you should prioritize OMRI-listed products and biological controls..."
        }
    }
}
```

**Error Response (400 Bad Request):**

```json
{
    "message": "expertRoles must be a non-empty array."
}
```

**Error Response (500 Internal Server Error):**

```json
{
    "message": "Error processing query",
    "error": "Failed to generate response from LLaMA model"
}
```

---

### 2. Roundtable Discussion

Initiate a multi-round discussion between selected experts with collaborative synthesis.

**Endpoint:** `POST /api/roundtable`

**Request Body:**

```json
{
    "query": "string (required)",
    "expertRoles": ["string"] (required, minimum 2),
    "rounds": number (optional, default: 3)
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | The topic for roundtable discussion |
| `expertRoles` | array | Yes | Array of expert role keys (minimum 2) |
| `rounds` | number | No | Number of discussion rounds (default: 3) |

**Example Request:**

```bash
curl -X POST http://localhost:3000/api/roundtable \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How can small farms adapt to climate change?",
    "expertRoles": ["climate", "agriculture", "irrigation", "economics"],
    "rounds": 2
  }'
```

**Success Response (200 OK):**

```json
{
    "transcript": [
        {
            "speaker": "Climate Change Impact Analyst",
            "text": "Climate change presents several challenges for small farms including increased temperature variability, changing precipitation patterns..."
        },
        {
            "speaker": "Agricultural Science Expert",
            "text": "Building on the climate analysis, small farms should consider drought-resistant crop varieties and soil conservation practices..."
        },
        {
            "speaker": "Irrigation & Water Management Specialist",
            "text": "I agree with both points. Adding to this, efficient irrigation systems like drip irrigation can reduce water usage by up to 60%..."
        },
        {
            "speaker": "Agricultural Economics Advisor",
            "text": "From a financial perspective, while these adaptations require upfront investment, government subsidies and long-term savings justify the costs..."
        }
    ],
    "finalAnswer": "Based on our collaborative discussion, small farms can adapt to climate change through a multi-faceted approach: 1) Implementing climate-resilient crop varieties, 2) Adopting water-efficient irrigation systems, 3) Enhancing soil health through conservation practices, and 4) Leveraging available subsidies to offset adaptation costs. Success requires integrating climate science, agricultural best practices, water management, and economic planning."
}
```

**Error Response (400 Bad Request):**

```json
{
    "message": "At least two experts are required for a round table discussion."
}
```

---

## Expert Roles

### Available Experts

| Key | Expert Title | Domain Expertise |
|-----|-------------|------------------|
| `agriculture` | Agricultural Science Expert | Crop science, soil management, farming practices, genetic modifications |
| `climate` | Climate Change Impact Analyst | Weather patterns, climate adaptation strategies, regional impacts |
| `commodities` | Commodities Trading Specialist | Market dynamics, supply/demand analysis, price forecasting |
| `agritech` | AgriTech Innovation Researcher | AI, IoT, robotics, precision agriculture, farm automation |
| `supplychain` | Food Supply Chain Analyst | Distribution networks, logistics, sustainability, traceability |
| `soil` | Soil Health Specialist | Soil composition, nutrient management, composting, regenerative agriculture |
| `pest` | Pest & Disease Management Expert | IPM, biological control, disease identification, sustainable pest control |
| `irrigation` | Irrigation & Water Management Specialist | Water conservation, irrigation systems, efficiency optimization |
| `organic` | Organic Farming Consultant | Certification standards (USDA, EU), non-GMO practices, holistic management |
| `economics` | Agricultural Economics Advisor | Farm budgeting, market analysis, risk assessment, financial planning |

### Expert Capabilities

Each expert can:
- Answer domain-specific questions
- Provide scientific and practical advice
- Consider relevant factors in their expertise area
- Recommend solutions and best practices
- Collaborate in roundtable discussions

---

## Usage Examples

### Example 1: Single Expert Query

**Request:**
```json
{
    "query": "What is the ideal soil pH for growing tomatoes?",
    "expertRoles": ["soil"]
}
```

**Response:**
```json
{
    "responses": {
        "soil": {
            "response": "The ideal soil pH for growing tomatoes is between 6.0 and 6.8, with 6.5 being optimal. This slightly acidic range ensures maximum nutrient availability, particularly for nitrogen, phosphorus, and potassium..."
        }
    }
}
```

---

### Example 2: Multi-Expert Consultation

**Request:**
```json
{
    "query": "Should I invest in solar panels for my farm?",
    "expertRoles": ["agritech", "economics", "climate"]
}
```

**Response:**
```json
{
    "responses": {
        "agritech": {
            "response": "Solar panels offer significant benefits for farms including reduced energy costs, energy independence, and the potential to sell excess power back to the grid..."
        },
        "economics": {
            "response": "The financial viability depends on several factors: upfront costs ($15,000-$25,000 per acre typically), available tax credits (26% federal ITC), expected ROI (7-20 years)..."
        },
        "climate": {
            "response": "From a climate perspective, solar energy reduces your farm's carbon footprint and provides resilience against energy price volatility..."
        }
    }
}
```

---

### Example 3: Complex Roundtable Discussion

**Request:**
```json
{
    "query": "What is the future of vertical farming?",
    "expertRoles": ["agritech", "economics", "supplychain", "climate"],
    "rounds": 3
}
```

**Response:**
```json
{
    "transcript": [
        {
            "speaker": "AgriTech Innovation Researcher",
            "text": "Vertical farming represents a paradigm shift with LED lighting, hydroponic systems, and AI-driven climate control..."
        },
        {
            "speaker": "Agricultural Economics Advisor",
            "text": "The economics are challenging. Initial capital costs are 10-20x traditional farming, but operational efficiency and year-round production offset this..."
        },
        {
            "speaker": "Food Supply Chain Analyst",
            "text": "Vertical farms near urban centers drastically reduce transportation costs and food miles, addressing 'last-mile' distribution challenges..."
        },
        {
            "speaker": "Climate Change Impact Analyst",
            "text": "As climate change increases agricultural risk, controlled environment agriculture provides climate-independent food production..."
        },
        {
            "speaker": "AgriTech Innovation Researcher",
            "text": "Building on the economic concerns, emerging technologies like solid-state LEDs and renewable energy integration are reducing costs by 30-40%..."
        }
        // ... more rounds
    ],
    "finalAnswer": "The future of vertical farming is promising but nuanced. While current economics favor high-value crops in urban settings, technological advances are expanding viability. Success factors include: 1) Proximity to urban markets, 2) Integration with renewable energy, 3) Focus on high-margin crops (herbs, microgreens, specialty produce), 4) Automation to reduce labor costs, and 5) Climate resilience as traditional agriculture faces increasing risks. Expect significant growth in the next decade, particularly in regions with limited arable land or extreme climates."
}
```

---

## Best Practices

### Query Formulation

**Do:**
- Be specific and clear in your questions
- Provide context when relevant
- Ask one focused question per query
- Use proper grammar and spelling

**Don't:**
- Ask multiple unrelated questions in one query
- Use ambiguous or vague language
- Include personally identifiable information
- Submit empty or extremely long queries

### Expert Selection

**Single Expert:**
- Use when you need domain-specific expertise
- Faster response times
- More focused answers

**Multiple Experts:**
- Use for multidimensional questions
- Get diverse perspectives
- Understand trade-offs between approaches

**Roundtable:**
- Use for complex, multi-faceted topics
- Best with 2-4 experts
- More processing time but richer insights
- Experts build on each other's points

### Performance Optimization

1. **Use appropriate expert count**
   - Single expert: ~3-5 seconds
   - 3 experts: ~10-15 seconds
   - Roundtable (3 rounds, 3 experts): ~30-45 seconds

2. **Cache common queries** (client-side)
   - Reduces server load
   - Faster responses for users

3. **Batch unrelated queries** separately
   - Don't combine unrelated topics
   - Better quality responses

---

## Response Time

Typical response times (depending on LLM model and server):

| Query Type | Experts | Time Range |
|------------|---------|------------|
| Single expert | 1 | 2-5 seconds |
| Multi-expert | 2-3 | 8-15 seconds |
| Multi-expert | 4-5 | 15-25 seconds |
| Roundtable (3 rounds) | 2 | 15-20 seconds |
| Roundtable (3 rounds) | 3 | 25-35 seconds |
| Roundtable (3 rounds) | 4 | 35-50 seconds |

**Note:** Times vary based on:
- LLM model speed (llama3.1 vs llama3.2)
- Server hardware (CPU/GPU)
- Query complexity
- Current server load

---

## Changelog

### Version 1.0.0 (Current)

**Features:**
- Multi-expert query endpoint
- Roundtable discussion endpoint
- 10 specialized agricultural experts
- Rate limiting
- Input validation
- Winston logging

**Known Limitations:**
- No authentication
- No response caching
- No streaming responses
- Text-only queries (no image support)

**Planned Features:**
- User authentication (JWT)
- Response caching
- Image analysis capabilities
- Real-time data integration
- WebSocket support for streaming

---

## Support

For API issues or questions:
- **GitHub Issues:** [Report bugs or request features](https://github.com/yourusername/ai-agriculture-advisors/issues)
- **Documentation:** [README.md](README.md)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/ai-agriculture-advisors/discussions)

---

**Last Updated:** November 29, 2025
