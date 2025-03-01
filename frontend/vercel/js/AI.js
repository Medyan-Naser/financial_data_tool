document.addEventListener("DOMContentLoaded", function () {
    const mainContainer = document.getElementById("main");
    
    let isUpdating = false; // Flag to prevent infinite loop

    function initializeAIContent() {
        if (!isUpdating) {
            fetchAIData();
        }
    }

    const observer = new MutationObserver((mutations) => {
        if (isUpdating) return; // Ignore changes made by the script itself

        mutations.forEach(mutation => {
            if (mutation.addedNodes.length > 0) {
                console.log("New content loaded into #main, initializing scripts...");
                initializeAIContent();
            }
        });
    });

    if (mainContainer) {
        observer.observe(mainContainer, { childList: true, subtree: true });
    } else {
        console.error("#main container not found.");
    }

    async function fetchAIData() {
        let currentTicker = sessionStorage.getItem("currentTicker");
        try {
            const response = await fetch(`http://localhost:3000/AI/${currentTicker}`); // Single endpoint for all data
            if (!response.ok) {
                throw new Error("Failed to fetch data");
            }
            const data = await response.json();
            isUpdating = true; // Prevent observer from reacting to changes
            console.log(data)
            displayAIData(data.AI_Data);
            setTimeout(() => { isUpdating = false; }, 500); // Reset after a short delay
        } catch (error) {
            console.error("Error fetching data:", error);
            const aiContainer = document.getElementById("aiContainer");

            if (aiContainer) {
                aiContainer.innerHTML = "<p>Error loading currency data.</p>";
            }
        }

    }


    function displayAIData(AI_Data) {
        const aiContainer = document.getElementById("aiContainer");
        if (!aiContainer || !AI_Data || AI_Data.length === 0) {
            if (aiContainer) {
                aiContainer.innerHTML = "<p>No currency data available.</p>";
            }
            return;
        }
        let tableHtml = "<table border='1'><tr><th>Currency</th><th>Price</th><th>Day Change</th><th>Weekly Change</th><th>Monthly Change</th><th>Year-over-Year Change</th></tr>";
        AI_Data.forEach(currency => {
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

        aiContainer.innerHTML = tableHtml;
    }

});
