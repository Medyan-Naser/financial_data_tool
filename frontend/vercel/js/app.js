document.addEventListener("DOMContentLoaded", function () {
    const tabContainer = document.getElementById("tabs-ul"); // Assuming this is your tab wrapper

    tabContainer.addEventListener("click", function (event) {
        setTimeout(() => {
            initializeContent();
        }, 50);
        // }
    });

    const fetchDataBtn = document.getElementById("fetchData");
    const tickerInput = document.getElementById("ticker");
    // Fetch income statement data
    fetchDataBtn.addEventListener("click", function (event) {
        console.log("search button")
        const ticker = tickerInput.value.trim();
        event.preventDefault();
        if (!ticker) {
            alert("Please enter a company ticker.");
            return;
        }
        fetchTableData(ticker);
    });



    // Function to initialize event listeners when new content is added
    function initializeContent() {
        const toggleTableBtn = document.getElementById("toggleTable"); 
        const tableContainer = document.getElementById("tableContainer");

        if (!toggleTableBtn) { 
            return; // Elements not yet available
        }

        // Toggle table visibility
        toggleTableBtn.addEventListener("click", function () {
            if (tableContainer) {
                tableContainer.classList.toggle("hidden");
            }
        });

        
    }
});
