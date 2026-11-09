// server.js -- the CampusEats Catalogue REST API (Node + Express)
require('dotenv').config();

const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const app = express();

// Users with different roles
const users = [
  {
    id: 1,
    username: 'alice',
    password: bcrypt.hashSync('alice123', 10),
    role: 'customer'
  },
  {
    id: 2,
    username: 'restaurant1',
    password: bcrypt.hashSync('rest123', 10),
    role: 'restaurant'
  }
];

app.use(express.json());            // read JSON request bodies
app.use(express.static('public'));  // serve the web page

// the menu -- in memory for now (a real database comes in Lecture 10)
let items = [
  { id: 1, name: 'Veg Thali', price: 90, veg: true },
  { id: 2, name: 'Paneer Roll', price: 70, veg: true },
];
let nextId = 3;

// POST /login --authenticate user and generate JWT

app.post('/login', (req,res)=>{
  const {username , password }= req.body ;

  // find user by unsername 

  const user = users.find(u=>u.username===username);

  //chek user and password 
  if(!user || !bcrypt.compareSync(password , user.password)){
    return res.status(401).json({
      error : 'invalid username or password'
    });
  }

  // Generate JWT token'
  const token =jwt.sign({
    id : user.id ,
    role : user.role
  },
  process.env.JWT_SECRET,
  {
    expiresIn :'1h'
  }
);
// send token
res.json({
  message : 'login successful',
  token : token 
});
});

// Authentication middleware
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];

  if (!authHeader) {
    return res.status(401).json({ error: 'token required' });
  }

  const token = authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'token required' });
  }

  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(401).json({ error: 'invalid or expired token' });
    }

    req.user = user;
    next();
  });
}

// access to action
function requireRole(...allowedRoles) {
  return (req, res, next) => {
    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({
        error: 'forbidden: insufficient permissions'
      });
    }

    next();
  };
}

// GET /items -- list menu with optional veg filter
app.get('/items', authenticateToken , (req, res) => {

  // Read query parameter
  const veg = req.query.veg;

  // If veg=true, return vegetarian dishes only
  if (veg === 'true') {
    const vegetarianItems = items.filter(i => i.veg === true);

    return res.json(vegetarianItems);
  }

  // Otherwise return the complete menu
  res.json(items);
});


// GET /items/:id  -- one dish, or 404
app.get('/items/:id', authenticateToken ,(req, res) => {
  const item = items.find(i => i.id === Number(req.params.id));
  if (!item) return res.status(404).json({ error: 'not found' });
  res.json(item);
});

// DELETE /items/:id -- remove one dish
app.delete('/items/:id', authenticateToken, requireRole('restaurant'),(req, res) => {
  const id = Number(req.params.id);

  // Find the dish
  const index = items.findIndex(i => i.id === id);

  // If dish does not exist
  if (index === -1) {
    return res.status(404).json({ error: 'not found' });
  }

  // Remove the dish from the array
  items.splice(index, 1);

  // Successfully deleted
  res.status(204).end();
});

// POST /items -- add a dish
app.post('/items',authenticateToken, requireRole('restaurant'), (req, res) => {

  const { name, price, veg } = req.body;

  if (!name) {
    return res.status(422).json({ error: 'name required' });
  }

  const item = {
    id: nextId++,
    name,
    price: Number(price) || 0,
    veg: veg === true
  };

  items.push(item);

  res.status(201).json(item);
});


app.listen(3000, () => console.log('Catalogue on http://localhost:3000'));
