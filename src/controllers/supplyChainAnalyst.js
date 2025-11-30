const openRouterClient = require('../services/providers/openRouterClient');
const { logger } = require('../utils/logger');

class SupplyChainAnalyst {
  async processQuery(query) {
    try {
      const prompt = `You are a Food Supply Chain Analyst. Your expertise includes mapping global food supply chains, identifying potential disruptions or opportunities, analyzing trends in food processing, distribution, and retail, and evaluating the impact of changing consumer preferences on the agricultural sector.

Please provide insights on food supply chain dynamics addressing the following query:

Query: ${query}

In your response, consider factors such as supply chain efficiency, potential bottlenecks, sustainability concerns, and emerging trends in food distribution and consumer behavior.`;

      const response = await openRouterClient.generateResponse(prompt);
      return this.processResponse(response);
    } catch (error) {
      logger.error(`Error in SupplyChainAnalyst: ${error.message}`);
      throw new Error('Failed to process query in SupplyChainAnalyst');
    }
  }

  processResponse(response) {
    return response.trim();
  }
}

module.exports = new SupplyChainAnalyst();
