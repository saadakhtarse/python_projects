document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const resultContainer = document.querySelector(".result-container");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const postcode = document.querySelector("#postcode").value;
        const numSchools = document.querySelector("#numSchools").value;

        if (!postcode || !numSchools) {
            alert("Please enter both Postcode and number of schools.");
            return;
        }

        resultContainer.style.display = "block";
        resultContainer.innerHTML = "<p>Loading schools...</p>";

        try {
            const response = await fetch("/find-schools", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ postcode: postcode, num_schools: numSchools })
            });

            const data = await response.json();

            if (data.error) {
                resultContainer.innerHTML = `<p style="color:red;">${data.error}</p>`;
                return;
            }

            resultContainer.innerHTML = "<h2>Nearby Schools:</h2>";
            data.schools.forEach(school => {
                const div = document.createElement("div");
                div.classList.add("school-item");
                div.innerHTML = `
                    <h3>${school.EstablishmentName}</h3>
                    <p><strong>Address:</strong> ${school.Address}</p>
                    <p><strong>Postcode:</strong> ${school.Postcode}</p>
                    <p><strong>Distance:</strong> ${school.distance_km} km</p>
                `;
                resultContainer.appendChild(div);
            });

        } catch (error) {
            console.error("Error fetching data:", error);
            resultContainer.innerHTML = "<p style='color:red;'>An error occurred. Please try again.</p>";
        }
    });
});
