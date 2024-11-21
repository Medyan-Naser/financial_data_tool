import axios from "axios";

const API_URL = "http://stocks_tool.local:8000/data";

export const getFinancialData = async () => {
  try {
    const response = await axios.get(API_URL);
    console.log(response.data);  // Log the data to check its structure
    return response.data;
  } catch (error) {
    console.error("Error fetching data", error);
    throw error;
  }
};
