// api/survey/submit.js
const clientPromise = require('../../lib/mongodb');

module.exports = async (req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
  );

  // Handle preflight request
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const client = await clientPromise;
    const db = client.db('realEstate');

    const { userId, answers } = req.body;

    // Validate data
    if (!answers || typeof answers !== 'object') {
      return res.status(400).json({ error: 'Invalid data' });
    }

    // Insert survey
    const result = await db.collection('surveys').insertOne({
      userId: userId || 'anonymous',
      answers: answers,
      submittedAt: new Date(),
      ip: req.headers['x-forwarded-for'] || req.connection.remoteAddress,
      userAgent: req.headers['user-agent']
    });

    return res.status(200).json({
      success: true,
      id: result.insertedId.toString(),
      message: 'Survey submitted successfully'
    });

  } catch (error) {
    console.error('Database error:', error);
    return res.status(500).json({
      error: 'Internal server error',
      message: error.message
    });
  }
};
