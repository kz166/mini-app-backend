// api/index.js - Test endpoint
module.exports = (req, res) => {
  res.status(200).json({
    message: 'Backend API is working!',
    timestamp: new Date().toISOString()
  });
};
