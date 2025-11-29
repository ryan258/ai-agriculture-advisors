const config = require('../config/llm');
const OpenRouterProvider = require('./providers/openRouterProvider');
const AnthropicProvider = require('./providers/anthropicProvider');

class LLMFactory {
  /**
   * Creates an LLM provider based on configuration.
   * @returns {BaseProvider} The configured LLM provider instance
   * @throws {Error} If provider type is unsupported
   */
  static createProvider() {
    const providerType = config.provider.toLowerCase();

    switch (providerType) {
      case 'openrouter':
        return new OpenRouterProvider(config.openRouter);
      case 'anthropic':
        return new AnthropicProvider(config.anthropic);
      default:
        throw new Error(`Unsupported LLM provider: ${providerType}`);
    }
  }
}

module.exports = LLMFactory;
