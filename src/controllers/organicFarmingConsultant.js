const llamaService = require('../services/llamaService');

const { logger } = require('../utils/logger');

class OrganicFarmingConsultant {
  async processQuery(query) {
    try {
      const prompt = `You are an Organic Farming Consultant. Your expertise covers organic certification standards, non-GMO practices, natural fertilizers, and holistic farm management.
    
    User Query: ${query}
    
    Provide guidance compliant with organic standards (like USDA Organic or EU Organic), focusing on ecological balance and biodiversity.`;

      const response = await llamaService.generateResponse(prompt);
      return this.processResponse(response);
    } catch (error) {
      logger.error(`Error in OrganicFarmingConsultant: ${error.message}`);
      throw new Error('Failed to process query in OrganicFarmingConsultant');
    }
  }

  processResponse(response) {
    return response.trim();
  }
}

module.exports = new OrganicFarmingConsultant();
