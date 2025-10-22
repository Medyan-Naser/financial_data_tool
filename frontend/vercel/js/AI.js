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
            displayAIData(data);
        } catch (error) {
            console.error("Error fetching data:", error);
            const aiContainer = document.getElementById("aiContainer");

            if (aiContainer) {
                aiContainer.innerHTML = "<p>Error loading currency data.</p>";
            }
        }

    }

    function decodeBData(bdata) {
        let byteArray = new Float64Array(atob(bdata).split("").map(c => c.charCodeAt(0)));
        return Array.from(byteArray); // Convert Typed Array to Normal JS Array
    }

    function convertYaxis(data){
        // Fix y-values before passing to Plotly
        data.forEach(trace => {
            if (trace.y && trace.y.bdata) {
                trace.y = decodeBData(trace.y.bdata);  // Convert bdata to normal numbers
            }
        });
        return data
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
        let company_plot_div = document.createElement("div");
        // You can create a new Plotly plot, assuming you're using Plotly.js
        
        if (window.Plotly) {
            // Create the chart using Plotly
            console.log(AI_Data.company_plot)
            AI_Data.company_plot.data = convertYaxis(AI_Data.company_plot.data)
            console.log(AI_Data.company_plot)
            Plotly.newPlot(company_plot_div, AI_Data.company_plot.data, AI_Data.company_plot.layout);
        }
        // Append the newly created div to the aiContainer
        aiContainer.appendChild(company_plot_div);

        // Create a new div element
        let spy_index_div = document.createElement("div");
        if (window.Plotly) {Plotly.newPlot(spy_index_div, AI_Data.spy_index.data, AI_Data.spy_index.layout);}
        aiContainer.appendChild(spy_index_div);

        // Create a new div element
        let plot_SPY_div = document.createElement("div");
        if (window.Plotly) {Plotly.newPlot(plot_SPY_div, AI_Data.plot_SPY.data, AI_Data.plot_SPY.layout);}
        aiContainer.appendChild(plot_SPY_div);

        // Create a new div element
        let rolling_volatility_plot_SPY_div = document.createElement("div");
        if (window.Plotly) {Plotly.newPlot(rolling_volatility_plot_SPY_div, AI_Data.rolling_volatility_plot_SPY.data, AI_Data.rolling_volatility_plot_SPY.layout);}
        aiContainer.appendChild(rolling_volatility_plot_SPY_div);

        // Create a new div element
        let forecast_plot_SPY_div = document.createElement("div");
        if (window.Plotly) {Plotly.newPlot(forecast_plot_SPY_div, AI_Data.forecast_plot_SPY.data, AI_Data.forecast_plot_SPY.layout);}
        aiContainer.appendChild(forecast_plot_SPY_div);
    }

});
