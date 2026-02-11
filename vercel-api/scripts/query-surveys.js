#!/usr/bin/env node
// scripts/query-surveys.js
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '.env.local') });
const { MongoClient } = require('mongodb');

async function querySurveys() {
  const client = new MongoClient(process.env.MONGODB_URI);

  try {
    await client.connect();
    const db = client.db('realEstate');

    const surveys = await db.collection('surveys')
      .find({})
      .sort({ submittedAt: -1 })
      .limit(10)
      .toArray();

    console.log('Recent 10 survey records:\n');
    surveys.forEach((survey, index) => {
      console.log(`${index + 1}. ID: ${survey._id}`);
      console.log(`   User: ${survey.userId}`);
      console.log(`   Time: ${new Date(survey.submittedAt).toLocaleString('zh-CN')}`);
      console.log(`   Answers: ${JSON.stringify(survey.answers, null, 2)}`);
      console.log('');
    });

    const total = await db.collection('surveys').countDocuments();
    console.log(`Total: ${total} records`);

  } finally {
    await client.close();
  }
}

querySurveys().catch(console.error);
