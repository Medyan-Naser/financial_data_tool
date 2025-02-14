const express = require('express');
const { Client } = require('pg');
const app = express();
const port = process.env.PORT || 3000;

// Setup PostgreSQL connection
const client = new Client({
  connectionString: "postgresql://neondb_owner:npg_bNBnIuwHj40U@ep-divine-grass-a4kjfwqv-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require",
  ssl: {
    rejectUnauthorized: false,
  },
});

client.connect();

// Endpoint to get the income statement based on the company's ticker
app.get('/income-statement/:ticker', async (req, res) => {
  const { ticker } = req.params;

  try {
    // Query the database to get the income statement for the company
    const result = await client.query(
      'SELECT * FROM income_statement WHERE company_id = $1 ORDER BY year DESC',
      [ticker]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Company not found or no data available.' });
    }

    return res.status(200).json(result.rows);
  } catch (error) {
    console.error('Error fetching income statement:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
});

// Start the server
app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
