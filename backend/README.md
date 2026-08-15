# ⚡ RSVP Backend

FastAPI backend for the RSVP Platform.

Handles RSVP submissions, approval status, waitlist capacity, EmailJS ticket delivery, PDF tickets, admin data access, and attendance tracking.

---

## 🧠 Backend Responsibilities

The backend is the source of truth for the RSVP platform. It manages:

- RSVP submission validation
- Duplicate email / Hofstra ID prevention
- Event capacity and waitlist assignment
- Admin PIN verification
- Admin RSVP listing
- RSVP approval and rejection
- Email ticket sending after approval
- Ticket validation
- PDF ticket generation
- Attendance fields for check-in tracking
- CSV export

---

## 🛠️ Tech Stack

- **FastAPI** — API framework
- **Motor** — async MongoDB driver
- **MongoDB Atlas** — cloud database
- **Pydantic** — request validation
- **ReportLab** — PDF ticket generation
- **EmailJS API** — confirmation email delivery
- **httpx** — async HTTP requests
- **Render** — backend deployment

---

## 📁 Backend Structure

```text
backend/
├── main.py             # Main FastAPI application
├── requirements.txt    # Python dependencies
└── README.md           # Backend documentation
```

---

### Approval statuses

```text
pending     → submitted and waiting for admin approval
approved    → admin approved and ticket email sent
rejected    → admin rejected RSVP
waitlisted  → event capacity was already reached
```

---

## 👥 Capacity Logic

Capacity is based on **total attendees**, not just RSVP form count.

```text
Main RSVP person = 1 attendee
Guest 1 = +1 attendee
Guest 2 = +1 attendee
```

Example:

```text
Event capacity: 200
Current active attendees: 199
New RSVP with 0 guests → pending
New RSVP with 1 guest → waitlisted
New RSVP with 2 guests → waitlisted
```

Only these statuses count toward capacity:

```text
pending
approved
```

These do not count toward capacity:

```text
waitlisted
rejected
```

---

## 📬 Email Ticket Flow

Tickets are sent only after admin approval.

```text
POST /submit
    ↓
Store RSVP as pending or waitlisted
    ↓
Admin clicks Approve
    ↓
PATCH /rsvps/{ticket_id}/approve
    ↓
Backend sends EmailJS confirmation email
    ↓
User receives ticket link
```

Ticket link format:

```text
https://psa-rsvp.vercel.app/ticket.html?id=<ticket_id>
```

---

## 🔐 Admin Security

Admin-only routes require this request header:

```http
x-admin-pin: your_admin_pin
```

The PIN is stored as an environment variable:

```env
ADMIN_PIN=your_admin_pin
```

---

## 📡 API Endpoints

### Health Check

```http
GET /
```

Returns backend status.

---

### Submit RSVP

```http
POST /submit
```

Creates a new RSVP and assigns either:

```text
pending
waitlisted
```

depending on event capacity.

---

### Verify Admin PIN

```http
POST /verify-pin
```

Body:

```json
{
  "pin": "your-pin"
}
```

---

### List RSVPs

```http
GET /rsvps
```

Requires:

```http
x-admin-pin: your_admin_pin
```

Used by:

- `admin.html`
- `analytics.html`

---

### Clear RSVPs

```http
DELETE /rsvps
```

Requires admin PIN.

---

### Export CSV

```http
GET /export.csv
```

Requires admin PIN.

Exports RSVP data for spreadsheets and event records.

---

### Get Ticket

```http
GET /ticket/{ticket_id}
```

Returns ticket details only if the RSVP is approved.

If the RSVP is pending, rejected, or waitlisted, the ticket is blocked.

---

### Generate PDF Ticket

```http
GET /generate-pdf?id=<ticket_id>
```

Generates a PDF ticket using ReportLab.

---

### Approve RSVP

```http
PATCH /rsvps/{ticket_id}/approve
```

Requires admin PIN.

Does three things:

```text
1. Sets approvalStatus = approved
2. Saves approvedTime
3. Sends confirmation email
```

---

### Reject RSVP

```http
PATCH /rsvps/{ticket_id}/reject
```

Requires admin PIN.

Sets:

```text
approvalStatus = rejected
rejectedTime = current Eastern time
```

---

### Scan Ticket

```http
POST /scan/{ticket_id}
```

Requires admin PIN.

Marks an approved ticket as attended.

Recommended scan fields:

```json
{
  "attended": true,
  "checkedInTime": "2026-08-14 08:45:00 PM EDT",
  "scanCount": 1,
  "scanHistory": [
    {
      "time": "2026-08-14 08:45:00 PM EDT",
      "type": "first_scan"
    }
  ]
}
```

If the same ticket is scanned again:

```text
scanCount increases
scanHistory gets another timestamp
scanner.html shows a warning
```

---

## 🧪 Testing Checklist

- [ ] Backend root route loads
- [ ] MongoDB connects successfully
- [ ] RSVP submission works
- [ ] Duplicate email is blocked
- [ ] Duplicate Hofstra ID is blocked
- [ ] Capacity sends overflow users to waitlist
- [ ] Admin PIN works
- [ ] Admin dashboard loads RSVPs
- [ ] Approve sends EmailJS email
- [ ] Rejected ticket cannot be opened
- [ ] Waitlisted ticket cannot be opened
- [ ] Approved ticket page loads QR code
- [ ] PDF ticket downloads
- [ ] Scanner marks ticket as attended
- [ ] Duplicate scan shows warning
- [ ] Analytics page updates attendance totals

---

## 🏁 Backend Goal

The backend makes sure every event action is trusted, recorded, and traceable:

```text
RSVP submitted → capacity checked → admin reviewed → ticket sent → QR scanned → attendance tracked
```

It is the control center for the PSA RSVP Platform.
