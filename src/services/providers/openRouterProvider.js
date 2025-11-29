const BaseProvider = require('./baseProvider');
const { logger } = require('../../utils/logger');

class OpenRouterProvider extends BaseProvider {
  async generateResponse(prompt) {
    const { apiKey, apiUrl, model } = this.config;

    if (!apiKey) {
      throw new Error('OpenRouter API key is not configured');
    }

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
          'HTTP-Referer': 'https://github.com/yourusername/ai-agriculture-advisors',
          'X-Title': 'AI Agriculture Advisors'
        },
        body: JSON.stringify({
          model,
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
      throw new Error(`Failed to generate response from OpenRouter: ${error.message}`);
    }
  }
}

module.exports = OpenRouterProvider;
