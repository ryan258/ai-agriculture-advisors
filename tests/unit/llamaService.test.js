const { LlamaService } = require('../../src/services/llamaService');
const LLMFactory = require('../../src/services/llmFactory');

// Mock LLMFactory and the provider
jest.mock('../../src/services/llmFactory');

describe('LlamaService', () => {
    let service;
    let mockProvider;

    beforeEach(() => {
        mockProvider = {
            generateResponse: jest.fn()
        };
        LLMFactory.createProvider.mockReturnValue(mockProvider);
        service = new LlamaService();
    });

    test('delegates generateResponse to the provider', async () => {
        mockProvider.generateResponse.mockResolvedValue('Provider response');

        const result = await service.generateResponse('Test prompt');

        expect(result).toBe('Provider response');
        expect(mockProvider.generateResponse).toHaveBeenCalledWith('Test prompt');
    });

    test('propagates errors from the provider', async () => {
        const error = new Error('Provider error');
        mockProvider.generateResponse.mockRejectedValue(error);

        await expect(service.generateResponse('Test prompt')).rejects.toThrow('Provider error');
    });
});
