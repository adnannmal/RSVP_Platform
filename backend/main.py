from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, field_validator
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader

from datetime import datetime, timezone
import os
import csv
import io
import re
import base64
import httpx #type: ignore

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

# ──EMAILJS configuration ────────────────────────────────────────────────────────────────────
EMAILJS_SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID")
EMAILJS_TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID")
EMAILJS_PUBLIC_KEY = os.getenv("EMAILJS_PUBLIC_KEY")
EMAILJS_PRIVATE_KEY = os.getenv("EMAILJS_PRIVATE_KEY")

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://psa-rsvp.vercel.app")
EVENT_LOCATION = os.getenv("EVENT_LOCATION", "Hofstra University")
EVENT_LOCATION_LINK = os.getenv("EVENT_LOCATION_LINK","https://www.google.com/maps/search/?api=1&query=Hofstra%20University")
EVENT_DATE = os.getenv("EVENT_DATE", "August 1, 2026")
EVENT_TIME = os.getenv("EVENT_TIME", "6:00 PM - 9:00 PM")
EVENT_START_UTC = os.getenv("EVENT_START_UTC", "20260801T220000Z")
EVENT_END_UTC = os.getenv("EVENT_END_UTC", "20260802T010000Z")
EVENT_CAPACITY = int(os.getenv("EVENT_CAPACITY", "1"))

# ── Helpers ────────────────────────────────────────────────────────────────────
def est_now() -> str:
    """Return current time formatted in US/Eastern with daylight saving handled."""
    from zoneinfo import ZoneInfo

    eastern = datetime.now(ZoneInfo("America/New_York"))
    return eastern.strftime("%Y-%m-%d %I:%M:%S %p %Z")

