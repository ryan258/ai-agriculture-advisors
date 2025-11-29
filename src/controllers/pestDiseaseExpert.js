const llamaService = require('../services/llamaService');

const { logger } = require('../utils/logger');

class PestDiseaseExpert {
  async processQuery(query) {
    try {
      const prompt = `You are a Pest & Disease Management Expert. Your expertise includes identifying crop diseases, pest life cycles, integrated pest management (IPM), and biological control methods.
    
    User Query: ${query}
    
    Provide a diagnosis if possible and recommend sustainable management strategies, prioritizing non-chemical interventions where appropriate.`;

      const response = await llamaService.generateResponse(prompt);
      return this.processResponse(response);
    } catch (error) {
      logger.error(`Error in PestDiseaseExpert: ${error.message}`);
      throw new Error('Failed to process query in PestDiseaseExpert');
    }
  }

  processResponse(response) {
    return response.trim();
  }
}

module.exports = new PestDiseaseExpert();
