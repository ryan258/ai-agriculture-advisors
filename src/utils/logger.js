const winston = require('winston');

// Define log format
const logFormat = winston.format.printf(({ level, message, timestamp }) => {
  return `${timestamp} [${level}]: ${message}`;
});

// Create logger instance
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    logFormat
  ),
  transports: [
    // Write all logs with importance level of `error` or less to `error.log`
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    // Write all logs with importance level of `info` or less to `combined.log`
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

// If we're not in production then log to the `console` with the format:
// `${info.level}: ${info.message} JSON.stringify({ ...rest }) `
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple()
  }));
}

// Legacy helper for backward compatibility with existing code
async function logInteraction(expertRole, query, response) {
  logger.info(`Interaction - Expert: ${expertRole} | Query: ${query} | Response: ${response.substring(0, 50)}...`);
  // We could also keep writing to the text file if strictly needed, but Winston is better.
  // For now, let's rely on Winston's combined.log
}

module.exports = { logger, logInteraction };
