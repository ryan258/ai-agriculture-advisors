const mongoose = require('mongoose');

const agriTechDataSchema = new mongoose.Schema({
  technology: { type: String, required: true },
  category: { type: String, enum: ['precision agriculture', 'farm management software', 'sensors', 'robotics', 'AI/ML', 'other'] },
  implementationDate: Date,
  vendor: String,
  cost: {
    value: Number,
    currency: { type: String, default: 'USD' }
  },
  impact: {
    yieldIncrease: Number,
    costReduction: Number,
    laborSavings: Number,
    waterConservation: Number,
    pesticideReduction: Number,
    fertilizerEfficiency: Number
  },
  adopters: Number,
  successRate: Number,
  challenges: [String],
  integration: {
    compatibleSystems: [String],
    dataFormats: [String]
  },
  roi: Number,
  feedback: [{
    user: String,
    rating: Number,
    comment: String,
    date: Date
  }],
  futureProspects: String
}, { timestamps: true });

module.exports = mongoose.model('AgriTechData', agriTechDataSchema);
