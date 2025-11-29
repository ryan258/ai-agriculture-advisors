const express = require('express');
const router = express.Router();
const expertMap = require('../config/experts');
const { logInteraction } = require('../utils/logger');

const { validateQueryRequest } = require('../middleware/validateRequest');

router.post('/query', validateQueryRequest, async (req, res) => {
  try {
    const { query, expertRoles } = req.body; // expertRoles: array of roles

    // Prepare promises for each expert
    const responsePromises = expertRoles.map(async (role) => {
      const expertEntry = expertMap[role];
      if (!expertEntry) {
        return { role, error: 'Invalid expert role' };
      }
      try {
        const resp = await expertEntry.instance.processQuery(query);
        await logInteraction(role, query, resp);
        return { role, response: resp };
      } catch (err) {
        return { role, error: err.message };
      }
    });

    const results = await Promise.all(responsePromises);
    // Structure as { role: response/error }
    const aggregated = {};
    results.forEach(({ role, response, error }) => {
      aggregated[role] = error ? { error } : { response };
    });

    res.json({ responses: aggregated });
  } catch (error) {
    console.error('Error processing multi-expert query:', error);
    res.status(500).json({ message: 'Error processing query', error: error.message });
  }
});

module.exports = router;