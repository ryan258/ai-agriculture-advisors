const LLMFactory = require('./llmFactory');
const { logger } = require('../utils/logger');

class LlamaService {
  constructor() {
    this.provider = LLMFactory.createProvider();
  }

  async generateResponse(prompt) {
    try {
      return await this.provider.generateResponse(prompt);
    } catch (error) {
      logger.error(`LlamaService Error: ${error.message}`);
      throw error;
    }
  }
}

module.exports = new LlamaService();
module.exports.LlamaService = LlamaService;
