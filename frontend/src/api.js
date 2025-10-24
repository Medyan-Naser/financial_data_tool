import axios from "axios";

// Define the base URL of your backend
const API_BASE_URL = "http://localhost:8000";

/**
 * Check if a ticker has cached data
 */
export const checkCacheStatus = async (ticker) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/financials/cache/status/${ticker}`);
    return response.data;
  } catch (error) {
    console.error("Error checking cache status", error);
    return { cached: false };
  }
};

/**
 * Get cached financial data (fast, no collection)
 */
export const getCachedFinancialData = async (ticker) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/financials/cached/${ticker}`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      return null; // Not cached
    }
    throw error;
  }
};

/**
 * Collect financial data with progress tracking using SSE
 * 
 * @param {string} ticker - Stock ticker symbol
 * @param {number} years - Number of years to collect (default: 15)
 * @param {boolean} forceRefresh - Force refresh even if cached
 * @param {function} onProgress - Callback for progress updates
 * @returns {Promise} - Resolves with complete data
 */
export const collectFinancialData = (ticker, years = 15, forceRefresh = false, onProgress) => {
  return new Promise((resolve, reject) => {
    const url = `${API_BASE_URL}/api/financials/collect/${ticker}?years=${years}&force_refresh=${forceRefresh}`;
    
    // Create EventSource for SSE
    const eventSource = new EventSource(url);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Call progress callback
        if (onProgress) {
          onProgress(data);
        }
        
        // Check if complete
        if (data.status === 'complete') {
          eventSource.close();
          resolve(data.data);
        } else if (data.status === 'error') {
          eventSource.close();
          reject(new Error(data.message));
        }
      } catch (error) {
        console.error("Error parsing SSE data:", error);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error("SSE error:", error);
      eventSource.close();
      reject(new Error("Connection error during data collection"));
    };
  });
};

/**
 * Refresh financial data (force re-collection)
 */
export const refreshFinancialData = (ticker, years = 15, onProgress) => {
  return collectFinancialData(ticker, years, true, onProgress);
};

/**
 * Legacy function to fetch financial data for a given ticker
 * (kept for backward compatibility with old code)
 */
export const getFinancialData = async (ticker) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/financials/${ticker}`);
    console.log(response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching data", error);
    throw error;
  }
};
