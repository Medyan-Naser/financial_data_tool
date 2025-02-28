document.addEventListener("DOMContentLoaded", function () {
    function initializeGraphContent() {
        const graphArea = document.getElementById("tableGraphContainer");
        const addGraphBtn = document.getElementById("addGraph");

        console.log("reloaded");
        
        if (addGraphBtn) {
            addGraphBtn.replaceWith(addGraphBtn.cloneNode(true)); // Removes all existing event listeners
            const newAddGraphBtn = document.getElementById("addGraph");
            newAddGraphBtn.addEventListener("click", function () {
                addGraph();
            });
        }
    }

    function addGraph(){
        console.log("add graph");
        const { years, metrics, data } = getStoredFinancialData();
        if (metrics.length === 0) {
            alert("No stored financial data found. Please fetch data first.");
            return;
        }
        createGraphSelection(years, metrics, data);
    }

    function getStoredFinancialData() {
        let storedData = sessionStorage.getItem("financialData");
        let currentTicker = sessionStorage.getItem("currentTicker");
    
        if (!storedData || !currentTicker) {
            return { years: [], metrics: [], data: {} };
        }
    
        storedData = JSON.parse(storedData);
        
        if (!storedData[currentTicker]) {
            return { years: [], metrics: [], data: {} };
        }
        
        const statementType = Object.keys(storedData[currentTicker])[0];
        if (!statementType) return { years: [], metrics: [], data: {} };
    
        const { years, metrics } = storedData[currentTicker][statementType];
    
        return { years, metrics: Object.keys(metrics), data: metrics };
    }
    
    function createGraphSelection(years, metrics, data) {
        const graphContainer = document.createElement("div");
        graphContainer.className = "graph-container resizable";

        const select = document.createElement("select");
        select.multiple = true;
        select.size = 5;

        metrics.forEach(metric => {
            const option = document.createElement("option");
            option.value = metric;
            option.textContent = metric;
            select.appendChild(option);
        });

        const plotButton = document.createElement("button");
        plotButton.textContent = "Plot Graph";
        plotButton.onclick = () => plotGraph(years, data, select, graphContainer);

        const removeButton = document.createElement("button");
        removeButton.textContent = "Remove Graph";
        removeButton.onclick = () => removeGraph(graphContainer);

        graphContainer.appendChild(select);
        graphContainer.appendChild(plotButton);
        graphContainer.appendChild(removeButton);

        const canvas = document.createElement("canvas");
        graphContainer.appendChild(canvas);
        document.getElementById("tableGraphContainer").appendChild(graphContainer);
    }

    function plotGraph(years, data, select, graphContainer) {
        const selectedMetrics = Array.from(select.selectedOptions).map(option => option.value);

        if (selectedMetrics.length === 0) {
            alert("Select at least one metric to plot.");
            return;
        }

        const datasets = selectedMetrics.map((metric, index) => ({
            label: metric,
            data: data[metric] || [],
            borderColor: getRandomColor(index),
            fill: false
        }));

        const canvas = graphContainer.querySelector("canvas");
        const ctx = canvas.getContext("2d");

        if (canvas.chart) {
            canvas.chart.destroy();
        }

        canvas.chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: years.sort((a, b) => a - b),
                datasets
            },
            options: {
                responsive: true,
                scales: {
                    x: { title: { display: true, text: "Year" } },
                    y: { title: { display: true, text: "Value" } }
                }
            }
        });
    }

    function removeGraph(graphContainer) {
        if (graphContainer) {
            const canvas = graphContainer.querySelector("canvas");
            if (canvas && canvas.chart) {
                canvas.chart.destroy();
            }
            graphContainer.remove();
        }
    }

    function getRandomColor(index) {
        const colors = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"];
        return colors[index % colors.length];
    }

    const mainContainer = document.getElementById("main");

    const observer = new MutationObserver((mutations) => {
        let contentAdded = false;
        
        mutations.forEach(mutation => {
            if (mutation.addedNodes.length > 0) {
                contentAdded = true;
            }
        });

        if (contentAdded) {
            console.log("New content loaded into #main, initializing scripts...");
            
            observer.disconnect(); // Disconnect observer before modifying the DOM
            initializeGraphContent();
            observer.observe(mainContainer, { childList: true, subtree: true }); // Reconnect observer
        }
    });

    observer.observe(mainContainer, { childList: true, subtree: true });
});