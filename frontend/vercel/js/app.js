document.addEventListener("DOMContentLoaded", function () {

    // Function to initialize event listeners when new content is added
    function initializeContent() {
        const toggleTableBtn = document.getElementById("toggleTable");
        const fetchDataBtn = document.getElementById("fetchData");
        const tickerInput = document.getElementById("ticker");

        // if (!toggleTableBtn || !fetchDataBtn || !addGraphBtn || !tickerInput || !currencyGraphContainer) {
        //     return; // Elements not yet available
        // }

        // Toggle table visibility
        toggleTableBtn.addEventListener("click", function () {
            const tableContainer = document.querySelector(".resizable.tableContainer");
            if (tableContainer) {
                tableContainer.classList.toggle("hidden");
            }
        });

        // Fetch income statement data
        fetchDataBtn.addEventListener("click", function (event) {
            const ticker = tickerInput.value.trim();
            event.preventDefault();
            if (!ticker) {
                alert("Please enter a company ticker.");
                return;
            }
            fetchTableData(ticker);
        });


    }

    const mainContainer = document.getElementById("main");

    // MutationObserver to detect when new content is loaded into #main
    const observer = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
            if (mutation.addedNodes.length > 0) {
                console.log("New content loaded into #main, initializing scripts...");
                initializeContent();
            }
        });
    });

    // Start observing #main for content changes
    observer.observe(mainContainer, { childList: true, subtree: true });
});
