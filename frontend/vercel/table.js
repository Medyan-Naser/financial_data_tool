async function fetchTableData(ticker) {
    const apiUrl = `http://localhost:3000/income-statement/${ticker}`;
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
