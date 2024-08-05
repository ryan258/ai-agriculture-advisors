const mongoose = require('mongoose');

const supplyChainDataSchema = new mongoose.Schema({
  product: { type: String, required: true },
  origin: {
    location: String,
    coordinates: {
      type: { type: String, default: 'Point' },
      coordinates: [Number]
    }
  },
  destination: {
    location: String,
    coordinates: {
      type: { type: String, default: 'Point' },
      coordinates: [Number]
    }
  },
  transportMethod: String,
  departureDate: Date,
  arrivalDate: Date,
  quantity: Number,
  unit: String,
  quality: {
    grade: String,
    certifications: [String]
  },
  storageFacilities: [{
    location: String,
    capacity: Number,
    conditions: {
      temperature: Number,
      humidity: Number
    }
  }],
  processingSteps: [{
    step: String,
    location: String,
    duration: Number
  }],
  costs: {
    production: Number,
    transportation: Number,
    storage: Number,
    processing: Number
  },
  traceability: {
    batchNumber: String,
    blockchainReference: String
  },
  sustainabilityMetrics: {
    carbonFootprint: Number,
    waterUsage: Number,
    wasteGenerated: Number
  },
  risks: [{
    type: String,
    probability: Number,
    impact: Number,
    mitigationStrategy: String
  }]
}, { timestamps: true });

supplyChainDataSchema.index({ 'origin.coordinates': '2dsphere', 'destination.coordinates': '2dsphere' });

module.exports = mongoose.model('SupplyChainData', supplyChainDataSchema);