def doc_to_dict(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serialisable dict."""
    doc["id"] = str(doc.pop("_id"))
    return doc

def require_admin(request: Request):
    pin = request.headers.get("x-admin-pin")

    if pin != ADMIN_PIN:
        raise HTTPException(status_code=401, detail="Unauthorized admin access.")

def attendee_count_from_doc(doc: dict) -> int:
    count = 1  # main RSVP person

    if doc.get("guest1fname") or doc.get("guest1lname"):
        count += 1

    if doc.get("guest2fname") or doc.get("guest2lname"):
        count += 1

    return count

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
    ticketExpire:    str = ""

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

#  ─── Email helper functions ────────────────────────────────────────────────────────────────────
def escape_ics_text(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\n", "\\n")
    )


def build_calendar_invite(ticket_id: str, full_name: str) -> str:
    event_title = "Hofstra PSA Event"
    description = f"RSVP confirmed for {full_name}. Ticket ID: {ticket_id}"

    now_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    ics = "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Hofstra PSA//RSVP Platform//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{ticket_id}@hofstrapsa",
        f"DTSTAMP:{now_utc}",
        f"DTSTART:{EVENT_START_UTC}",
        f"DTEND:{EVENT_END_UTC}",
        f"SUMMARY:{escape_ics_text(event_title)}",
        f"LOCATION:{escape_ics_text(EVENT_LOCATION)}",
        f"DESCRIPTION:{escape_ics_text(description)}",
        "END:VEVENT",
        "END:VCALENDAR",
        ""
    ])

    return ics


async def send_confirmation_email(doc: dict, ticket_id: str):
    if not all([EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, EMAILJS_PUBLIC_KEY]):
        print("EmailJS is not fully configured.")
        print("EMAILJS_SERVICE_ID:", bool(EMAILJS_SERVICE_ID))
        print("EMAILJS_TEMPLATE_ID:", bool(EMAILJS_TEMPLATE_ID))
        print("EMAILJS_PUBLIC_KEY:", bool(EMAILJS_PUBLIC_KEY))
        print("EMAILJS_PRIVATE_KEY:", bool(EMAILJS_PRIVATE_KEY))
        return

    full_name = f"{doc.get('fname', '')} {doc.get('lname', '')}".strip()

    guest1 = f"{doc.get('guest1fname', '')} {doc.get('guest1lname', '')}".strip()
    guest2 = f"{doc.get('guest2fname', '')} {doc.get('guest2lname', '')}".strip()
    guests = ", ".join([g for g in [guest1, guest2] if g]) or "N/A"

    ticket_link = f"{FRONTEND_URL}/ticket.html?id={ticket_id}"

    ics_content = build_calendar_invite(ticket_id, full_name)
    ics_base64 = base64.b64encode(ics_content.encode("utf-8")).decode("utf-8")

    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "accessToken": EMAILJS_PRIVATE_KEY,
        "template_params": {
            "name": full_name,
            "email": doc.get("email", ""),
            "guests": guests,
            "ticket_link": ticket_link,
            "event_location": EVENT_LOCATION,
            "event_location_link": EVENT_LOCATION_LINK,
            "event_date": EVENT_DATE,
            "event_time": EVENT_TIME,
        },
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            json=payload,
        )

    if response.status_code != 200:
        print("EmailJS error:", response.status_code, response.text)
    else:
        print("Confirmation email sent to", doc.get("email", ""))

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "PSA RSVP backend is running"}


# ── Submit RSVP ────────────────────────────────────────────────────────────────
@app.post("/submit")
async def submit_rsvp(data: RSVPSubmit):
    existing = await col.find_one({
        "$or": [
            {"email": data.email},
            {"hofstraId": data.hofstraId}
        ]
    })

    if existing:
        raise HTTPException(
            status_code=409,
            detail="An RSVP already exists for this email address or Hofstra ID."
        )

    # Count total attendees already taking capacity
    active_attendee_count = 0

    async for existing_doc in col.find({
        "approvalStatus": {
            "$in": ["pending", "approved"]
        }
    }):
        active_attendee_count += attendee_count_from_doc(existing_doc)

    doc = data.model_dump()
    new_attendee_count = attendee_count_from_doc(doc)

    if active_attendee_count + new_attendee_count > EVENT_CAPACITY:
        approval_status = "waitlisted"
        message = "RSVP submitted successfully. The event is currently full, so you have been placed on the waitlist."
    else:
        approval_status = "pending"
        message = "RSVP submitted successfully. We will send a confirmation email with ticket details once approved."

    doc["submitTime"] = est_now()
    doc["approvalStatus"] = approval_status
    doc["emailSent"] = False
    doc["attendeeCount"] = new_attendee_count

    result = await col.insert_one(doc)
    ticket_id = str(result.inserted_id)

    return {
        "success": True,
        "id": ticket_id,
        "approvalStatus": approval_status,
        "attendeeCount": new_attendee_count,
        "message": message
    }

# ── Get single ticket (for ticket scan) ───────────────────────────────────────────
@app.get("/ticket/{ticket_id}")
async def get_ticket(ticket_id: str):
    try:
        oid = ObjectId(ticket_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ticket ID format.")

    doc = await col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    
    approval_status = doc.get("approvalStatus", "pending")

    if approval_status != "approved":
        return {
            "ok": False,
            "error": "This RSVP has not been approved yet."
        }

    # Check ticket expiry
    ticket_expire = doc.get("ticketExpire", "")
    if ticket_expire:
        try:
            expire_dt = datetime.fromisoformat(ticket_expire.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expire_dt:
                return {"ok": False, "error": "This ticket has expired."}
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
async def list_rsvps(request: Request):
    require_admin(request)

    docs = []
    async for doc in col.find().sort("submitTime", -1):
        docs.append(doc_to_dict(doc))
    return docs


# ── Delete all RSVPs (admin) ───────────────────────────────────────────────────
@app.delete("/rsvps")
async def clear_rsvps(request: Request):
    require_admin(request)

    result = await col.delete_many({})
    return {"deleted": result.deleted_count}


# ── Export CSV ─────────────────────────────────────────────────────────────────
@app.get("/export.csv")
async def export_csv(request: Request):
    require_admin(request)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "First Name", "Last Name", "Email", "Hofstra ID",
        "Status", "Guest 1", "Guest 2", "Submit Time"
    ])

    async for doc in col.find().sort("submitTime", 1):
        g1 = f"{doc.get('guest1fname','')} {doc.get('guest1lname','')}".strip()
        g2 = f"{doc.get('guest2fname','')} {doc.get('guest2lname','')}".strip()

        writer.writerow([
            str(doc["_id"]),
            doc.get("fname", ""),
            doc.get("lname", ""),
            doc.get("email", ""),
            doc.get("hofstraId", ""),
            doc.get("approvalStatus", ""),
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
    emerald_deep = "#022c22"
    emerald_dark = "#064e3b"
    emerald_mid = "#047857"
    light_green = "#ecfdf5"
    gold = "#d4af37"
    off_white = "#f9fafb"
    light_gray = "#e5e7eb"
    gray = "#4b5563"
    black_green = "#011c16"

    # Event info
    event_location = "Hofstra University"  # Change this to your real event location

    # Logo path
    logo_path = "Images/logo.png"

    # Data
    ticket_id = str(doc["_id"])
    full_name = f"{doc.get('fname', '')} {doc.get('lname', '')}".strip()
    email = doc.get("email", "")

    guest1 = f"{doc.get('guest1fname', '')} {doc.get('guest1lname', '')}".strip()
    guest2 = f"{doc.get('guest2fname', '')} {doc.get('guest2lname', '')}".strip()
    guests = [g for g in [guest1, guest2] if g]
    guest_text = ", ".join(guests) if guests else "N/A"

    pdf.setTitle("PSA Event Ticket")

    # Background
    pdf.setFillColor(emerald_deep)
    pdf.rect(0, 0, width, height, fill=True, stroke=False)

    # Main ticket card - crisp edges
    card_x = 0.85 * inch
    card_y = 1.0 * inch
    card_w = width - 1.7 * inch
    card_h = height - 2.0 * inch

    pdf.setFillColor("white")
    pdf.rect(card_x, card_y, card_w, card_h, fill=True, stroke=False)

    # Outer gold border
    pdf.setStrokeColor(gold)
    pdf.setLineWidth(2)
    pdf.rect(card_x, card_y, card_w, card_h, fill=False, stroke=True)

    # Inner border
    pdf.setStrokeColor(light_gray)
    pdf.setLineWidth(1)
    pdf.rect(
        card_x + 0.18 * inch,
        card_y + 0.18 * inch,
        card_w - 0.36 * inch,
        card_h - 0.36 * inch,
        fill=False,
        stroke=True,
    )

    # Top header block
    header_h = 1.55 * inch
    pdf.setFillColor(off_white)
    pdf.rect(card_x, card_y + card_h - header_h, card_w, header_h, fill=True, stroke=False)

    # Logo
    try:
        logo = ImageReader(logo_path)
        logo_size = 0.72 * inch
        pdf.drawImage(
            logo,
            width / 2 - logo_size / 2,
            card_y + card_h - 0.78 * inch,
            width=logo_size,
            height=logo_size,
            mask="auto",
        )
    except Exception:
        # If logo is missing, the PDF still generates
        pass

    # Header text
    pdf.setFillColor(emerald_deep)
    pdf.setFont("Helvetica-Bold", 25)
    pdf.drawCentredString(width / 2, card_y + card_h - 1.08 * inch, "PSA EVENT TICKET")

    pdf.setFillColor(gold)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(
        width / 2,
        card_y + card_h - 1.32 * inch,
        "HOFSTRA PAKISTANI STUDENTS ASSOCIATION"
    )

    # Header bottom line
    pdf.setStrokeColor(gold)
    pdf.setLineWidth(1.2)
    pdf.line(card_x, card_y + card_h - header_h, card_x + card_w, card_y + card_h - header_h)

    # RSVP confirmed label
    badge_w = 2.9 * inch
    badge_h = 0.52 * inch
    badge_x = (width - badge_w) / 2
    badge_y = card_y + card_h - header_h - 0.75 * inch

    pdf.setFillColor(light_green)
    pdf.roundRect(badge_x, badge_y, badge_w, badge_h, 14, fill=True, stroke=False)

    pdf.setStrokeColor(emerald_mid)
    pdf.setLineWidth(0.7)
    pdf.roundRect(badge_x, badge_y, badge_w, badge_h, 14, fill=False, stroke=True)

    pdf.setFillColor(emerald_dark)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, badge_y + 0.18 * inch, "✓ RSVP Confirmed")


    # Details section
    details_x = card_x + 0.55 * inch
    details_y = badge_y - 2.0 * inch
    details_w = card_w - 1.1 * inch
    details_h = 1.55 * inch

    pdf.setFillColor("white")
    pdf.rect(details_x, details_y, details_w, details_h, fill=True, stroke=False)

    pdf.setStrokeColor(light_gray)
    pdf.setLineWidth(1)
    pdf.rect(details_x, details_y, details_w, details_h, fill=False, stroke=True)

    label_x = details_x + 0.28 * inch
    value_x = details_x + 1.35 * inch
    y = details_y + details_h - 0.38 * inch

    def draw_field(label, value):
        nonlocal y

        pdf.setFillColor(gray)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(label_x, y, label.upper())

        pdf.setFillColor(black_green)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(value_x, y, value if value else "N/A")

        y -= 0.34 * inch

    draw_field("Name", full_name)
    draw_field("Email", email)
    draw_field("Guests", guest_text)
    draw_field("Location", event_location)

    # Divider
    divider_y = details_y - 0.55 * inch
    pdf.setStrokeColor(light_gray)
    pdf.setLineWidth(1)
    pdf.line(card_x + 0.55 * inch, divider_y, card_x + card_w - 0.55 * inch, divider_y)

    # Barcode title
    barcode_label_y = divider_y - 0.45 * inch

    pdf.setFillColor(gray)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(width / 2, barcode_label_y, "CHECK-IN BARCODE")

    # Barcode white container
    barcode_box_w = card_w - 1.2 * inch
    barcode_box_h = 1.25 * inch
    barcode_box_x = (width - barcode_box_w) / 2
    barcode_box_y = barcode_label_y - 1.45 * inch

    pdf.setFillColor(off_white)
    pdf.rect(barcode_box_x, barcode_box_y, barcode_box_w, barcode_box_h, fill=True, stroke=False)

    pdf.setStrokeColor(light_gray)
    pdf.setLineWidth(1)
    pdf.rect(barcode_box_x, barcode_box_y, barcode_box_w, barcode_box_h, fill=False, stroke=True)

    # Barcode-style visual, centered and crisp
    pattern = [
        3, 1, 1, 2, 4, 1, 2, 3,
        1, 1, 3, 2, 1, 4, 2, 1,
        3, 1, 2, 2, 4, 1, 1, 3
    ]

    bars = pattern * 3
    gap = 2.1
    total_barcode_width = sum(bars) + (len(bars) - 1) * gap
    barcode_x = (width - total_barcode_width) / 2
    barcode_y = barcode_box_y + 0.38 * inch
    bar_height = 0.58 * inch

    pdf.setFillColor(black_green)

    x = barcode_x
    for i, bar_width in enumerate(bars):
        if i % 2 == 0:
            pdf.rect(x, barcode_y, bar_width, bar_height, fill=True, stroke=False)
        x += bar_width + gap

    # Ticket ID under barcode
    pdf.setFillColor(black_green)
    pdf.setFont("Courier-Bold", 9)
    pdf.drawCentredString(width / 2, barcode_box_y + 0.18 * inch, ticket_id)

    # Footer
    pdf.setFillColor(gray)
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(
        width / 2,
        card_y + 0.48 * inch,
        "This ticket is valid for the listed attendee and guests only."
    )

    pdf.setFillColor(gold)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(
        width / 2,
        card_y + 0.28 * inch,
        "Please present this ticket at event check-in."
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

# ── Approve RSVP ─────────────────────────────────────────
@app.patch("/rsvps/{ticket_id}/approve")
async def approve_rsvp(ticket_id: str, request: Request):
    require_admin(request)

    try:
        oid = ObjectId(ticket_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid RSVP ID format.")

    doc = await col.find_one({"_id": oid})

    if not doc:
        raise HTTPException(status_code=404, detail="RSVP not found.")

    if doc.get("approvalStatus") == "approved" and doc.get("emailSent") is True:
        return {
            "success": True,
            "message": "RSVP was already approved and email was already sent."
        }

    await col.update_one(
        {"_id": oid},
        {
            "$set": {
                "approvalStatus": "approved",
                "approvedTime": est_now()
            }
        }
    )

    updated_doc = await col.find_one({"_id": oid})

    await send_confirmation_email(updated_doc, ticket_id)

    await col.update_one(
        {"_id": oid},
        {
            "$set": {
                "emailSent": True,
                "emailSentTime": est_now()
            }
        }
    )

    return {
        "success": True,
        "message": "RSVP approved and confirmation email sent."
    }

# ── Reject RSVP ─────────────────────────────────────────
@app.patch("/rsvps/{ticket_id}/reject")
async def reject_rsvp(ticket_id: str, request: Request):
    require_admin(request)

    try:
        oid = ObjectId(ticket_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid RSVP ID format.")

    doc = await col.find_one({"_id": oid})

    if not doc:
        raise HTTPException(status_code=404, detail="RSVP not found.")

    await col.update_one(
        {"_id": oid},
        {
            "$set": {
                "approvalStatus": "rejected",
                "rejectedTime": est_now()
            }
        }
    )

    return {
        "success": True,
        "message": "RSVP rejected."
    }