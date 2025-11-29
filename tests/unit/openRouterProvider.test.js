const OpenRouterProvider = require('../../src/services/providers/openRouterProvider');

// Mock global fetch
global.fetch = jest.fn();

describe('OpenRouterProvider', () => {
    let provider;
    const mockConfig = {
        apiKey: 'test-key',
        apiUrl: 'https://test.api',
        model: 'test-model'
    };

    beforeEach(() => {
        fetch.mockClear();
        provider = new OpenRouterProvider(mockConfig);
    });

    test('generateResponse returns content on success', async () => {
        const mockResponse = {
            ok: true,
            json: async () => ({
                choices: [{ message: { content: 'Test response' } }]
            })
        };
        fetch.mockResolvedValue(mockResponse);

        const result = await provider.generateResponse('Test prompt');
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

        await expect(provider.generateResponse('Test prompt'))
            .rejects
            .toThrow('HTTP error! status: 500');
    });

    test('throws error when API key is missing', async () => {
        const noKeyProvider = new OpenRouterProvider({ ...mockConfig, apiKey: null });
        await expect(noKeyProvider.generateResponse('Test prompt'))
            .rejects
            .toThrow('OpenRouter API key is not configured');
    });
});
