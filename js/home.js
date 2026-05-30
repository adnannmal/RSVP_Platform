document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("rsvpForm");
    const statusSelect = document.getElementById("statusSelect");
    const guestField = document.getElementById("guestField");
    const submitBtn = document.getElementById("submitBtn");
    const countdown = document.getElementById("countdown");

    const guest1fname = document.getElementById("guest1fname");
    const guest1lname = document.getElementById("guest1lname");
    const guest2fname = document.getElementById("guest2fname");
    const guest2lname = document.getElementById("guest2lname");

    if (!form) {
        return;
    }

    const formExpire = new Date("2026-08-01T01:00:00Z");
    const eventDate = new Date("2026-08-01T00:00:00Z");

    if (new Date() > formExpire && submitBtn) {
        submitBtn.classList.add("hidden");
    }

    if (statusSelect) {
        statusSelect.addEventListener("change", () => {
            const selected = statusSelect.value;

            if (selected === "guest") {
                guestField.classList.remove("hidden");

                guest1fname.required = true;
                guest1lname.required = true;
                guest2fname.required = false;
                guest2lname.required = false;
            } 
            else {
                guestField.classList.add("hidden");

                guest1fname.required = false;
                guest1lname.required = false;
                guest2fname.required = false;
                guest2lname.required = false;

                guest1fname.value = "";
                guest1lname.value = "";
                guest2fname.value = "";
                guest2lname.value = "";
            }
        });
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const data = {
            fname: form.fname.value.trim(),
            lname: form.lname.value.trim(),
            email: form.email.value.trim().toLowerCase(),
            hofstraId: form.hofstraId.value.trim().toLowerCase(),
            status: form.status.value,
            guest1fname: form.guest1fname.value.trim() || "",
            guest1lname: form.guest1lname.value.trim() || "",
            guest2fname: form.guest2fname.value.trim() || "",
            guest2lname: form.guest2lname.value.trim() || "",
            qrExpire: eventDate.toISOString(),
        };

        try {
            bmitBtn.disabled = true;
            submitBtn.innerText = "Submitting...";

            const response = await fetch(`${API_BASE}/submit`, {
                method: "POST",
                headers: {
                "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Submission failed.");
            }

            localStorage.setItem("ticketId", result.id);

            window.location.href = "success.html";
        } 
        catch (err) {
            console.error(err);
            alert(err.message || "Network error. Please try again.");

            submitBtn.disabled = false;
            submitBtn.innerText = "Submit RSVP";
        }
    });
    startCountdown(eventDate, countdown);
});

function startCountdown(eventDate, countdown) {
    if (!countdown) return;

    const countdownTimer = setInterval(() => {
        const now = new Date().getTime();
        const timeLeft = eventDate.getTime() - now;

        if (timeLeft <= 0) {
            countdown.style.display = "none";
            clearInterval(countdownTimer);
            return;
        }

        const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
        const hours = Math.floor(
            (timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)
        );
        const mins = Math.floor(
            (timeLeft % (1000 * 60 * 60)) / (1000 * 60)
        );
        const secs = Math.floor((timeLeft % (1000 * 60)) / 1000);

        let color = "text-black-700";

        if (timeLeft < 1000 * 60 * 60 * 24 * 3) {
            color = "text-orange-500";
        }

        if (timeLeft < 1000 * 60 * 60 * 12) {
            color = "text-yellow-500";
        }

        if (timeLeft < 1000 * 60 * 60) {
            color = "text-red-600";
        }

        countdown.className = `text-center text-lg font-semibold ${color} my-4`;
        countdown.innerHTML = `⏳ ${days}d ${hours}h ${mins}m ${secs}s left`;
    }, 1000);
}

window.openPage = function () {
    document.getElementById("contactPage")?.classList.remove("hidden");
};

window.closePage = function () {
    document.getElementById("contactPage")?.classList.add("hidden");
};