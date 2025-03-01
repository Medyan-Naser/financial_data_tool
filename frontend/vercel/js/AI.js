document.addEventListener("DOMContentLoaded", function () {

    const tabContainer = document.getElementById("ai-tab"); // Assuming this is your tab wrapper

    tabContainer.addEventListener("click", function (event) {
        setTimeout(() => {
            fetchAIData();
        }, 50);
        // }
    });

    async function fetchAIData() {
        console.log("get ai data")
        let currentTicker = sessionStorage.getItem("currentTicker");
        try {
            console.log(currentTicker)
            const response = await fetch(`http://localhost:3000/AI/${currentTicker}`); // Single endpoint for all data
            if (!response.ok) {
                throw new Error("Failed to fetch data");
            }
            const data = await response.json();
            console.log(data)
            displayAIData(data.AI_Data);
        } catch (error) {
            console.error("Error fetching data:", error);
            const aiContainer = document.getElementById("aiContainer");

            if (aiContainer) {
                aiContainer.innerHTML = "<p>Error loading currency data.</p>";
            }
        }

    }


    function displayAIData(AI_Data) {
        const aiContainer = document.getElementById("aiContainer");
        if (!aiContainer || !AI_Data || AI_Data.length === 0) {
            if (aiContainer) {
                aiContainer.innerHTML = "<p>No currency data available.</p>";
            }
            return;
        }
        let tableHtml = "<table border='1'><tr><th>Currency</th><th>Price</th><th>Day Change</th><th>Weekly Change</th><th>Monthly Change</th><th>Year-over-Year Change</th></tr>";
        AI_Data.forEach(currency => {
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

        aiContainer.innerHTML = tableHtml;
    }

});
