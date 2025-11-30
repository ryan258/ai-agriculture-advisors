require('dotenv').config();

module.exports = {
  openRouter: {
    apiKey: process.env.OPENROUTER_API_KEY,
    apiUrl: process.env.OPENROUTER_API_URL || 'https://openrouter.ai/api/v1/chat/completions',
    model: process.env.OPENROUTER_MODEL_NAME || 'mistralai/mistral-7b-instruct:free'
  }
};
