const mongoose = require('mongoose');

const cropDataSchema = new mongoose.Schema({
  cropType: { type: String, required: true },
  variety: String,
  plantingDate: Date,
  harvestDate: Date,
  yield: { type: Number, required: true },
  soil: {
    type: { type: String, required: true },
    ph: Number,
    nutrients: {
      nitrogen: Number,
      phosphorus: Number,
      potassium: Number
    },
    organicMatter: Number
  },
  irrigation: {
    method: String,
    frequency: Number,
    amount: Number
  },
  pesticides: [{
    name: String,
    applicationDate: Date,
    amount: Number
  }],
  fertilizers: [{
    name: String,
    applicationDate: Date,
    amount: Number
  }],
  notes: String
}, { timestamps: true });

module.exports = mongoose.model('CropData', cropDataSchema);