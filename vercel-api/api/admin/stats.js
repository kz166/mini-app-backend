// api/admin/stats.js
const clientPromise = require('../../lib/mongodb');

const ADMIN_TOKEN = process.env.ADMIN_TOKEN || 'your-secret-admin-token-change-this';

function verifyAdmin(req) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  return token === ADMIN_TOKEN;
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (!verifyAdmin(req)) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const client = await clientPromise;
    const db = client.db('realEstate');

    // Total submissions
    const total = await db.collection('surveys').countDocuments();

    // This month's submissions
    const startOfMonth = new Date();
    startOfMonth.setDate(1);
    startOfMonth.setHours(0, 0, 0, 0);

    const thisMonth = await db.collection('surveys').countDocuments({
      submittedAt: { $gte: startOfMonth }
    });

    // Today's submissions
    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);

    const today = await db.collection('surveys').countDocuments({
      submittedAt: { $gte: startOfDay }
    });

    return res.status(200).json({
      success: true,
      stats: {
        total,
        thisMonth,
        today
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
