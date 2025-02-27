document.addEventListener("DOMContentLoaded", function () {
    const root = document.getElementById("root");

    root.innerHTML = `
        <div class="container">
            <h2>Income Statement Viewer</h2>
            <input type="text" id="ticker" placeholder="Enter Company Ticker">
            <button id="fetchData">Get Income Statement</button>
            <div id="result"></div>
        </div>
    `;

    document.getElementById("fetchData").addEventListener("click", async function () {
        const ticker = document.getElementById("ticker").value.trim();
        if (!ticker) {
            alert("Please enter a company ticker.");
            return;
        }

        const apiUrl = `https://financial-data-tool.onrender.com/income-statement/101`;
        
        try {
            const response = await fetch(apiUrl);
            const data = await response.json();
            
            if (response.status === 404) {
                document.getElementById("result").innerHTML = `<p>${data.message}</p>`;
                return;
            }

            let tableHTML = `
                <table>
                    <tr>
                        <th>Year</th>
                        <th>Revenue</th>
                        <th>Net Income</th>
                    </tr>
            `;

            data.forEach(item => {
                tableHTML += `
                    <tr>
                        <td>${item.year}</td>
                        <td>${item.revenue}</td>
                        <td>${item.net_income}</td>
                    </tr>
                `;
            });

            tableHTML += "</table>";
            document.getElementById("result").innerHTML = tableHTML;
        } catch (error) {
            console.error("Error fetching data:", error);
            document.getElementById("result").innerHTML = `<p>Error fetching data.</p>`;
        }
    });
});
