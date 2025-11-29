const openRouterClient = require('../services/providers/openRouterClient');

const { logger } = require('../utils/logger');

class IrrigationSpecialist {
  async processQuery(query) {
    try {
      const prompt = `You are an Irrigation & Water Management Specialist. Your expertise covers irrigation systems (drip, sprinkler, flood), water conservation, scheduling, and water quality analysis.
    
    User Query: ${query}
    
    Provide advice on efficient water use, system design, or troubleshooting, keeping sustainability and cost-effectiveness in mind.`;

      const response = await openRouterClient.generateResponse(prompt);
      return this.processResponse(response);
    } catch (error) {
      logger.error(`Error in IrrigationSpecialist: ${error.message}`);
      throw new Error('Failed to process query in IrrigationSpecialist');
    }
  }

  processResponse(response) {
    return response.trim();
  }
}

module.exports = new IrrigationSpecialist();
