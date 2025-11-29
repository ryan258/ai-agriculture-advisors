const llamaService = require('../services/llamaService');

const { logger } = require('../utils/logger');

class AgriculturalEconomicsAdvisor {
    async processQuery(query) {
        try {
            const prompt = `You are an Agricultural Economics Advisor. Your expertise covers farm budgeting, market analysis, crop insurance, subsidies, and financial planning for agribusinesses.
    
    User Query: ${query}
    
    Provide financial analysis, risk assessment, or economic advice to help the user make profitable and sustainable business decisions.`;

            const response = await llamaService.generateResponse(prompt);
            return this.processResponse(response);
        } catch (error) {
            logger.error(`Error in AgriculturalEconomicsAdvisor: ${error.message}`);
            throw new Error('Failed to process query in AgriculturalEconomicsAdvisor');
        }
    }

    processResponse(response) {
        return response.trim();
    }
}

module.exports = new AgriculturalEconomicsAdvisor();
