const BaseProvider = require('./baseProvider');

class AnthropicProvider extends BaseProvider {
  async generateResponse(prompt) {
    const { apiKey } = this.config;

    if (!apiKey) {
      throw new Error('Anthropic API key is not configured');
    }

    // Placeholder implementation - requires installing @anthropic-ai/sdk or using fetch
    // For now, we'll simulate a response or throw not implemented if strictly needed.
    // But to make it "work" as a demo if a key is present:

    // Placeholder implementation
    throw new Error('Anthropic provider not yet implemented. Set LLM_PROVIDER=openrouter in .env');
  }
}

module.exports = AnthropicProvider;
