# Quick Start Guide

## Running the Application

### 1. Start the Backend (Terminal 1)

```bash
cd backend
python -m venv venv  # Optional: create virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### 2. Start the Frontend (Terminal 2)

```bash
cd frontend
npm install  # Only needed first time or after package.json changes
npm start
```

Frontend will open automatically at: http://localhost:3000

## First Time Use

1. **Search for a ticker** - Type a ticker symbol (e.g., AAPL) in the search box
2. **View financial data** - The financial statements will load automatically
3. **Switch between statements** - Click tabs to see Income Statement, Balance Sheet, or Cash Flow
4. **Create a chart**:
   - Click "📈 Create Chart"
   - Select rows from the table (checkbox them)
   - Choose a chart type (Line, Bar, or Area)
   - Click "Add Chart"
5. **Adjust layout** - Use the slider to resize table vs charts

## Available Tickers

The application will show all tickers that have CSV files in:
```
backend/api/financials/
```

File naming pattern:
- `TICKER_income_statement.csv`
- `TICKER_balance_sheet.csv`
- `TICKER_cash_flow.csv`

## Testing the API

Visit http://localhost:8000/docs to see the interactive API documentation (Swagger UI).

Try these endpoints:
- `GET /api/tickers` - List all available tickers
- `GET /api/financials/AAPL` - Get all Apple financial statements
- `GET /api/financials/AAPL/income_statement` - Get just the income statement

## Troubleshooting

**Backend won't start:**
- Check Python version (3.8+)
- Ensure port 8000 is not in use
- Verify CSV files exist in `backend/api/financials/`

**Frontend won't start:**
- Check Node version (14+)
- Delete `node_modules` and run `npm install` again
- Check port 3000 is not in use

**No data showing:**
- Verify backend is running on port 8000
- Check browser console for errors (F12)
- Ensure CSV files are properly formatted

**CORS errors:**
- Backend CORS is configured for localhost:3000
- If using different port, update `backend/app/main.py`

## Key Features to Try

1. **Multiple Charts** - Create several charts with different metrics
2. **Different Chart Types** - Compare Line vs Bar vs Area visualizations
3. **Mixed Metrics** - Select multiple rows from different sections
4. **Layout Adjustment** - Drag the slider to change table/chart ratio
5. **Tab Switching** - Charts persist when switching between statements

## Next Steps

- Read SETUP_README.md for detailed documentation
- Explore the API at http://localhost:8000/docs
- Add your own CSV files to analyze more companies

Enjoy analyzing financial data! 📊
