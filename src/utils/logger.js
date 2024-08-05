const fs = require('fs').promises;
const path = require('path');

const logFile = path.join(__dirname, '../../agri-ai.txt');

async function logInteraction(expertRole, query, response) {
    const timestamp = new Date().toISOString();
    const logEntry = `
Timestamp: ${timestamp}
Expert: ${expertRole}
Query: ${query}
Response:
${response}
----------------------------------------
`;

    try {
        await fs.appendFile(logFile, logEntry);
        console.log('Interaction logged successfully');
    } catch (error) {
        console.error('Error writing to log file:', error);
    }
}

module.exports = { logInteraction };