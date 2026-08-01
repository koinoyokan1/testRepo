import express from 'express';
import axios from 'axios';
import * as _ from 'lodash';

const app = express();
const PORT = process.env.PORT || 4000;

app.use(express.json());

app.get('/admin/users', async (req, res) => {
  try {
    const response = await axios.get('http://localhost:8080/api/users');
    const users = _.sortBy(response.data, 'createdAt');
    res.json(users);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch users' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'admin-dashboard' });
});

app.listen(PORT, () => {
  console.log(`Admin dashboard listening on port ${PORT}`);
});
