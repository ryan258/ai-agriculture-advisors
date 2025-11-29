const LLMFactory = require('../../src/services/llmFactory');
const config = require('../../src/config/llm');
const OpenRouterProvider = require('../../src/services/providers/openRouterProvider');
const AnthropicProvider = require('../../src/services/providers/anthropicProvider');

jest.mock('../../src/config/llm', () => ({
    provider: 'openrouter',
    openRouter: {},
    anthropic: {}
}));

describe('LLMFactory', () => {
    test('creates OpenRouterProvider when configured', () => {
        config.provider = 'openrouter';
        const provider = LLMFactory.createProvider();
        expect(provider).toBeInstanceOf(OpenRouterProvider);
    });

    test('creates AnthropicProvider when configured', () => {
        config.provider = 'anthropic';
        const provider = LLMFactory.createProvider();
        expect(provider).toBeInstanceOf(AnthropicProvider);
    });

    test('throws error for unsupported provider', () => {
        config.provider = 'unknown';
        expect(() => LLMFactory.createProvider()).toThrow('Unsupported LLM provider');
    });
});
