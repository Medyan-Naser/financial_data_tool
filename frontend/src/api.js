import axios from "axios";

// Define the base URL of your backend
const API_URL = "http://stocks_tool.local:8000/api/financials";

// Function to fetch financial data for a given ticker
export const getFinancialData = async (ticker) => {
  try {
    const response = await axios.get(`${API_URL}/${ticker}`);
    console.log(response.data); // Log the data to verify its structure
    return response.data; // Return the financial data from the backend
  } catch (error) {
    console.error("Error fetching data", error);
    throw error; // Re-throw error to handle it in the component
  }
};


