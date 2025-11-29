const openRouterClient = require('../services/providers/openRouterClient');

class AgricultureExpert {
  async processQuery(query) {
    try {
      const prompt = `You are an Agricultural Science Expert. Your knowledge spans crop science, soil management, and agricultural practices. You have expertise in analyzing trends in crop yields, pest resistance, and genetic modifications. You can evaluate the potential of new farming techniques and their impact on productivity.

Please provide a detailed, scientific answer to the following query:

Query: ${query}

In your response, consider relevant factors such as soil conditions, climate impact, crop varieties, and modern agricultural practices. If applicable, mention potential challenges and solutions.`;

      const response = await openRouterClient.generateResponse(prompt);
      return this.processResponse(response);
    } catch (error) {
      console.error('Error in AgricultureExpert:', error);
      throw new Error('Failed to process query in AgricultureExpert');
    }
  }

  processResponse(response) {
    // Here you can add any post-processing of the LLaMA response if needed
    return response.trim();
  }
}

module.exports = new AgricultureExpert();
