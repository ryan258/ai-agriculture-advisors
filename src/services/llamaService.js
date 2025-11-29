const API_URL = process.env.LLAMA_API_URL || 'http://localhost:11434/api/generate';
const MODEL_NAME = process.env.LLAMA_MODEL_NAME || 'llama3.1:latest';

class LlamaService {
  async generateResponse(prompt) {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: MODEL_NAME,
          prompt: prompt,
          stream: false
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.response;
    } catch (error) {
      console.error('Error calling Ollama API:', error);
      throw new Error('Failed to generate response from LLaMA model');
    }
  }
}

module.exports = new LlamaService();