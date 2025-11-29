const AgricultureExpert = require('../controllers/agricultureExpert');
const ClimateAnalyst = require('../controllers/climateAnalyst');
const CommoditiesSpecialist = require('../controllers/commoditiesSpecialist');
const AgritechResearcher = require('../controllers/agritechResearcher');
const SupplyChainAnalyst = require('../controllers/supplyChainAnalyst');
const SoilHealthSpecialist = require('../controllers/soilHealthSpecialist');
const PestDiseaseExpert = require('../controllers/pestDiseaseExpert');
const IrrigationSpecialist = require('../controllers/irrigationSpecialist');
const OrganicFarmingConsultant = require('../controllers/organicFarmingConsultant');
const AgriculturalEconomicsAdvisor = require('../controllers/agriculturalEconomicsAdvisor');

const expertMap = {
  agriculture: { instance: AgricultureExpert, label: 'Agricultural Science Expert' },
  climate: { instance: ClimateAnalyst, label: 'Climate Change Impact Analyst' },
  commodities: { instance: CommoditiesSpecialist, label: 'Commodities Trading Specialist' },
  agritech: { instance: AgritechResearcher, label: 'AgriTech Innovation Researcher' },
  supplychain: { instance: SupplyChainAnalyst, label: 'Food Supply Chain Analyst' },
  soil: { instance: SoilHealthSpecialist, label: 'Soil Health Specialist' },
  pest: { instance: PestDiseaseExpert, label: 'Pest & Disease Management Expert' },
  irrigation: { instance: IrrigationSpecialist, label: 'Irrigation & Water Management Specialist' },
  organic: { instance: OrganicFarmingConsultant, label: 'Organic Farming Consultant' },
  economics: { instance: AgriculturalEconomicsAdvisor, label: 'Agricultural Economics Advisor' }
};

module.exports = expertMap;
