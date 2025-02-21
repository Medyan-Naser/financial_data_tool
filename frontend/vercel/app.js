
document.addEventListener("DOMContentLoaded", function () {
    const toggleTableBtn = document.getElementById("toggleTable");
    const fetchDataBtn = document.getElementById("fetchData");
    const addGraphBtn = document.getElementById("addGraph");
    const tickerInput = document.getElementById("ticker");

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
});
