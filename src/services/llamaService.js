const { logger } = require('../utils/logger');

class LlamaService {
  constructor(apiUrl, modelName, apiKey) {
    this.apiUrl = apiUrl || process.env.OPENROUTER_API_URL || 'https://openrouter.ai/api/v1/chat/completions';
    this.modelName = modelName || process.env.OPENROUTER_MODEL_NAME || 'meta-llama/llama-3.1-8b-instruct:free';
    this.apiKey = apiKey || process.env.OPENROUTER_API_KEY;
  }

  async generateResponse(prompt) {
    try {
      if (!this.apiKey) {
        throw new Error('OPENROUTER_API_KEY is not set in environment variables');
      }

      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.apiKey}`,
          'HTTP-Referer': 'https://github.com/yourusername/ai-agriculture-advisors',
          'X-Title': 'AI Agriculture Advisors'
        },
        body: JSON.stringify({
          model: this.modelName,
          messages: [
            {
              role: 'user',
              content: prompt
            }
          ],
          stream: false
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        logger.error(`OpenRouter API error: ${response.status} - ${JSON.stringify(errorData)}`);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.choices[0].message.content;
    } catch (error) {
      logger.error(`Error calling OpenRouter API: ${error.message}`);
      throw new Error(`Failed to generate response from LLM via OpenRouter: ${error.message}`);
    }
  }
}

module.exports = new LlamaService(); // Export default instance for backward compatibility
module.exports.LlamaService = LlamaService; // Export class for DI
