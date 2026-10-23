
const { ApolloServer } = require('@apollo/server');
const { startStandaloneServer } = require('@apollo/server/standalone');
const fs = require('fs');
const path = require('path');
const pool = require('./db');

// Read GraphQL schema from schema.graphql
const typeDefs = fs.readFileSync(
  path.join(__dirname, 'schema.graphql'),
  'utf8'
);

// Define GraphQL resolvers
const resolvers = {
  Query: {
    // Return all dishes
    dishes: async () => {
      const [rows] = await pool.query(
        'SELECT id, name, price, available FROM dishes'
      );

      return rows.map(row => ({
        ...row,
        price: Number(row.price),
        available: Boolean(row.available)
      }));
    },

    // Return one dish by ID
    dish: async (_, { id }) => {
      const [rows] = await pool.query(
        'SELECT id, name, price, available FROM dishes WHERE id = ?',
        [id]
      );

      if (rows.length === 0) {
        return null;
      }

      const row = rows[0];

      return {
        ...row,
        price: Number(row.price),
        available: Boolean(row.available)
      };
    }
  },

  Mutation: {
    // Add a new dish
    addDish: async (_, { input }) => {
      const {
        name,
        price,
        available = true
      } = input;

      const [result] = await pool.query(
        'INSERT INTO dishes (name, price, available) VALUES (?, ?, ?)',
        [name, price, available]
      );

      const [rows] = await pool.query(
        'SELECT id, name, price, available FROM dishes WHERE id = ?',
        [result.insertId]
      );

      const row = rows[0];

      return {
        ...row,
        price: Number(row.price),
        available: Boolean(row.available)
      };
    }
  }
};

// Start Apollo Server
async function start() {
  const server = new ApolloServer({
    typeDefs,
    resolvers
  });

  const { url } = await startStandaloneServer(server, {
    listen: { port: 4000 }
  });

  console.log(`CampusEats GraphQL API ready at ${url}`);
}

start().catch(error => {
  console.error('Failed to start GraphQL server:', error);
  process.exitCode = 1;
});
