// server.js — CS543 Assignment 8: CampusEats REST API
const express = require('express');
const app = express();

// Middleware
app.use(express.json());           // Read JSON request bodies (req.body)
app.use(express.static('public')); // Serve frontend assets from public/

// In-memory data store for CampusEats Menu/Catalogue (3-4 seed records)
let items = [
  { id: 1, name: 'Veg Thali', price: 90, available: true },
  { id: 2, name: 'Paneer Roll', price: 70, available: true },
  { id: 3, name: 'Masala Dosa', price: 60, available: true },
  { id: 4, name: 'Cold Coffee', price: 45, available: true }
];
let nextId = 5;

// 1. GET /items — List all menu items (200 OK)
app.get('/items', (req, res) => {
  res.status(200).json(items);
});

// 2. GET /items/:id — Fetch a single item by id (200 OK or 404 Not Found)
app.get('/items/:id', (req, res) => {
  const item = items.find(i => i.id === Number(req.params.id));
  if (!item) {
    return res.status(404).json({ error: 'not found' });
  }
  res.status(200).json(item);
});

// 3. POST /items — Add a new menu item (201 Created or 422 Unprocessable)
app.post('/items', (req, res) => {
  const { name, price, available } = req.body;

  // Validation: 'name' is required
  if (!name || typeof name !== 'string' || name.trim() === '') {
    return res.status(422).json({ error: 'name required' });
  }

  const newItem = {
    id: nextId++,
    name: name.trim(),
    price: Number(price) || 0,
    available: available !== undefined ? Boolean(available) : true
  };

  items.push(newItem);
  res.status(201).json(newItem);
});

// Start Express Server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`CampusEats REST API running on http://localhost:${PORT}`);
});
