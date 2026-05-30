let ticketData = null;

document.addEventListener("DOMContentLoaded", async () => {
    const query = new URLSearchParams(window.location.search);
    const id = query.get("id");

    const authBox = document.getElementById("authUser");
    const ticketBox = document.getElementById("ticket");
    const submitPin = document.getElementById("submitPin");

    if (!id) {
        document.body.innerHTML = `
        <p class="text-red-700 text-center font-bold">
            ❌ Invalid ticket link.
        </p>
        `;
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/ticket/${encodeURIComponent(id)}`);
        const result = await response.json();

        if (!response.ok || !result.ok) {
            throw new Error(result.error || result.detail || "Ticket not found.");
        }

        ticketData = result.ticket;
    } 
    catch (err) {
        console.error(err);

        document.body.innerHTML = `
        <p class="text-red-700 text-center font-bold">
            ❌ This ticket is invalid or expired.
        </p>
        `;
        return;
    }

    if (submitPin) {
        submitPin.addEventListener("click", checkPass);
    }

    const passInput = document.getElementById("pass");

    if (passInput) {
        passInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            checkPass();
        }
        });
    }
});

async function checkPass() {
    const input = document.getElementById("pass");
    const error = document.getElementById("error");
    const authBox = document.getElementById("authUser");
    const ticketBox = document.getElementById("ticket");

    if (!input || !ticketBox || !ticketData) return;

    try {
        const response = await fetch(`${API_BASE}/verify-pin`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ pin: input.value.trim() }),
        });

        const result = await response.json();

        if (!result.ok) {
            error?.classList.remove("hidden");
            return;
        }

        authBox?.classList.add("hidden");

        let guestHTML = "";

        if (ticketData.guest1fname || ticketData.guest1lname) {
            guestHTML += `<li>${ticketData.guest1fname || ""} ${ticketData.guest1lname || ""}</li>`;
        }

        if (ticketData.guest2fname || ticketData.guest2lname) {
            guestHTML += `<li>${ticketData.guest2fname || ""} ${ticketData.guest2lname || ""}</li>`;
        }

        ticketBox.innerHTML = `
        <div class="space-y-3 text-left">
            <h2 class="text-2xl font-bold text-green-700 mb-2">🎟️ Event Ticket</h2>

            <p>
            <strong>Full Name:</strong>
            ${ticketData.fname || ""} ${ticketData.lname || ""}
            </p>

            <p>
            <strong>Email:</strong>
            ${ticketData.email || ""}
            </p>

            <p>
            <strong>Hofstra ID:</strong>
            ${ticketData.hofstraId || ""}
            </p>

            ${
            guestHTML
                ? `<div>
                    <p class="font-semibold">Guests:</p>
                    <ul class="list-disc list-inside text-gray-700">${guestHTML}</ul>
                </div>`
                : `<p><strong>Guests:</strong> N/A</p>`
            }
        </div>
        `;

        ticketBox.classList.remove("hidden");
    } 
    catch (err) {
        console.error(err);
        alert("Error verifying PIN. Please try again.");
    }
}

window.checkPass = checkPass;