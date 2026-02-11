// api/admin/surveys.js
const clientPromise = require('../../lib/mongodb');

// Simple authentication - you should replace this with real auth
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || 'your-secret-admin-token-change-this';

function verifyAdmin(req) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  return token === ADMIN_TOKEN;
}

module.exports = async (req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization'
  );

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Verify admin
  if (!verifyAdmin(req)) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const client = await clientPromise;
    const db = client.db('realEstate');

    // Get query parameters
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const skip = (page - 1) * limit;

    // Get total count
    const total = await db.collection('surveys').countDocuments();

    // Get surveys
    const surveys = await db.collection('surveys')
      .find({})
      .sort({ submittedAt: -1 })
      .skip(skip)
      .limit(limit)
      .toArray();

    return res.status(200).json({
      success: true,
      data: surveys,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit)
      }
    });

  } catch (error) {
    console.error('Database error:', error);
    return res.status(500).json({
      error: 'Internal server error',
      message: error.message
    });
  }
};
