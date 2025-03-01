const express = require("express");
const cors = require("cors");
const { Client } = require("pg");
const { spawn } = require("child_process");

const app = express();
const port = process.env.PORT || 3000;

// Allowed frontend origins
const allowedOrigins = [
  "https://financial-data-tool-hjkdo28ly-medyans-projects.vercel.app",
  "http://127.0.0.1:3000",
  "http://localhost:3001",
];

app.use(
  cors({
    origin: (origin, callback) => {
      if (!origin || allowedOrigins.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error("Not allowed by CORS"));
      }
    },
    methods: "GET,POST,PUT,DELETE",
    allowedHeaders: "Content-Type",
  })
);

// PostgreSQL connection
const client = new Client({
  connectionString:
    "postgresql://neondb_owner:npg_bNBnIuwHj40U@ep-divine-grass-a4kjfwqv-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require",
  ssl: { rejectUnauthorized: false },
});
client.connect();

// Store cached data from Python scripts
let cachedData = {};

// Function to execute a Python script and return JSON data
const runPythonScript = (scriptName) => {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn("python3", [scriptName]);

    let output = "";
    pythonProcess.stdout.on("data", (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on("data", (data) => {
      console.error(`Python Error (${scriptName}): ${data}`);
      reject(data.toString());
    });

    pythonProcess.on("close", () => {
      try {
        const parsedData = JSON.parse(output.trim());

        if (!Array.isArray(parsedData)) {
          return reject(`Expected an array but got: ${output.trim()}`);
        }

        resolve(parsedData);
      } catch (error) {
        reject(`Failed to parse JSON from ${scriptName}: ${error}`);
      }
    });
  });
};


// Function to load data at startup
const loadInitialData = async () => {
  try {
    console.log("Loading initial data from Python scripts...");
    const [currenciesData] = await Promise.all([
      runPythonScript("../../AI_ML/Macro/currencies.py"), // Add more scripts here later
    ]);

    const [energy, metals, agricultural, industrial, livestock, commodities_index] = await runPythonScript("../../AI_ML/Macro/commodities.py");

    cachedData = {
      currenciesTable: currenciesData,
      energyTable: energy,
      metalsTable: metals,
      agriculturalTable: agricultural,
      industrialTable: industrial,
      livestockTable: livestock,
      commodities_indexTable: commodities_index,
    };
    console.log(energy)
    console.log(metals)

    console.log("Initial data loaded successfully.");
  } catch (error) {
    console.error("Error loading initial data:", error);
  }
};

// Serve cached data
app.get("/", (req, res) => {
  if (!cachedData.currenciesTable) {
    return res.status(500).json({ message: "Data not yet loaded. Try again later." });
  }

  return res.status(200).json({
    message: "Available graphs",
    currenciesTable: cachedData.currenciesTable,
    energyTable: cachedData.energyTable,
    metalsTable: cachedData.metalsTable,
    agriculturalTable: cachedData.agriculturalTable,
    industrialTable: cachedData.industrialTable,
    livestockTable: cachedData.livestockTable,
    commodities_indexTable: cachedData.commodities_indexTable,
  });
});

// Income statement endpoint
app.get("/income-statement/:ticker", async (req, res) => {
  const { ticker } = req.params;

  try {
    const result = await client.query(
      "SELECT * FROM income_statement WHERE company_id = $1 ORDER BY year DESC",
      [ticker]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: "Company not found or no data available." });
    }

    return res.status(200).json(result.rows);
  } catch (error) {
    console.error("Error fetching income statement:", error);
    return res.status(500).json({ message: "Internal server error" });
  }
});

// Start server and load initial data
app.listen(port, async () => {
  console.log(`Server running on http://localhost:${port}`);
  await loadInitialData();
});
