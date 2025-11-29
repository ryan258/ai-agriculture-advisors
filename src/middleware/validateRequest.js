const validateQueryRequest = (req, res, next) => {
  const { query, expertRoles } = req.body;
  if (!query || typeof query !== 'string' || !query.trim()) {
    return res.status(400).json({ message: 'Query is required and must be a non-empty string.' });
  }
  if (!Array.isArray(expertRoles) || expertRoles.length === 0) {
    return res.status(400).json({ message: 'expertRoles must be a non-empty array.' });
  }
  next();
};

const validateRoundtableRequest = (req, res, next) => {
  const { query, expertRoles, rounds } = req.body;
  if (!query || typeof query !== 'string' || !query.trim()) {
    return res.status(400).json({ message: 'Query is required and must be a non-empty string.' });
  }
  if (!Array.isArray(expertRoles) || expertRoles.length < 2) {
    return res.status(400).json({ message: 'At least two experts are required for a round table discussion.' });
  }
  if (rounds && (typeof rounds !== 'number' || rounds < 1)) {
    return res.status(400).json({ message: 'Rounds must be a positive number.' });
  }
  next();
};

module.exports = {
  validateQueryRequest,
  validateRoundtableRequest
};
