require('dotenv').config();

const config = {
  provider: process.env.LLM_PROVIDER || 'openrouter',
  openRouter: {
    apiKey: process.env.OPENROUTER_API_KEY,
    apiUrl: process.env.OPENROUTER_API_URL || 'https://openrouter.ai/api/v1/chat/completions',
    model: process.env.OPENROUTER_MODEL_NAME || 'meta-llama/llama-3.1-8b-instruct:free'
  },
  anthropic: {
    apiKey: process.env.ANTHROPIC_API_KEY,
    apiUrl: 'https://api.anthropic.com/v1/messages',
    model: 'claude-3-sonnet-20240229'
  }
};

module.exports = config;
