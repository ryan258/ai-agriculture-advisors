const llamaService = require('../services/llamaService');

class ClimateAnalyst {
  async processQuery(query) {
    try {
      const prompt = `You are a Climate Change Impact Analyst specializing in agriculture. Your expertise includes assessing how climate change affects different agricultural regions, forecasting weather patterns and their potential impact on crop yields, and identifying climate-resilient crops and farming methods.

Please provide a detailed analysis addressing the following query:

Query: ${query}

In your response, consider factors such as temperature changes, precipitation patterns, extreme weather events, and their impacts on agricultural productivity. If relevant, discuss potential adaptation strategies for farmers.`;

      const response = await llamaService.generateResponse(prompt);
      return this.processResponse(response);
    } catch (error) {
      console.error('Error in ClimateAnalyst:', error);
      throw new Error('Failed to process query in ClimateAnalyst');
    }
  }

  processResponse(response) {
    return response.trim();
  }
}

module.exports = new ClimateAnalyst();