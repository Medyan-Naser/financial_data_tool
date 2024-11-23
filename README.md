# Financial Data Analysis Tool
This project provides an in-depth analysis and visualization of financial data from publicly listed companies. The project is split into two main stages: Data Collection and Website Development. Below is an overview of each stage and how they contribute to the tool's functionality.

<img src="GIFs/website_demo.gif" alt="Demo" width="600"/>

# Stage 1: Data Collection
In this first stage, the tool collects financial data from the SEC API (U.S. Securities and Exchange Commission). The process is divided into the following steps:

## Data Collection:

The tool fetches financial data for all public companies from the SEC's EDGAR API, covering multiple years.
The data includes key financial metrics such as income statements, balance sheets, and cash flow statements.
- Data Fetching: Retrieve data for public companies from the SEC’s EDGAR API.
- Coverage: Data spans multiple years for a comprehensive view.
- Financial Metrics: Includes income statements, balance sheets, and cash flow statements.

## Data Cleaning:

Once the data is collected, it is parsed and cleaned. This involves:
- Removing irrelevant information.
- Converting data formats for easier processing and analysis.
- Handling missing or inconsistent data points.

## Data Storage:

After the data is collected and cleaned, it is stored for later analysis. The goal is to ensure that the data is organized and easily accessible for future processing and evaluation.

## Data Analysis
In the analysis phase, meaningful insights are extracted from the financial data:

- Financial Metrics Calculation: Compute ratios like Earnings Per Share (EPS), Price-to-Earnings (P/E), and Return on Equity (ROE) to evaluate profitability and efficiency.
- Trend and Comparative Analysis: Analyze data trends over time and compare performance across companies or sectors. Use statistical techniques like regression or time series analysis for deeper insights.
- Identifying Anomalies: Flag unusual patterns in revenue, expenses, or cash flow for further investigation.

# Stage 2: Website Development
The second stage focuses on creating an interactive web application where users can explore and visualize the financial data. This stage is divided into backend and frontend development:

## Backend:
The backend is built using FastAPI (Python) to serve as an API that fetches the data collected in the first stage.
Several API endpoints are provided, including those for retrieving financial statements and filtering data based on criteria such as company name, year, or financial metric.
## Frontend:
The frontend is developed using React (JavaScript) to create an intuitive and interactive user interface (UI).
The UI displays the financial data in tables and graphs, allowing users to interact with and analyze the data.
Chart.js and Plotly are used to render financial data visually, allowing users to compare different companies, financial years, and metrics.
The goal is to allow users to play with the graphs — manipulating and exploring various financial aspects in an interactive and engaging way.
# Features
## Data Collection:

- Fetches data for all companies from the SEC API.
- Cleans, parses, and stores financial data for analysis.

## Interactive Data Visualization:

- Graphical representation of financial statements using Plotly and Chart.js.
- Allows users to filter and compare financial data across multiple years and companies.

## User-Friendly Interface:

- Developed with React for a smooth, dynamic experience.
- Easy navigation through financial statements and graphical views.

# Technologies Used
- Backend: FastAPI (Python), Pandas
- Frontend: React (JavaScript), Chart.js, Plotly
