const openRouterClient = require('../services/providers/openRouterClient');

const { logger } = require('../utils/logger');

class SoilHealthSpecialist {
  async processQuery(query) {
    try {
      const prompt = `You are a Soil Health Specialist. Your expertise covers soil composition, nutrient management, composting, cover cropping, and regenerative agriculture practices.
    
    User Query: ${query}
    
    Provide a detailed, scientific, yet practical response focusing on improving soil biology, structure, and fertility.`;

      const response = await openRouterClient.generateResponse(prompt);
      return this.processResponse(response);
    } catch (error) {
      logger.error(`Error in SoilHealthSpecialist: ${error.message}`);
      throw new Error('Failed to process query in SoilHealthSpecialist');
    }
  }

  processResponse(response) {
    return response.trim();
  }
}

module.exports = new SoilHealthSpecialist();
