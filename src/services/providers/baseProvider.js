class BaseProvider {
  constructor(config) {
    this.config = config;
  }

  /**
     * Generates a response from the LLM.
     * @param {string} prompt - The user prompt.
     * @returns {Promise<string>} - The generated text response.
     */
  async generateResponse(prompt) {
    throw new Error(`${this.constructor.name} must implement generateResponse()`);
  }
}

module.exports = BaseProvider;
