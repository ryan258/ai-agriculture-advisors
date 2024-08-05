const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const { marked } = require('marked');
const apiRoutes = require('./routes/api');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(bodyParser.json());

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, '../public')));

// Middleware to convert markdown to HTML
app.use((req, res, next) => {
  res.markdown = (md) => {
    const html = marked(md);
    res.send(html);
  };
  next();
});

// API routes
app.use('/api', apiRoutes);

// Serve the HTML file for any other route
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});