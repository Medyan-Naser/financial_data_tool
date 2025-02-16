document.addEventListener("DOMContentLoaded", function () {
    const graphArea = document.getElementById("graphArea");

    // Expose addGraph globally
    window.addGraph = function () {
        const table = document.querySelector("#result table");
        if (!table) {
            alert("Please fetch data first!");
            return;
        }

        const { years, metrics } = getTableData(table);
        if (metrics.length === 0) {
            alert("No valid financial data found.");
            return;
        }

        createGraphSelection(years, metrics);
    };

    function getTableData(table) {
        const rows = table.querySelectorAll("tr");
        if (rows.length < 2) return { years: [], metrics: [] };

        // Extract years (column headers)
        const years = Array.from(rows[0].cells).slice(1).map(cell => cell.textContent.trim());

        // Extract metric names and values
        const metrics = [];
        const data = {};

        rows.forEach((row, index) => {
            if (index === 0) return; // Skip header row
            const metricName = row.cells[0].textContent.trim();
            metrics.push(metricName);
            data[metricName] = Array.from(row.cells).slice(1).map(cell => parseFloat(cell.textContent) || 0);
        });

        return { years, metrics, data };
    }

    function createGraphSelection(years, metrics) {
        const graphContainer = document.createElement("div");
        graphContainer.className = "graph-container";
    
        const select = document.createElement("select");
        select.multiple = true;
        select.size = 5; // Show multiple options at once
    
        metrics.forEach(metric => {
            const option = document.createElement("option");
            option.value = metric;
            option.textContent = metric;
            select.appendChild(option);
        });
    
        const plotButton = document.createElement("button");
        plotButton.textContent = "Plot Graph";
        plotButton.onclick = () => plotGraph(years, select, graphContainer);
    
        // Create the Remove Graph button
        const removeButton = document.createElement("button");
        removeButton.textContent = "Remove Graph";
        removeButton.onclick = () => removeGraph(graphContainer);
    
        graphContainer.appendChild(select);
        graphContainer.appendChild(plotButton);
        graphContainer.appendChild(removeButton); // Add the remove button
        const canvas = document.createElement("canvas");
        graphContainer.appendChild(canvas);
    
        graphArea.appendChild(graphContainer);
    }
    

    function plotGraph(years, select, graphContainer) {
        const table = document.querySelector("#result table");
        const { data } = getTableData(table);
    
        const selectedMetrics = Array.from(select.selectedOptions).map(option => option.value);
        if (selectedMetrics.length === 0) {
            alert("Select at least one metric to plot.");
            return;
        }
    
        const datasets = selectedMetrics.map((metric, index) => ({
            label: metric,
            data: data[metric],
            borderColor: getRandomColor(index),
            fill: false
        }));
    
        const canvas = graphContainer.querySelector("canvas");
        const ctx = canvas.getContext("2d");
    
        // Check if a chart already exists on the canvas, and destroy it if it does
        if (canvas.chart) {
            canvas.chart.destroy();
        }
    
        // Create a new chart
        const newChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: years.sort((a, b) => a - b), // Sort years numerically
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
    
        // Store the chart on the canvas for later reference
        canvas.chart = newChart;
    
        // Ensure the chart resizes when the container is resized
        window.addEventListener('resize', () => {
            if (canvas.chart) {
                canvas.chart.resize();
            }
        });
    }
    
    
    function removeGraph(graphContainer) {
        if (graphContainer) {
            // If a chart is present, destroy it before removing
            const canvas = graphContainer.querySelector("canvas");
            if (canvas && canvas.chart) {
                canvas.chart.destroy();
            }
    
            // Remove the graph container from the DOM
            graphContainer.remove();
        }
    }

    function getRandomColor(index) {
        const colors = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"];
        return colors[index % colors.length];
    }
});
