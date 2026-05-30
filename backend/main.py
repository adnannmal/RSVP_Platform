from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, field_validator
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

from datetime import datetime, timezone
import os
import csv
import io
import re

# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(title="PSA RSVP Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://psa-rsvp.vercel.app",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ── MongoDB ────────────────────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
ADMIN_PIN  = os.getenv("ADMIN_PIN", "123456")   # Change via env var

client = AsyncIOMotorClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
db     = client["rsvp_db"]
col    = db["rsvps"]

# ── Helpers ────────────────────────────────────────────────────────────────────
def est_now() -> str:
    """Return current time formatted in US/Eastern (EST offset)."""
    from datetime import timedelta
    # Simple EST offset (UTC-5). For auto-DST use pytz/zoneinfo.
    est = datetime.now(timezone.utc) - timedelta(hours=5)
    return est.strftime("%Y-%m-%d %I:%M:%S %p EST")

def doc_to_dict(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serialisable dict."""
    doc["id"] = str(doc.pop("_id"))
    return doc

# ── Schemas ────────────────────────────────────────────────────────────────────
class RSVPSubmit(BaseModel):
    fname:       str
    lname:       str
    email:       str
    hofstraId:   str
    status:      str          # "student" | "guest"
    guest1fname: str = ""
    guest1lname: str = ""
    guest2fname: str = ""
    guest2lname: str = ""
    qrExpire:    str = ""

    @field_validator("email")
    @classmethod
    def must_be_hofstra(cls, v: str) -> str:
        if not v.lower().endswith("@pride.hofstra.edu"):
            raise ValueError("Email must be a @pride.hofstra.edu address")
        return v.lower()

    @field_validator("hofstraId")
    @classmethod
    def must_match_hofstra_id(cls, v: str) -> str:
        if not re.fullmatch(r"h\d{9}", v, re.IGNORECASE):
            raise ValueError("Hofstra ID must be in format h123456789")
        return v.lower()

class PinVerify(BaseModel):
    pin: str

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "PSA RSVP backend is running"}


# ── Submit RSVP ────────────────────────────────────────────────────────────────
@app.post("/submit")
async def submit_rsvp(data: RSVPSubmit):
    # Prevent duplicate submissions by email
    existing = await col.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=409, detail="An RSVP already exists for this email address.")

    doc = data.model_dump()
    doc["submitTime"] = est_now()

    result = await col.insert_one(doc)
    return {"success": True, "id": str(result.inserted_id)}


# ── Get single ticket (for QR scan) ───────────────────────────────────────────
@app.get("/ticket/{ticket_id}")
async def get_ticket(ticket_id: str):
    try:
        oid = ObjectId(ticket_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ticket ID format.")

    doc = await col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    # Check QR expiry
    qr_expire = doc.get("qrExpire", "")
    if qr_expire:
        try:
            expire_dt = datetime.fromisoformat(qr_expire.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expire_dt:
                return {"ok": False, "error": "This QR code has expired."}
        except ValueError:
            pass

    return {"ok": True, "ticket": doc_to_dict(doc)}


# ── Verify PIN ─────────────────────────────────────────────────────────────────
@app.post("/verify-pin")
async def verify_pin(body: PinVerify):
    if body.pin == ADMIN_PIN:
        return {"ok": True}
    return {"ok": False}


# ── List all RSVPs (admin) ─────────────────────────────────────────────────────
@app.get("/rsvps")
async def list_rsvps():
    docs = []
    async for doc in col.find().sort("submitTime", -1):
        docs.append(doc_to_dict(doc))
    return docs


# ── Delete all RSVPs (admin) ───────────────────────────────────────────────────
@app.delete("/rsvps")
async def clear_rsvps():
    result = await col.delete_many({})
    return {"deleted": result.deleted_count}


# ── Export CSV ─────────────────────────────────────────────────────────────────
@app.get("/export.csv")
async def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "First Name", "Last Name", "Email", "Hofstra ID",
                     "Status", "Guest 1", "Guest 2", "Submit Time"])

    async for doc in col.find().sort("submitTime", 1):
        g1 = f"{doc.get('guest1fname','')} {doc.get('guest1lname','')}".strip()
        g2 = f"{doc.get('guest2fname','')} {doc.get('guest2lname','')}".strip()
        writer.writerow([
            str(doc["_id"]),
            doc.get("fname", ""),
            doc.get("lname", ""),
            doc.get("email", ""),
            doc.get("hofstraId", ""),
            doc.get("status", ""),
            g1 or "N/A",
            g2 or "N/A",
            doc.get("submitTime", ""),
        ])

    output.seek(0)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"rsvp_export_{date_str}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

# ── Generate PDF Ticket ─────────────────────────────────────────────────────────
@app.get("/generate-pdf")
async def generate_pdf(id: str):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ticket ID format.")

    doc = await col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Colors
    emerald_dark = "#064e3b"
    emerald_deep = "#022c22"
    gold = "#d4af37"
    light_green = "#ecfdf5"
    gray = "#4b5563"
    light_gray = "#e5e7eb"

    # Data
    ticket_id = str(doc["_id"])
    full_name = f"{doc.get('fname', '')} {doc.get('lname', '')}".strip()
    email = doc.get("email", "")
    hofstra_id = doc.get("hofstraId", "")
    submit_time = doc.get("submitTime", "")

    guest1 = f"{doc.get('guest1fname', '')} {doc.get('guest1lname', '')}".strip()
    guest2 = f"{doc.get('guest2fname', '')} {doc.get('guest2lname', '')}".strip()
    guests = [g for g in [guest1, guest2] if g]

    pdf.setTitle("PSA Event Ticket")

    # Page background
    pdf.setFillColor(emerald_deep)
    pdf.rect(0, 0, width, height, fill=True, stroke=False)

    # Main ticket card
    card_x = 0.75 * inch
    card_y = 1.0 * inch
    card_w = width - 1.5 * inch
    card_h = height - 2.0 * inch

    pdf.setFillColor("white")
    pdf.roundRect(card_x, card_y, card_w, card_h, 18, fill=True, stroke=False)

    # Header
    pdf.setFillColor(emerald_dark)
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(
        width / 2,
        card_y + card_h - 0.75 * inch,
        "PSA EVENT TICKET"
    )

    pdf.setFillColor(gold)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(
        width / 2,
        card_y + card_h - 1.05 * inch,
        "HOFSTRA PAKISTANI STUDENTS ASSOCIATION"
    )

    # Divider under header
    pdf.setStrokeColor(light_gray)
    pdf.setLineWidth(1)
    pdf.line(
        card_x + 0.45 * inch,
        card_y + card_h - 1.35 * inch,
        card_x + card_w - 0.45 * inch,
        card_y + card_h - 1.35 * inch
    )

    # Centered confirmation badge
    badge_w = 2.6 * inch
    badge_h = 0.5 * inch
    badge_x = (width - badge_w) / 2
    badge_y = card_y + card_h - 2.05 * inch

    pdf.setFillColor(light_green)
    pdf.roundRect(badge_x, badge_y, badge_w, badge_h, 12, fill=True, stroke=False)

    pdf.setFillColor(emerald_dark)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, badge_y + 0.18 * inch, "✓ RSVP Confirmed")

    # Ticket details section
    y = card_y + card_h - 2.75 * inch
    label_x = card_x + 0.65 * inch
    value_x = card_x + 2.15 * inch

    def draw_field(label, value):
        nonlocal y

        pdf.setFillColor(gray)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(label_x, y, label.upper())

        pdf.setFillColor(emerald_deep)
        pdf.setFont("Helvetica", 12)
        pdf.drawString(value_x, y, value if value else "N/A")

        y -= 0.42 * inch

    draw_field("Name", full_name)
    draw_field("Email", email)
    draw_field("Hofstra ID", hofstra_id)
    draw_field("Submitted", submit_time)

    # Guests
    pdf.setFillColor(gray)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(label_x, y, "GUESTS")

    pdf.setFillColor(emerald_deep)
    pdf.setFont("Helvetica", 12)

    if guests:
        pdf.drawString(value_x, y, guests[0])
        y -= 0.32 * inch

        if len(guests) > 1:
            pdf.drawString(value_x, y, guests[1])
            y -= 0.32 * inch
    else:
        pdf.drawString(value_x, y, "N/A")
        y -= 0.42 * inch

    # Dashed divider
    y -= 0.25 * inch
    pdf.setDash(4, 4)
    pdf.setStrokeColor(light_gray)
    pdf.line(
        card_x + 0.45 * inch,
        y,
        card_x + card_w - 0.45 * inch,
        y
    )
    pdf.setDash()

    # Ticket verification code
    y -= 0.55 * inch
    pdf.setFillColor(gray)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawCentredString(width / 2, y, "TICKET VERIFICATION CODE")

    y -= 0.45 * inch
    pdf.setFillColor(emerald_deep)
    pdf.setFont("Courier-Bold", 16)
    pdf.drawCentredString(width / 2, y, ticket_id)

    # Centered barcode-style visual
    y -= 0.65 * inch
    barcode_y = y
    bar_height = 0.55 * inch

    pdf.setFillColor(emerald_deep)

    pattern = [
        2, 1, 3, 1, 1, 2, 4, 1,
        2, 3, 1, 1, 3, 2, 1, 4,
        2, 1, 3, 1, 2, 2, 4, 1
    ]

    bars = pattern * 3
    total_barcode_width = sum(bars) + (len(bars) - 1) * 2
    barcode_x = (width - total_barcode_width) / 2

    x = barcode_x

    for i, bar_width in enumerate(bars):
        if i % 2 == 0:
            pdf.rect(x, barcode_y, bar_width, bar_height, fill=True, stroke=False)

        x += bar_width + 2

    # Footer note
    pdf.setFillColor(gray)
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawCentredString(
        width / 2,
        card_y + 0.55 * inch,
        "One ticket is valid for the listed attendee and guests."
    )

    pdf.setFillColor(gold)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(
        width / 2,
        card_y + 0.32 * inch,
        "Please present this ticket at check-in."
    )

    pdf.showPage()
    pdf.save()

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="PSA_Event_Ticket_{id}.pdf"'
        },
    )