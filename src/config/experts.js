const AgricultureExpert = require('../controllers/agricultureExpert');
const ClimateAnalyst = require('../controllers/climateAnalyst');
const CommoditiesSpecialist = require('../controllers/commoditiesSpecialist');
const AgritechResearcher = require('../controllers/agritechResearcher');
const SupplyChainAnalyst = require('../controllers/supplyChainAnalyst');

const expertMap = {
    agriculture: { instance: AgricultureExpert, label: 'Agricultural Science Expert' },
    climate: { instance: ClimateAnalyst, label: 'Climate Change Impact Analyst' },
    commodities: { instance: CommoditiesSpecialist, label: 'Commodities Trading Specialist' },
    agritech: { instance: AgritechResearcher, label: 'AgriTech Innovation Researcher' },
    supplychain: { instance: SupplyChainAnalyst, label: 'Food Supply Chain Analyst' }
};

module.exports = expertMap;
