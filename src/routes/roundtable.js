const express = require('express');
const router = express.Router();
const expertMap = require('../config/experts');
const { logInteraction } = require('../utils/logger');

const { validateRoundtableRequest } = require('../middleware/validateRequest');

router.post('/', validateRoundtableRequest, async(req, res) => {
  try {
    const { query, expertRoles, rounds = 3 } = req.body;

    // Initialize transcript
    const transcript = [];

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
          await logInteraction(role, `RoundTable|${query}|Round:${round + 1}`, response);
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
