# Financial Data Tool - Setup Guide

A modern web application for visualizing and analyzing financial statements with interactive charts.

## Features

- **Ticker Search**: Search and select from available stock tickers
- **Financial Statements**: View Income Statement, Balance Sheet, and Cash Flow statements
- **Dynamic Tables**: Responsive tables with formatted financial data
- **Interactive Charts**: Create multiple charts with different visualization types
- **Flexible Layout**: Adjust the layout between tables and charts dynamically
- **Missing Data Handling**: Gracefully handles missing statement types

## Architecture

### Backend (FastAPI)
- RESTful API for financial data retrieval
- Supports multiple statement types (income_statement, balance_sheet, cash_flow)
- Handles missing files gracefully
- Returns structured JSON data

### Frontend (React)
- Modern React 18 with hooks
- Recharts for data visualization
- Responsive design with dynamic resizing
- Component-based architecture

## Installation & Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The app will open at `http://localhost:3000`

## API Endpoints

### Get Available Tickers
```
GET /api/tickers
```
Returns a list of all available tickers.

### Get All Financial Statements for a Ticker
```
GET /api/financials/{ticker}
```
Returns all available statements (income_statement, balance_sheet, cash_flow) for a ticker.

**Example Response:**
```json
{
  "ticker": "AAPL",
  "statements": {
    "income_statement": {
      "available": true,
      "columns": ["2023-09-30", "2022-09-24", ...],
      "row_names": ["Total revenue", "COGS", ...],
      "data": [[383285000000.0, 394328000000.0, ...], ...]
    },
    "balance_sheet": {
      "available": true,
      ...
    },
    "cash_flow": {
      "available": false,
      ...
    }
  }
}
```

### Get Specific Statement Type
```
GET /api/financials/{ticker}/{statement_type}
```
Returns a specific financial statement.

## Usage Guide

### Viewing Financial Statements

1. **Search for a Ticker**: Use the search bar to find a ticker (e.g., AAPL, AMZN)
2. **Browse Statements**: Click on tabs to switch between Income Statement, Balance Sheet, and Cash Flow
3. **View Data**: Scroll through the formatted table to see financial metrics over time

### Creating Charts

1. **Open Chart Builder**: Click the "📈 Create Chart" button
2. **Select Metrics**: Check the rows you want to visualize from the table
3. **Choose Chart Type**: Select Line, Bar, or Area chart
4. **Add Chart**: Click "Add Chart" to create the visualization
5. **Multiple Charts**: Repeat to add more charts with different metrics

### Adjusting Layout

- Use the **Table Width slider** at the bottom to adjust space between table and charts
- Charts automatically resize based on available space
- Remove charts by clicking the ✕ button on each chart card

## Data Format

Financial data CSV files should be located in `backend/api/financials/` with the following naming convention:
- `{TICKER}_income_statement.csv`
- `{TICKER}_balance_sheet.csv`
- `{TICKER}_cash_flow.csv`
- `{TICKER}_{statement_type}_custom.csv` (alternative format)

**CSV Structure:**
- First column: Row names (metric names)
- Remaining columns: Date periods
- Data values: Numeric financial data

**Example:**
```csv
,2023-09-30,2022-09-24,2021-09-25
Total revenue,383285000000.0,394328000000.0,365817000000.0
COGS,-214137000000.0,-223546000000.0,-212981000000.0
```

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Pandas**: Data manipulation and CSV processing
- **Uvicorn**: ASGI server

### Frontend
- **React 18**: UI framework
- **Axios**: HTTP client
- **Recharts**: Chart library
- **CSS3**: Modern styling with gradients and animations

## Troubleshooting

### Backend Issues

**Problem**: Import errors
```bash
# Solution: Reinstall dependencies
pip install --upgrade -r requirements.txt
```

**Problem**: CORS errors
- Ensure CORS middleware is configured correctly in `backend/app/main.py`
- Check that frontend URL is in `allow_origins`

### Frontend Issues

**Problem**: Module not found errors
```bash
# Solution: Reinstall node modules
rm -rf node_modules package-lock.json
npm install
```

**Problem**: Charts not displaying
- Verify Recharts is installed: `npm list recharts`
- Check browser console for errors

### Data Issues

**Problem**: Ticker not found
- Verify CSV files exist in `backend/api/financials/`
- Check file naming convention matches expected format
- Ensure at least one statement type exists for the ticker

## Development

### Adding New Features

1. **Backend**: Add endpoints in `backend/app/data.py`
2. **Frontend**: Create components in `frontend/src/components/`
3. **Styling**: Update `frontend/src/App.css`

### Code Structure

```
financial_data_tool/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app & CORS config
│   │   └── data.py          # API endpoints & data logic
│   ├── api/
│   │   └── financials/      # CSV data files
│   └── requirements.txt     # Python dependencies
└── frontend/
    ├── src/
    │   ├── App.js           # Main application component
    │   ├── App.css          # Global styles
    │   └── components/
    │       ├── TickerSearch.js    # Search functionality
    │       ├── FinancialTable.js  # Table display
    │       └── ChartManager.js    # Chart rendering
    └── package.json         # Node dependencies
```

## Performance Tips

- Large datasets may take time to load
- Consider pagination for tickers list with 1000+ entries
- Charts with many metrics may slow down rendering
- Use Chrome DevTools to monitor performance

## Future Enhancements

- Export data to CSV/Excel
- Save chart configurations
- Compare multiple tickers
- Custom date range selection
- Advanced filtering options
- Dark mode support

## License

See project root for license information.

## Support

For issues or questions, please check the project repository or contact the development team.
