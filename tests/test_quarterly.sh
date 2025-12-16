#!/bin/bash

echo "Testing Quarterly Data Collection..."
echo "======================================"

# Clean up any previous test data
rm -rf data-collection/scripts/output/TEST

# Test quarterly data collection
cd data-collection/scripts
python3 main.py --ticker AAPL --years 1 --quarterly --output output

# Check if files were created with correct naming
echo ""
echo "Checking file naming..."
if ls output/AAPL/*_quarterly.csv 1> /dev/null 2>&1; then
    echo "✅ Quarterly files created correctly!"
    ls -la output/AAPL/*_quarterly.csv
else
    echo "❌ ERROR: Quarterly files not found!"
    ls -la output/AAPL/
    exit 1
fi

echo ""
echo "Test passed! ✅"
