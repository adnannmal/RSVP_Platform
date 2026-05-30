document.addEventListener("DOMContentLoaded", () => {
    tailwind.config = {
        theme: {
            extend: {
                colors: {
                emerald: {
                    800: '#064e3b',
                    900: '#022c22',
                },
                pakistan: {
                dark: '#004b23',
                light: '#007200',
                gold: '#d4af37'
                }
                }
            }
        }
    }


    try {
        confetti({
            particleCount: 160,
            spread: 80,
            origin: { y: 0.55 },
            colors: ["#004b23", "#007200", "#d4af37", "#ffffff"],
        });
    } 
    
    catch (err) {
        console.error("Confetti failed:", err);
    }

    const id = localStorage.getItem("ticketId");

    if (!id) {
        console.warn("No ticket ID found in localStorage.");
        return;
    }

    if (window.JsBarcode) {
        JsBarcode("#barcode", id, {
        format: "CODE128",
        width: 4.2,
        height: 95,
        displayValue: false,
        text: `TICKET: ${id}`,
        font: "monospace",
        fontSize: 15,
        fontOptions: "bold",
        lineColor: "#022c22",
        background: "transparent",
        });
    }

    const downloadBtn = document.getElementById("downloadBtn");

    if (!downloadBtn) {
        return;
    }

    downloadBtn.addEventListener("click", async () => {
        try {
            downloadBtn.disabled = true;
            downloadBtn.innerText = "Preparing PDF...";

            const response = await fetch(
                `${API_BASE}/generate-pdf?id=${encodeURIComponent(id)}`
            );

            if (!response.ok) {
                throw new Error("Server error while generating PDF.");
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");

            a.href = url;
            a.download = `PSA_Event_Ticket_${id}.pdf`;

            document.body.appendChild(a);
            a.click();
            a.remove();

            URL.revokeObjectURL(url);

            downloadBtn.disabled = false;
            downloadBtn.innerText = "Download PDF Ticket ⬇";
        } 
        catch (err) {
            console.error(err);
            alert("Sorry, there was an error generating your PDF. Please try again later.");

            downloadBtn.disabled = false;
            downloadBtn.innerText = "Download PDF Ticket ⬇";
        }
    });
});