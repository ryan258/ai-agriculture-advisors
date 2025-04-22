const express = require('express');
const router = express.Router();
const AgricultureExpert = require('../controllers/agricultureExpert');
const ClimateAnalyst = require('../controllers/climateAnalyst');
const CommoditiesSpecialist = require('../controllers/commoditiesSpecialist');
const AgritechResearcher = require('../controllers/agritechResearcher');
const SupplyChainAnalyst = require('../controllers/supplyChainAnalyst');
const { logInteraction } = require('../utils/logger');

router.post('/query', async (req, res) => {
  try {
    const { query, expertRoles } = req.body; // expertRoles: array of roles
    if (!Array.isArray(expertRoles) || expertRoles.length === 0) {
      return res.status(400).json({ message: 'expertRoles must be a non-empty array.' });
    }

    // Map role string to expert instance
    const expertMap = {
      agriculture: AgricultureExpert,
      climate: ClimateAnalyst,
      commodities: CommoditiesSpecialist,
      agritech: AgritechResearcher,
      supplychain: SupplyChainAnalyst
    };

    // Prepare promises for each expert
    const responsePromises = expertRoles.map(async (role) => {
      const expert = expertMap[role];
      if (!expert) {
        return { role, error: 'Invalid expert role' };
      }
      try {
        const resp = await expert.processQuery(query);
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