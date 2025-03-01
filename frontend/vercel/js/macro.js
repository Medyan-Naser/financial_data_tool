document.addEventListener("DOMContentLoaded", function () {

    // fetch the data for the first time when the user load
    setTimeout(() => {
        fetchAllData();
    }, 50);


    const tabContainer = document.getElementById("macro-tab"); // Assuming this is your tab wrapper

    tabContainer.addEventListener("click", function (event) {
        setTimeout(() => {
            fetchAllData();
        }, 50);
        // }
    });


    async function fetchAllData() {
        try {
            const response = await fetch("http://localhost:3000/"); // Single endpoint for all data
            if (!response.ok) {
                throw new Error("Failed to fetch data");
            }
            const data = await response.json();
            console.log(data)
            displayCurrencyData(data.currenciesTable);
            displayMetalsData(data.metalsTable);
            displayEnergyData(data.energyTable);
        } catch (error) {
            console.error("Error fetching data:", error);
            const currencyGraphContainer = document.getElementById("currencyGraph");
            const metalsGraphContainer = document.getElementById("metalsGraph");
            const energyGraphContainer = document.getElementById("energyGraph");

            if (currencyGraphContainer) {
                currencyGraphContainer.innerHTML = "<p>Error loading currency data.</p>";
            }
            if (metalsGraphContainer) {
                metalsGraphContainer.innerHTML = "<p>Error loading metals data.</p>";
            }
            if (energyGraphContainer) {
                energyGraphContainer.innerHTML = "<p>Error loading energy data.</p>";
            }
        }
    }

    function displayCurrencyData(currenciesTable) {
        const currencyGraphContainer = document.getElementById("currencyTable");
        if (!currencyGraphContainer || !currenciesTable || currenciesTable.length === 0) {
            if (currencyGraphContainer) {
                currencyGraphContainer.innerHTML = "<p>No currency data available.</p>";
            }
            return;
        }
        let tableHtml = "<table border='1'><tr><th>Currency</th><th>Price</th><th>Day Change</th><th>Weekly Change</th><th>Monthly Change</th><th>Year-over-Year Change</th></tr>";
        currenciesTable.forEach(currency => {
            tableHtml += `<tr>
                <td>${currency.Major}</td>
                <td>${currency.Price}</td>
                <td>${currency.Day}</td>
                <td>${currency.Weekly}</td>
                <td>${currency.Monthly}</td>
                <td>${currency.YoY}</td>
            </tr>`;
        });
        tableHtml += "</table>";

        currencyGraphContainer.innerHTML = tableHtml;
    }

    function displayMetalsData(metalsTable) {
        const metalsGraphContainer = document.getElementById("MetalsTable");
        if (!metalsGraphContainer || !metalsTable || metalsTable.length === 0) {
            if (metalsGraphContainer) {
                metalsGraphContainer.innerHTML = "<p>No metals data available.</p>";
            }
            return;
        }
        let tableHtml = "<table border='1'><tr><th>Metal</th><th>Price</th><th>Day Change</th><th>Weekly Change</th><th>Monthly Change</th><th>Year-over-Year Change</th></tr>";
        metalsTable.forEach(metal => {
            tableHtml += `<tr>
                <td>${metal.Metals}</td>
                <td>${metal.Price}</td>
                <td>${metal.Day}</td>
                <td>${metal.Weekly}</td>
                <td>${metal.Monthly}</td>
                <td>${metal.YoY}</td>
            </tr>`;
        });
        tableHtml += "</table>";

        metalsGraphContainer.innerHTML = tableHtml;
    }

    function displayEnergyData(energyTable) {
        const energyGraphContainer = document.getElementById("energyTable");
        if (!energyGraphContainer || !energyTable || energyTable.length === 0) {
            if (energyGraphContainer) {
                energyGraphContainer.innerHTML = "<p>No energy data available.</p>";
            }
            return;
        }
        let tableHtml = "<table border='1'><tr><th>Energy Source</th><th>Price</th><th>Day Change</th><th>Weekly Change</th><th>Monthly Change</th><th>Year-over-Year Change</th></tr>";
        energyTable.forEach(energy => {
            tableHtml += `<tr>
                <td>${energy.Energy}</td>
                <td>${energy.Price}</td>
                <td>${energy.Day}</td>
                <td>${energy.Weekly}</td>
                <td>${energy.Monthly}</td>
                <td>${energy.YoY}</td>
            </tr>`;
        });
        tableHtml += "</table>";

        energyGraphContainer.innerHTML = tableHtml;
    }
});
