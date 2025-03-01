function storeFinancialData(ticker, statementType, data) {
    let storedData = sessionStorage.getItem("financialData");
    storedData = storedData ? JSON.parse(storedData) : {};

    // Ensure structure: { ticker: { statementType: data } }
    if (!storedData[ticker]) {
        storedData[ticker] = {};
    }

    storedData[ticker][statementType] = data;

    sessionStorage.setItem("financialData", JSON.stringify(storedData));
    sessionStorage.setItem("currentTicker", ticker)
}

function createTableSelection() {
    const tableContainer = document.createElement("div");
    tableContainer.className = "table-container resize-handle resizable";

    tableContainer.innerHTML = `
        <div id="result" class="table-result">
        </div>
    `;
    document.getElementById("tableGraphContainer").appendChild(tableContainer);
}


async function fetchTableData(ticker, statementType = "income-statement") {
    const apiUrl = `http://localhost:3000/${statementType}/${ticker}`;
    createTableSelection()
    const result = document.getElementById("result");

    try {
        const response = await fetch(apiUrl);
        const data = await response.json();

        if (response.status === 404) {
            result.innerHTML = `<p>${data.message}</p>`;
            return;
        }

        // Transform the data into financial statement format
        const years = data.map(item => new Date(item.year).getFullYear());
        const metrics = {
            "Total Revenue": data.map(item => item.total_revenue),
            "Net Income": data.map(item => item.net_income),
            "COGS": data.map(item => item.cogs),
            "Gross Profit": data.map(item => item.gross_profit),
            "SGA": data.map(item => item.sga),
            "R&D": data.map(item => item.r_d)
        };

        // Store data in sessionStorage
        storeFinancialData(ticker, statementType, { years, metrics });
        console.log(sessionStorage.getItem("financialData"));
        console.log("test2")

        // Generate Table
        let tableHTML = `<table><thead><tr><th>Metric</th>`;

        // Add Year Headers
        years.forEach(year => {
            tableHTML += `<th>${year}</th>`;
        });
        tableHTML += `</tr></thead><tbody>`;

        // Add Data Rows
        for (let metric in metrics) {
            tableHTML += `<tr><td>${metric}</td>`;
            metrics[metric].forEach(value => {
                tableHTML += `<td>${value}</td>`;
            });
            tableHTML += `</tr>`;
        }

        tableHTML += "</tbody></table>";
        result.innerHTML = tableHTML;

    } catch (error) {
        console.error("Error fetching data:", error);
        result.innerHTML = `<p>Error fetching data: ${error.message}</p>`;
    }
}
