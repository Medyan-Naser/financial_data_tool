document.addEventListener("DOMContentLoaded", function () {
    const mainContainer = document.getElementById("main");
    
    let isUpdating = false; // Flag to prevent infinite loop

    function initializeContent() {
        if (!isUpdating) {
            fetchAllData();
        }
    }

    const observer = new MutationObserver((mutations) => {
        if (isUpdating) return; // Ignore changes made by the script itself

        mutations.forEach(mutation => {
            if (mutation.addedNodes.length > 0) {
                console.log("New content loaded into #main, initializing scripts...");
                initializeContent();
            }
        });
    });

    if (mainContainer) {
        observer.observe(mainContainer, { childList: true, subtree: true });
    } else {
        console.error("#main container not found.");
    }

    async function fetchAllData() {
        try {
            const response = await fetch("http://localhost:3000/"); // Single endpoint for all data
            if (!response.ok) {
                throw new Error("Failed to fetch data");
            }
            const data = await response.json();
            isUpdating = true; // Prevent observer from reacting to changes
            console.log(data)
            displayCurrencyData(data.currenciesTable);
            displayMetalsData(data.metalsTable);
            displayEnergyData(data.energyTable);
            setTimeout(() => { isUpdating = false; }, 500); // Reset after a short delay
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
