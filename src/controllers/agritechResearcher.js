const openRouterClient = require('../services/providers/openRouterClient');
const { logger } = require('../utils/logger');

class AgritechResearcher {
  async processQuery(query) {
    try {
      const prompt = `You are an AgriTech Innovation Researcher. Your expertise includes tracking developments in agricultural technology (such as AI, IoT, and robotics), evaluating the potential of emerging AgriTech companies and their technologies, and assessing the adoption rates of new technologies in different markets.

Please provide insights on agricultural technology innovations addressing the following query:

Query: ${query}

In your response, consider recent technological advancements, their potential impact on agricultural productivity and sustainability, and any challenges or opportunities in their implementation.`;

      const response = await openRouterClient.generateResponse(prompt);
      return this.processResponse(response);
    } catch (error) {
      logger.error(`Error in AgritechResearcher: ${error.message}`);
      throw new Error('Failed to process query in AgritechResearcher');
    }
  }

  processResponse(response) {
    return response.trim();
  }
}

module.exports = new AgritechResearcher();
