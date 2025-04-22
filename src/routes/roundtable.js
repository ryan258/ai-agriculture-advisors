const express = require('express');
const router = express.Router();
const AgricultureExpert = require('../controllers/agricultureExpert');
const ClimateAnalyst = require('../controllers/climateAnalyst');
const CommoditiesSpecialist = require('../controllers/commoditiesSpecialist');
const AgritechResearcher = require('../controllers/agritechResearcher');
const SupplyChainAnalyst = require('../controllers/supplyChainAnalyst');
const { logInteraction } = require('../utils/logger');

// Helper to map role string to expert instance and label
const expertMap = {
  agriculture: { instance: AgricultureExpert, label: 'Agricultural Science Expert' },
  climate: { instance: ClimateAnalyst, label: 'Climate Change Impact Analyst' },
  commodities: { instance: CommoditiesSpecialist, label: 'Commodities Trading Specialist' },
  agritech: { instance: AgritechResearcher, label: 'AgriTech Innovation Researcher' },
  supplychain: { instance: SupplyChainAnalyst, label: 'Food Supply Chain Analyst' }
};

router.post('/', async (req, res) => {
  try {
    const { query, expertRoles, rounds = 3 } = req.body;
    if (!Array.isArray(expertRoles) || expertRoles.length < 2) {
      return res.status(400).json({ message: 'At least two experts are required for a round table discussion.' });
    }
    if (!query || !query.trim()) {
      return res.status(400).json({ message: 'Query is required.' });
    }

    // Initialize transcript
    let transcript = [];

    // Simulate discussion rounds
    for (let round = 0; round < rounds; round++) {
      for (const role of expertRoles) {
        const expertEntry = expertMap[role];
        if (!expertEntry) {
          transcript.push({ speaker: role, text: 'Invalid expert role.' });
          continue;
        }
        // Compose prompt with transcript so far
        const discussionPrompt = `You are ${expertEntry.label} participating in a round table discussion with other experts.\n\nQuery: ${query}\n\nTranscript so far:\n${transcript.map(msg => msg.speaker + ': ' + msg.text).join('\n')}\n\nAs ${expertEntry.label}, contribute your analysis, critique, or build upon previous points. Be concise, insightful, and aim to move the discussion forward.`;
        try {
          const response = await expertEntry.instance.processQuery(discussionPrompt);
          transcript.push({ speaker: expertEntry.label, text: response });
          await logInteraction(role, `RoundTable|${query}|Round:${round+1}`, response);
        } catch (err) {
          transcript.push({ speaker: expertEntry.label, text: 'Error: ' + err.message });
        }
      }
    }

    // Synthesize final answer
    const summaryPrompt = `You are a moderator. Based on the following transcript of a round table discussion among experts, provide a consensus or next-level answer to the original query.\n\nQuery: ${query}\n\nTranscript:\n${transcript.map(msg => msg.speaker + ': ' + msg.text).join('\n')}\n\nConsensus/Next-level Answer:`;
    // Use the first expert to generate the summary for simplicity
    const summaryExpert = expertMap[expertRoles[0]].instance;
    let finalAnswer = '';
    try {
      finalAnswer = await summaryExpert.processQuery(summaryPrompt);
    } catch (err) {
      finalAnswer = 'Error generating final answer: ' + err.message;
    }

    res.json({ transcript, finalAnswer });
  } catch (error) {
    console.error('Error in round table discussion:', error);
    res.status(500).json({ message: 'Error in round table discussion', error: error.message });
  }
});

module.exports = router;
