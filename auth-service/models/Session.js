const mongoose = require('mongoose');

const messageSchema = new mongoose.Schema({
  role: { type: String, enum: ['user', 'agent'], required: true },
  content: { type: String, required: true }
});

const sessionSchema = new mongoose.Schema({
  user_id: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  title: { type: String, default: 'New Chat' },
  messages: [messageSchema]
}, { timestamps: true });

module.exports = mongoose.model('Session', sessionSchema);
