document.addEventListener("DOMContentLoaded", async function () {
    const mainDiv = document.getElementById("main");
    const links = document.querySelectorAll(".links a");
    const body = document.body;

    async function loadPage(page) {
        try {
            const response = await fetch(page);
            const html = await response.text();
            mainDiv.innerHTML = html;
        } catch (error) {
            console.error("Error loading page:", error);
        }
    }

    function closeNavPanel() {
        body.classList.remove("is-navPanel-visible"); // Remove the class to close the menu
    }

    // Load default home page and wait for it to finish
    await loadPage("macro.html");

    // Add event listeners for navigation
    links.forEach(link => {
        link.addEventListener("click", async function (event) {
            event.preventDefault();
            // Remove active class from all list items
            document.querySelectorAll(".links li").forEach(li => li.classList.remove("active"));
            
            // Add active class to the clicked item's parent <li>
            this.parentElement.classList.add("active");

            // Load the requested page and wait for it to finish
            const page = this.getAttribute("data-page");
            await loadPage(page);

            // Close the navigation panel
            closeNavPanel();
        });
    });

    // Notify other scripts that page loading is complete
    window.pageLoaded = true;
    document.dispatchEvent(new Event("pageLoaded"));
});
