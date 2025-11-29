const config = require('../../config/llm');
const OpenRouterProvider = require('./openRouterProvider');

// Single OpenRouter provider instance shared across controllers/routes
const openRouterClient = new OpenRouterProvider(config.openRouter);

module.exports = openRouterClient;
