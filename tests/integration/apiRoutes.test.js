jest.mock('../../src/services/providers/openRouterClient', () => ({
  generateResponse: jest.fn()
}));

const apiRoutes = require('../../src/routes/api');
const roundtableRoutes = require('../../src/routes/roundtable');
const openRouterClient = require('../../src/services/providers/openRouterClient');

const findRouteHandlers = (router, path) => {
  const layer = router.stack.find((item) => item.route && item.route.path === path);
  if (!layer) {
    throw new Error(`Route not found for path: ${path}`);
  }
  return layer.route.stack.map((s) => s.handle);
};

const createMockRes = () => {
  const res = {};
  res.statusCode = 200;
  res.status = jest.fn(function status(code) {
    res.statusCode = code;
    return res;
  });
  res.json = jest.fn(function json(payload) {
    res.body = payload;
    return res;
  });
  return res;
};

const runHandlers = async(handlers, req) => {
  const res = createMockRes();
  for (const handler of handlers) {
    let nextCalled = false;
    await handler(req, res, (err) => {
      nextCalled = true;
      if (err) throw err;
    });
    if (!nextCalled) {
      break;
    }
  }
  return res;
};

describe('API routes', () => {
  const queryHandlers = findRouteHandlers(apiRoutes, '/query');
  const roundtableHandlers = findRouteHandlers(roundtableRoutes, '/');

  beforeEach(() => {
    openRouterClient.generateResponse.mockReset();
  });

  test('POST /api/query returns responses for selected experts', async() => {
    openRouterClient.generateResponse.mockResolvedValue('stub response');

    const req = {
      body: { query: 'Test query', expertRoles: ['agriculture', 'climate'] }
    };

    const res = await runHandlers(queryHandlers, req);

    expect(res.statusCode).toBe(200);
    expect(res.body.responses.agriculture.response).toBe('stub response');
    expect(res.body.responses.climate.response).toBe('stub response');
    expect(openRouterClient.generateResponse).toHaveBeenCalledTimes(2);
  });

  test('POST /api/query rejects invalid payloads', async() => {
    const req = { body: { expertRoles: [] } };

    const res = await runHandlers(queryHandlers, req);

    expect(res.statusCode).toBe(400);
    expect(res.body.message).toContain('Query is required');
    expect(openRouterClient.generateResponse).not.toHaveBeenCalled();
  });

  test('POST /api/roundtable builds a transcript and summary', async() => {
    openRouterClient.generateResponse.mockResolvedValue('stub response');

    const req = {
      body: {
        query: 'Roundtable topic',
        expertRoles: ['agriculture', 'climate'],
        rounds: 2
      }
    };

    const res = await runHandlers(roundtableHandlers, req);

    expect(res.statusCode).toBe(200);
    expect(res.body.transcript).toHaveLength(4); // 2 experts * 2 rounds
    expect(res.body.finalAnswer).toBe('stub response');
    expect(openRouterClient.generateResponse).toHaveBeenCalledTimes(5); // 4 contributions + 1 summary
  });
});
