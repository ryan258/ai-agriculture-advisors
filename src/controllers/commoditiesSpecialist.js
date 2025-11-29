const llamaService = require('../services/llamaService');

class CommoditiesSpecialist {
  async processQuery(query) {
    try {
      const prompt = `You are a Commodities Trading Specialist focusing on agricultural products. Your expertise includes monitoring global agricultural commodity markets, analyzing supply and demand dynamics for various crops, and identifying trading opportunities based on market trends.

Please provide a detailed market analysis addressing the following query:

Query: ${query}

In your response, consider factors such as current market trends, supply and demand dynamics, price forecasts, and any relevant geopolitical or environmental factors that might impact agricultural commodities.`;

      const response = await llamaService.generateResponse(prompt);
      return this.processResponse(response);
    } catch (error) {
      console.error('Error in CommoditiesSpecialist:', error);
      throw new Error('Failed to process query in CommoditiesSpecialist');
    }
  }

  processResponse(response) {
    return response.trim();
  }
}

module.exports = new CommoditiesSpecialist();
