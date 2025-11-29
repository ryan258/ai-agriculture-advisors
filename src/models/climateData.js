const mongoose = require('mongoose');

const climateDataSchema = new mongoose.Schema({
  date: { type: Date, required: true },
  location: {
    type: { type: String, default: 'Point' },
    coordinates: [Number]
  },
  temperature: {
    average: Number,
    min: Number,
    max: Number
  },
  humidity: Number,
  rainfall: Number,
  windSpeed: Number,
  windDirection: String,
  solarRadiation: Number,
  evapotranspiration: Number,
  growingDegreeDays: Number,
  extremeWeatherEvents: [{
    type: String,
    date: Date,
    description: String
  }]
}, { timestamps: true });

climateDataSchema.index({ location: '2dsphere' });

module.exports = mongoose.model('ClimateData', climateDataSchema);
