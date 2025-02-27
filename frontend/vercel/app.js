
document.addEventListener("DOMContentLoaded", function () {
    const toggleTableBtn = document.getElementById("toggleTable");
    const fetchDataBtn = document.getElementById("fetchData");
    const addGraphBtn = document.getElementById("addGraph");
    const tickerInput = document.getElementById("ticker");
    const currencyGraphContainer = document.getElementById("currencyGraph");

    let isDragging = false;
    let startX = 0, startY = 0;
    let startWidth = 0, startHeight = 0;
    let resizeDirection = "";
    let activeElement = null;
    const edgeThreshold = 10; // Distance from edge to trigger resize

    // Toggle table visibility
    toggleTableBtn.addEventListener("click", function () {
        const tableContainer = document.querySelector(".resizable.tableContainer");
        if (tableContainer) {
            tableContainer.classList.toggle("hidden");
        }
    });

    // Fetch income statement data
    fetchDataBtn.addEventListener("click", function () {
        const ticker = tickerInput.value.trim();
        if (!ticker) {
            alert("Please enter a company ticker.");
            return;
        }
        fetchTableData(ticker);
    });
    // Dynamically add a graph
    addGraphBtn.addEventListener("click", function () {
        addGraph();
    });

    // Function to fetch and display currency data
    async function fetchCurrencyData() {
        try {
            const response = await fetch("http://localhost:3000/"); // Request data from backend
            if (!response.ok) {
                throw new Error("Failed to fetch currency data");
            }
            const data = await response.json();
            console.log(data)
            displayCurrencyData(data.currenciesTable);
        } catch (error) {
            console.error("Error fetching currency data:", error);
            currencyGraphContainer.innerHTML = "<p>Error loading currency data.</p>";
        }
    }

    // Function to display currency data in the div
    function displayCurrencyData(currenciesTable) {
        if (!currenciesTable || currenciesTable.length === 0) {
            currencyGraphContainer.innerHTML = "<p>No currency data available.</p>";
            return;
        }

        // Create the header and rows for the table
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

        // Insert the table HTML into the container
        currencyGraphContainer.innerHTML = tableHtml;
    }

    // Function to detect resize region
    function detectResizeRegion(element, e) {
        const rect = element.getBoundingClientRect();
        let direction = "";

        if (Math.abs(e.clientX - rect.left) < edgeThreshold) {
            direction = "left";
        } else if (Math.abs(e.clientX - rect.right) < edgeThreshold) {
            direction = "right";
        }
        if (Math.abs(e.clientY - rect.top) < edgeThreshold) {
            direction += "top";
        } else if (Math.abs(e.clientY - rect.bottom) < edgeThreshold) {
            direction += "bottom";
        }

        return direction;
    }

    // Function to start resizing
    function startResize(e, element) {
        resizeDirection = detectResizeRegion(element, e);
        if (!resizeDirection) return;

        isDragging = true;
        activeElement = element;
        startX = e.clientX;
        startY = e.clientY;
        const rect = element.getBoundingClientRect();
        startWidth = rect.width;
        startHeight = rect.height;

        e.preventDefault();
        // document.body.style.cursor = "ew-resize";
        // resizeDirection.includes("left") || resizeDirection.includes("right") ? "ew-resize" : "ns-resize"
    }

    // Function to handle resizing
    function handleResize(e) {
        if (!isDragging || !activeElement) return;

        if (resizeDirection.includes("right")) {
            activeElement.style.width = `${startWidth + (e.clientX - startX)}px`;
        }
        if (resizeDirection.includes("left")) {
            activeElement.style.width = `${startWidth - (e.clientX - startX)}px`;
            // activeElement.style.left = `${activeElement.offsetLeft + (e.clientX - startX)}px`;
        }
        if (resizeDirection.includes("bottom")) {
            activeElement.style.height = `${startHeight + (e.clientY - startY)}px`;
        }
        if (resizeDirection.includes("top")) {
            activeElement.style.height = `${startHeight - (e.clientY - startY)}px`;
            // activeElement.style.top = `${activeElement.offsetTop + (e.clientY - startY)}px`;
        }
    }

    // Function to stop resizing
    function stopResize() {
        isDragging = false;
        activeElement = null;
        document.body.style.cursor = "default";
    }

    // Attach resizing to all resizable elements
    document.addEventListener("mousedown", (e) => {
        document.querySelectorAll(".resizable").forEach(element => {
            if (element.contains(e.target)) {
                startResize(e, element);
            }
        });
    });

    // Global event listeners for resizing
    document.addEventListener("mousemove", handleResize);
    document.addEventListener("mouseup", stopResize);
    // Fetch data on page load
    fetchCurrencyData();
});
