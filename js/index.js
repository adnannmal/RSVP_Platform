document.addEventListener("DOMContentLoaded", () => {
    const title = document.getElementById("title");
    const countdown = document.getElementById("countdown");

    if (!title || !countdown) {
        return;
    }

    title.innerText = "RSVP Opening In";

    const open = new Date();

    // Month is 0-indexed: 0 = Jan, 6 = July
    open.setFullYear(2026, 6, 16);
    open.setHours(14);
    open.setMinutes(52);
    open.setSeconds(0);

    if (localStorage.getItem("formUnlocked") === "true") {
        window.location.href = "home.html";
        return;
    }

    const interval = setInterval(() => {
        const now = new Date();
        const timeLeft = open - now;

        if (timeLeft <= 0) {
            clearInterval(interval);

            countdown.innerText = "Redirecting...";
            title.innerText = "Form Opened";

            localStorage.setItem("formUnlocked", "true");

            setTimeout(() => {
                window.location.href = "home.html";
            }, 500);

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

        countdown.innerText = `${days}d ${hours}h ${mins}m ${secs}s`;
    }, 1000);
});