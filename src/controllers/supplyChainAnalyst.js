const llamaService = require('../services/llamaService');

class SupplyChainAnalyst {
  async processQuery(query) {
    try {
      const prompt = `You are a Food Supply Chain Analyst. Your expertise includes mapping global food supply chains, identifying potential disruptions or opportunities, analyzing trends in food processing, distribution, and retail, and evaluating the impact of changing consumer preferences on the agricultural sector.

Please provide insights on food supply chain dynamics addressing the following query:

Query: ${query}

In your response, consider factors such as supply chain efficiency, potential bottlenecks, sustainability concerns, and emerging trends in food distribution and consumer behavior.`;

      const response = await llamaService.generateResponse(prompt);
      return this.processResponse(response);
    } catch (error) {
      console.error('Error in SupplyChainAnalyst:', error);
      throw new Error('Failed to process query in SupplyChainAnalyst');
    }
  }

  processResponse(response) {
    return response.trim();
  }
}

module.exports = new SupplyChainAnalyst();