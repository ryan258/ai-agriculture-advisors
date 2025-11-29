const mongoose = require('mongoose');

const agriculturalDataSchema = new mongoose.Schema({
  cropType: String,
  soil: {
    type: String,
    ph: Number,
    nutrients: {
      nitrogen: Number,
      phosphorus: Number,
      potassium: Number
    }
  },
  climate: {
    temperature: Number,
    humidity: Number,
    rainfall: Number
  },
  yield: Number,
  date: { type: Date, default: Date.now }
});

module.exports = mongoose.model('AgriculturalData', agriculturalDataSchema);
