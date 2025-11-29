const { logger } = require('../utils/logger');

const API_URL = process.env.LLAMA_API_URL || 'http://localhost:11434/api/generate';
const MODEL_NAME = process.env.LLAMA_MODEL_NAME || 'llama3.1:latest';

class LlamaService {
  constructor(apiUrl, modelName) {
    this.apiUrl = apiUrl || process.env.LLAMA_API_URL || 'http://localhost:11434/api/generate';
    this.modelName = modelName || process.env.LLAMA_MODEL_NAME || 'llama3.1:latest';
  }

  async generateResponse(prompt) {
    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: this.modelName,
          prompt: prompt,
          stream: false
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.response;
    } catch (error) {
      logger.error(`Error calling Ollama API: ${error.message}`);
      throw new Error('Failed to generate response from LLaMA model');
    }
  }
}

module.exports = new LlamaService(); // Export default instance for backward compatibility
module.exports.LlamaService = LlamaService; // Export class for DI