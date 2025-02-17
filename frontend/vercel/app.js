document.addEventListener("DOMContentLoaded", function () {
    const toggleTableBtn = document.getElementById("toggleTable");
    const fetchDataBtn = document.getElementById("fetchData");
    const addGraphBtn = document.getElementById("addGraph");
    const tickerInput = document.getElementById("ticker");

    // Toggle table visibility
    toggleTableBtn.addEventListener("click", function () {
        document.getElementById("tableContainer").classList.toggle("hidden");
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

    // Get references to the divider and the sections
    const divider = document.getElementById("divider");
    const tableContainer = document.getElementById("tableContainer");
    const graphArea = document.getElementById("graphArea");

    // Initialize variables for tracking the mouse position
    let isDragging = false;
    let startX = 0;
    let startWidth = 0;

    // Mouse down event on the divider to start dragging
    divider.addEventListener("mousedown", (e) => {
        isDragging = true;
        startX = e.clientX;  // Mouse position when dragging starts
        startWidth = tableContainer.offsetWidth;  // Current width of the table container
        document.body.style.cursor = "ew-resize";  // Change cursor to resizing
    });

    // Mouse move event to resize the table and graph
    document.addEventListener("mousemove", (e) => {
        if (!isDragging) return;

        const diff = e.clientX - startX;  // Calculate how far the mouse has moved
        const newTableWidth = startWidth + diff;  // Calculate new width for the table

        // Set new widths for the table and graph containers
        tableContainer.style.width = `${newTableWidth}px`;
        graphArea.style.width = `calc(100% - ${newTableWidth + 10}px)`;  // 10px for the divider width
    });

    // Mouse up event to stop dragging
    document.addEventListener("mouseup", () => {
        isDragging = false;
        document.body.style.cursor = "default";  // Reset cursor
    });
});
