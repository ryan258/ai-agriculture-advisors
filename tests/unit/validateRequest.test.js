const { validateQueryRequest } = require('../../src/middleware/validateRequest');

describe('validateQueryRequest', () => {
    let req, res, next;

    beforeEach(() => {
        req = { body: {} };
        res = {
            status: jest.fn().mockReturnThis(),
            json: jest.fn()
        };
        next = jest.fn();
    });

    test('calls next() for valid request', () => {
        req.body = {
            query: 'Valid query',
            expertRoles: ['agriculture']
        };
        validateQueryRequest(req, res, next);
        expect(next).toHaveBeenCalled();
        expect(res.status).not.toHaveBeenCalled();
    });

    test('returns 400 if query is missing', () => {
        req.body = {
            expertRoles: ['agriculture']
        };
        validateQueryRequest(req, res, next);
        expect(res.status).toHaveBeenCalledWith(400);
        expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
            message: expect.stringContaining('Query is required')
        }));
        expect(next).not.toHaveBeenCalled();
    });

    test('returns 400 if expertRoles is missing', () => {
        req.body = {
            query: 'Valid query'
        };
        validateQueryRequest(req, res, next);
        expect(res.status).toHaveBeenCalledWith(400);
        expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
            message: expect.stringContaining('expertRoles must be')
        }));
        expect(next).not.toHaveBeenCalled();
    });

    test('returns 400 if expertRoles is empty array', () => {
        req.body = {
            query: 'Valid query',
            expertRoles: []
        };
        validateQueryRequest(req, res, next);
        expect(res.status).toHaveBeenCalledWith(400);
        expect(next).not.toHaveBeenCalled();
    });
});
