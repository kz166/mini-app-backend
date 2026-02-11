// test-connection.js - Test MongoDB connection
require('dotenv').config({ path: '.env.local' });
const { MongoClient } = require('mongodb');

async function testConnection() {
  console.log('Testing MongoDB connection...\n');

  const uri = process.env.MONGODB_URI;

  if (!uri) {
    console.error('Error: MONGODB_URI not found');
    console.log('Make sure .env.local exists and contains MONGODB_URI');
    process.exit(1);
  }

  console.log('Connection string:', uri.replace(/:[^:@]+@/, ':****@'));
  console.log('');

  const client = new MongoClient(uri);

  try {
    console.log('Connecting to MongoDB Atlas...');
    await client.connect();
    console.log('Connected successfully!\n');

    const db = client.db('realEstate');
    console.log('Database: realEstate');

    console.log('Testing insert...');
    const result = await db.collection('surveys').insertOne({
      test: true,
      message: 'Test data',
      timestamp: new Date()
    });
    console.log('Insert OK! ID:', result.insertedId);

    console.log('Testing query...');
    const count = await db.collection('surveys').countDocuments();
    console.log('Total records:', count);

    await db.collection('surveys').deleteOne({ test: true });
    console.log('Test data cleaned up\n');

    console.log('All tests passed! MongoDB configured correctly.');

  } catch (error) {
    console.error('Connection failed:', error.message);
    process.exit(1);
  } finally {
    await client.close();
  }
}

testConnection();
