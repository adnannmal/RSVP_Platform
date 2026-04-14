from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, field_validator
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, timezone
import os
import csv
import io
import re

# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(title="PSA RSVP Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Tighten to your Vercel domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── MongoDB ────────────────────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
ADMIN_PIN  = os.getenv("ADMIN_PIN", "123456")   # Change via env var

client = AsyncIOMotorClient(MONGO_URI)
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
