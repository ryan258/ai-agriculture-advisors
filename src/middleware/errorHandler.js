const { logger } = require('../utils/logger');

const errorHandler = (err, req, res, next) => {
    logger.error(err.stack);
    res.status(500).json({
        message: 'Internal Server Error',
        error: process.env.NODE_ENV === 'production' ? 'An unexpected error occurred' : err.message
    });
};

module.exports = errorHandler;
