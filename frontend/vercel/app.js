document.addEventListener("DOMContentLoaded", function () {
    const toggleTableBtn = document.getElementById("toggleTable");
    const fetchDataBtn = document.getElementById("fetchData");
    const addGraphBtn = document.getElementById("addGraph");
    const tickerInput = document.getElementById("ticker");

    // Toggle table visibility
    toggleTableBtn.addEventListener("click", function () {
        document.getElementById("table-wrapper").classList.toggle("hidden");
    });

    // Fetch income statement data
    fetchDataBtn.addEventListener("click", function () {
        const ticker = tickerInput.value.trim();
        if (!ticker) {
            alert("Please enter a company ticker.");
            return;
        }
        fetchTableData(ticker); // Call function from table.js
    });

    // Dynamically add a graph
    addGraphBtn.addEventListener("click", function () {
        addGraph(); // Call function from graph.js
    });
});


