document.addEventListener("DOMContentLoaded", () => {
    const tableBody = document.getElementById("tableData");
    const exportBtn = document.getElementById("exportBtn");
    const clearBtn = document.getElementById("clearBtn");
    const totalCount = document.getElementById("totalCount");

    if (!tableBody) {
        return;
    }

    loadRSVPs();

    if (exportBtn) {
        exportBtn.addEventListener("click", () => {
        window.location.href = `${API_BASE}/export.csv`;
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener("click", clearEntries);
    }

    async function loadRSVPs() {
        tableBody.innerHTML = "";

        try {
            const response = await fetch(`${API_BASE}/rsvps`);

            if (!response.ok) {
                throw new Error("Could not load RSVP data.");
            }

            const list = await response.json();

            if (totalCount) {
                totalCount.textContent = Array.isArray(list) ? list.length : 0;
            }

            if (!Array.isArray(list) || list.length === 0) {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                <td colspan="5" class="border px-4 py-2 text-center italic text-gray-500">
                    No RSVPs yet.
                </td>
                `;
                tableBody.appendChild(tr);
                return;
            }

            list.forEach((entry) => {
                const tr = document.createElement("tr");

                const guests = [];

                if (entry.guest1fname || entry.guest1lname) {
                    guests.push(`${entry.guest1fname || ""} ${entry.guest1lname || ""}`.trim());
                }

                if (entry.guest2fname || entry.guest2lname) {
                    guests.push(`${entry.guest2fname || ""} ${entry.guest2lname || ""}`.trim());
                }

                tr.innerHTML = `
                    <td class="border px-4 py-2">${entry.fname || ""} ${entry.lname || ""}</td>
                    <td class="border px-4 py-2">${entry.email || ""}</td>
                    <td class="border px-4 py-2">${entry.hofstraId || ""}</td>
                    <td class="border px-4 py-2">${guests.length ? guests.join("<br>") : "N/A"}</td>
                    <td class="border px-4 py-2">${entry.submitTime || ""}</td>
                `;

                tableBody.appendChild(tr);
            });
        } 
    catch (err) {
        console.error(err);

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td colspan="5" class="border px-4 py-2 text-center text-red-600 font-semibold">
            Error loading RSVP data.
            </td>
        `;
        tableBody.appendChild(tr);
    }
  }

  async function clearEntries() {
    const confirmed = confirm(
        "Are you sure you want to delete ALL RSVP entries? This cannot be undone."
    );

    if (!confirmed) return;

    try {
        const response = await fetch(`${API_BASE}/rsvps`, {
            method: "DELETE",
        });

        if (!response.ok) {
            throw new Error("Could not clear RSVPs.");
        }

        alert("All RSVP entries were cleared.");
        loadRSVPs();
    } 
    catch (err) {
        console.error(err);
        alert("Error clearing RSVP entries.");
    }
  }
});