
const pool = require('./db');

async function testConnection() {
  try {
    const [rows] = await pool.query(
      'SELECT id, name, price, available FROM dishes'
    );

    console.log('Database connected successfully!');
    console.table(rows);
  } catch (error) {
    console.error('Database connection failed:', error.message);
  } finally {
    await pool.end();
  }
}

testConnection();
