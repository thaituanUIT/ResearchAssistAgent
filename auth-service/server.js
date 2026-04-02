const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const User = require('./models/User');
const Session = require('./models/Session');

const app = express();
app.use(express.json());
app.use(cors());

const PORT = process.env.PORT || 5000;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/researchassist';
const JWT_SECRET = process.env.JWT_SECRET || 'supersecretjwtkey';

mongoose.connect(MONGO_URI)
  .then(() => console.log('MongoDB Connected'))
  .catch(err => console.error('MongoDB connection error:', err));

// Middleware for JWT verify
const protect = (req, res, next) => {
  let token = req.headers.authorization;
  if (token && token.startsWith('Bearer')) {
    try {
      token = token.split(' ')[1];
      const decoded = jwt.verify(token, JWT_SECRET);
      req.user = decoded;
      next();
    } catch (e) {
      res.status(401).json({ error: 'Not authorized, token failed' });
    }
  } else {
    res.status(401).json({ error: 'Not authorized, no token' });
  }
};

// Auth Routes
app.post('/api/auth/register', async (req, res) => {
  const { username, password } = req.body;
  try {
    const userExists = await User.findOne({ username });
    if (userExists) return res.status(400).json({ error: 'User already exists' });
    
    const user = await User.create({ username, password_hash: password });
    const token = jwt.sign({ id: user._id }, JWT_SECRET, { expiresIn: '30d' });
    res.status(201).json({ _id: user._id, username: user.username, token });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/auth/login', async (req, res) => {
  const { username, password } = req.body;
  try {
    const user = await User.findOne({ username });
    if (user && (await user.matchPassword(password))) {
      const token = jwt.sign({ id: user._id }, JWT_SECRET, { expiresIn: '30d' });
      res.json({ _id: user._id, username: user.username, token });
    } else {
      res.status(401).json({ error: 'Invalid username or password' });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Session Routes
app.get('/api/sessions', protect, async (req, res) => {
  try {
    const sessions = await Session.find({ user_id: req.user.id }).sort({ updatedAt: -1 });
    res.json(sessions);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/sessions', protect, async (req, res) => {
  try {
    const session = await Session.create({ user_id: req.user.id, title: req.body.title || 'New Chat', messages: req.body.messages || [] });
    res.status(201).json(session);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/sessions/:id', protect, async (req, res) => {
  try {
    const session = await Session.findOne({ _id: req.params.id, user_id: req.user.id });
    if (!session) return res.status(404).json({ error: 'Session not found' });
    res.json(session);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.put('/api/sessions/:id', protect, async (req, res) => {
  try {
    const session = await Session.findOne({ _id: req.params.id, user_id: req.user.id });
    if (!session) return res.status(404).json({ error: 'Session not found' });
    
    // Updates
    if (req.body.title) session.title = req.body.title;
    if (req.body.messages) {
      session.messages = req.body.messages;
    }
    
    const updated = await session.save();
    res.json(updated);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.delete('/api/sessions/:id', protect, async (req, res) => {
  try {
    const session = await Session.findOneAndDelete({ _id: req.params.id, user_id: req.user.id });
    if (!session) return res.status(404).json({ error: 'Session not found' });
    res.json({ message: 'Session removed' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => console.log(`Auth/Session Microservice running on port ${PORT}`));
