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
        console.log("display ai")
        console.log(AI_Data)
        const aiContainer = document.getElementById("aiContainer");
        if (!aiContainer || !AI_Data || AI_Data.length === 0) {
            if (aiContainer) {
                aiContainer.innerHTML = "<p>No currency data available.</p>";
            }
            return;
        }
        // let tableHtml = `<div><Plot data=${AI_Data.data} layout=${AI_Data.layout} /></div>`;
        // aiContainer.innerHTML = tableHtml;

        // Create a new div element
        let div = document.createElement("div");

        // You can create a new Plotly plot, assuming you're using Plotly.js
        if (window.Plotly) {
            // Create the chart using Plotly
            Plotly.newPlot(div, AI_Data.data, AI_Data.layout);
        }

        // Append the newly created div to the aiContainer
        aiContainer.innerHTML = '';  // Clear any existing content
        aiContainer.appendChild(div);
    }

});
