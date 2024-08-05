const express = require('express');
const router = express.Router();
const AgricultureExpert = require('../controllers/agricultureExpert');
const ClimateAnalyst = require('../controllers/climateAnalyst');
const CommoditiesSpecialist = require('../controllers/commoditiesSpecialist');
const AgritechResearcher = require('../controllers/agritechResearcher');
const SupplyChainAnalyst = require('../controllers/supplyChainAnalyst');

router.post('/query', async (req, res) => {
  try {
    const { query, expertRole } = req.body;
    let response;

    switch (expertRole) {
      case 'agriculture':
        response = await AgricultureExpert.processQuery(query);
        break;
      case 'climate':
        response = await ClimateAnalyst.processQuery(query);
        break;
      case 'commodities':
        response = await CommoditiesSpecialist.processQuery(query);
        break;
      case 'agritech':
        response = await AgritechResearcher.processQuery(query);
        break;
      case 'supplychain':
        response = await SupplyChainAnalyst.processQuery(query);
        break;
      default:
        throw new Error('Invalid expert role');
    }

    res.json({ response });
  } catch (error) {
    console.error('Error processing query:', error);
    res.status(500).json({ message: 'Error processing query', error: error.message });
  }
});

module.exports = router;