require('dotenv').config();
const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const rateLimit = require('express-rate-limit');
const cors = require('cors');
const helmet = require('helmet');
const connectDB = require('./config/database');
const apiRoutes = require('./routes/api');
const roundtableRoutes = require('./routes/roundtable');
const { logger } = require('./utils/logger');

const app = express();
const PORT = process.env.PORT || 3000;

// Connect to Database
connectDB();

// Security Middleware
app.use(helmet());
app.use(cors());
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use(limiter);

// Middleware
app.use(bodyParser.json({ limit: '1mb' })); // Limit request size
app.use(bodyParser.urlencoded({ extended: true }));

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, '../public')));

// API routes
app.use('/api', apiRoutes);
app.use('/api/roundtable', roundtableRoutes);

// Serve the HTML file for any other route
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Error Handling Middleware
app.use(require('./middleware/errorHandler'));

app.listen(PORT, () => {
  logger.info(`Server running on port ${PORT}`);
});
