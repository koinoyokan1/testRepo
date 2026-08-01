import express from 'express';
import axios from 'axios';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// API Gateway proxy
app.get('/api/*', async (req, res) => {
  try {
    const apiUrl = `http://localhost:8080${req.path}`;
    const response = await axios.get(apiUrl);
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: 'API Gateway error' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'web-frontend' });
});

app.listen(PORT, () => {
  console.log(`Web frontend listening on port ${PORT}`);
});
