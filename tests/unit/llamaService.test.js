const { LlamaService } = require('../../src/services/llamaService');

// Mock global fetch
global.fetch = jest.fn();

describe('LlamaService', () => {
    let service;

    beforeEach(() => {
        fetch.mockClear();
        // Use constructor injection to avoid singleton mutation
        service = new LlamaService(
            'https://test.api',
            'test-model',
            'test-key'
        );
    });

    test('generateResponse returns content on success', async () => {
        const mockResponse = {
            ok: true,
            json: async () => ({
                choices: [{ message: { content: 'Test response' } }]
            })
        };
        fetch.mockResolvedValue(mockResponse);

        const result = await service.generateResponse('Test prompt');
        expect(result).toBe('Test response');
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    test('generateResponse throws error on API failure', async () => {
        const mockResponse = {
            ok: false,
            status: 500,
            json: async () => ({ error: 'Internal Server Error' })
        };
        fetch.mockResolvedValue(mockResponse);

        await expect(service.generateResponse('Test prompt'))
            .rejects
            .toThrow('HTTP error! status: 500');
    });

    test('generateResponse throws error when API key is missing', async () => {
        // Create service without API key
        const noKeyService = new LlamaService('https://test.api', 'test-model', null);

        await expect(noKeyService.generateResponse('Test prompt'))
            .rejects
            .toThrow('OPENROUTER_API_KEY is not set');
    });

    test('handles network errors gracefully', async () => {
        fetch.mockRejectedValue(new Error('Network failure'));

        await expect(service.generateResponse('Test prompt'))
            .rejects
            .toThrow('Failed to generate response from LLM via OpenRouter: Network failure');
    });

    test('handles malformed API response', async () => {
        fetch.mockResolvedValue({
            ok: true,
            json: async () => ({ choices: [] }) // Empty choices, will cause crash when accessing [0]
        });

        // The current implementation will throw TypeError when accessing choices[0]
        // We expect the service to catch it and wrap it
        await expect(service.generateResponse('Test prompt'))
            .rejects
            .toThrow('Failed to generate response from LLM via OpenRouter');
    });
});
