const mongoose = require('mongoose');

const marketDataSchema = new mongoose.Schema({
  date: { type: Date, required: true },
  commodity: { type: String, required: true },
  price: {
    value: { type: Number, required: true },
    currency: { type: String, default: 'USD' }
  },
  volume: Number,
  marketType: { type: String, enum: ['spot', 'futures', 'options'] },
  exchange: String,
  openInterest: Number,
  contractSize: Number,
  deliveryMonth: Date,
  supplyDemandFactors: {
    production: Number,
    consumption: Number,
    exports: Number,
    imports: Number,
    endingStocks: Number
  },
  notes: String
}, { timestamps: true });

module.exports = mongoose.model('MarketData', marketDataSchema);
