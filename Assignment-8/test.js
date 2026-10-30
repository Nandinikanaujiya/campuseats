// test.js — Automated test verification for CampusEats REST API (Assignment 8)
const assert = require('assert');

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';

async function runTests() {
  console.log(`\n========================================`);
  console.log(`Running CS543 Assignment 8 REST API Tests`);
  console.log(`Target Server: ${BASE_URL}`);
  console.log(`========================================\n`);

  let passed = 0;
  let total = 0;

  async function test(name, fn) {
    total++;
    process.stdout.write(`[Test ${total}] ${name} ... `);
    try {
      await fn();
      console.log(`PASSED \u2705`);
      passed++;
    } catch (err) {
      console.log(`FAILED \u274c`);
      console.error(`       Error: ${err.message}`);
    }
  }

  // 1. GET /items
  await test('GET /items returns 200 OK with list of menu dishes', async () => {
    const res = await fetch(`${BASE_URL}/items`);
    assert.strictEqual(res.status, 200, `Expected 200, got ${res.status}`);
    const data = await res.json();
    assert(Array.isArray(data), 'Expected response to be an array');
    assert(data.length >= 4, `Expected at least 4 seed dishes, found ${data.length}`);
    const first = data[0];
    assert.strictEqual(first.id, 1);
    assert.strictEqual(first.name, 'Veg Thali');
    assert.strictEqual(first.price, 90);
    assert.strictEqual(first.available, true);
  });

  // 2. GET /items/:id (Found)
  await test('GET /items/1 returns 200 OK and single dish', async () => {
    const res = await fetch(`${BASE_URL}/items/1`);
    assert.strictEqual(res.status, 200, `Expected 200, got ${res.status}`);
    const item = await res.json();
    assert.strictEqual(item.id, 1);
    assert.strictEqual(item.name, 'Veg Thali');
    assert.strictEqual(item.price, 90);
  });

  // 3. GET /items/:id (Not Found 404)
  await test('GET /items/99 returns 404 Not Found', async () => {
    const res = await fetch(`${BASE_URL}/items/99`);
    assert.strictEqual(res.status, 404, `Expected 404, got ${res.status}`);
    const body = await res.json();
    assert.strictEqual(body.error, 'not found');
  });

  // 4. POST /items (Success 201)
  await test('POST /items adds a valid dish and returns 201 Created', async () => {
    const payload = { name: 'Pav Bhaji Special', price: 80, available: true };
    const res = await fetch(`${BASE_URL}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    assert.strictEqual(res.status, 201, `Expected 201, got ${res.status}`);
    const added = await res.json();
    assert(added.id, 'Expected new dish to have an id');
    assert.strictEqual(added.name, 'Pav Bhaji Special');
    assert.strictEqual(added.price, 80);
    assert.strictEqual(added.available, true);

    // Verify it now exists in the collection
    const verifyRes = await fetch(`${BASE_URL}/items/${added.id}`);
    assert.strictEqual(verifyRes.status, 200);
    const verifyItem = await verifyRes.json();
    assert.strictEqual(verifyItem.name, 'Pav Bhaji Special');
  });

  // 5. POST /items (Validation Failure 422 - Missing Name)
  await test('POST /items without name returns 422 Unprocessable Entity', async () => {
    const payload = { price: 50 };
    const res = await fetch(`${BASE_URL}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    assert.strictEqual(res.status, 422, `Expected 422, got ${res.status}`);
    const body = await res.json();
    assert.strictEqual(body.error, 'name required');
  });

  // 6. POST /items (Validation Failure 422 - Empty Whitespace Name)
  await test('POST /items with empty whitespace name returns 422 Unprocessable', async () => {
    const payload = { name: '   ', price: 50 };
    const res = await fetch(`${BASE_URL}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    assert.strictEqual(res.status, 422, `Expected 422, got ${res.status}`);
    const body = await res.json();
    assert.strictEqual(body.error, 'name required');
  });

  console.log(`\n========================================`);
  console.log(`Result: ${passed}/${total} Tests Passed`);
  console.log(`========================================\n`);

  if (passed !== total) {
    process.exit(1);
  }
}

runTests().catch(err => {
  console.error('Test runner fatal error:', err);
  process.exit(1);
});
