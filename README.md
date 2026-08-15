# RSVP Platform

A polished, event-ready RSVP and check-in system built for the **Hofstra Pakistani Student Association (PSA)**.

Collect RSVPs, manage approvals, control capacity, issue QR tickets, scan attendees at the door, and track event analytics from one lightweight web platform.

---

## ✨ What This Project Does

The PSA RSVP Platform is a full event management system for student organization events. It replaces manual sign-up forms with a clean web experience that supports:

- RSVP form submission
- Hofstra email validation
- Guest tracking
- Admin approval before tickets are sent
- Automatic waitlist placement when capacity is full
- Email ticket delivery through EmailJS
- QR ticket display
- PDF ticket download
- Scanner-based attendance check-in
- Attendance analytics dashboard
- CSV export for event records

---

## 🎟️ Event Flow

```text
User opens RSVP site
        ↓
Completes RSVP form
        ↓
Backend checks duplicate email / Hofstra ID
        ↓
Backend checks total attendee capacity
        ↓
User is marked as pending or waitlisted
        ↓
Admin approves RSVP
        ↓
Confirmation email is sent with ticket link
        ↓
User opens ticket.html?id=<ticket_id>
        ↓
Ticket page shows QR code + ticket details
        ↓
Event staff scans QR code at check-in
        ↓
Backend marks user as attended
        ↓
Analytics dashboard updates attendance totals
```

---

## 🚀 Core Features

### ✅ RSVP Form

- Clean TailwindCSS RSVP page
- Hofstra Pride email restriction
- Hofstra ID validation
- Guest support
- Duplicate RSVP protection
- Success page after submission

### 🧑‍💼 Admin Dashboard

- PIN-protected admin access
- Live RSVP table
- Approve / reject workflow
- Waitlist status support
- CSV export
- Clear all entries for testing or reset
- Dashboard cards for:
  - Total RSVPs
  - Pending
  - Waitlisted
  - Approved
  - Rejected
  - Total attending

### 📬 Email Ticket Delivery

Tickets are not sent immediately. The system waits for admin approval first.

```text
Submitted → Pending → Admin Approves → Email Sent → Ticket Link Works
```

The email includes:

- Attendee name
- Guest names
- Event date and time
- Event location
- Ticket link

### 🧾 QR Ticket Page

Each approved RSVP gets a unique ticket page:

```text
ticket.html?id=<ticket_id>
```

The ticket page displays:

- Full name
- Email
- Guest list
- QR code for check-in
- Ticket ID
- PDF ticket download button

### 🧍 Waitlist System

Capacity is based on **total attendees**, not just form submissions.

```text
1 RSVP with no guests = 1 attendee
1 RSVP with 1 guest = 2 attendees
1 RSVP with 2 guests = 3 attendees
```

When total active attendees reaches the event capacity:

- New submissions are automatically marked as `waitlisted`
- Waitlisted users do not receive ticket emails immediately
- Admin can approve from the waitlist if a spot opens

### 📷 QR Scanner

The scanner page is designed for event check-in:

```text
scanner.html
```

It supports:

- Phone camera QR scanning
- Manual ticket ID entry
- Multiple ticket scans in one session
- Warning if a ticket was already scanned
- Ticket details after scan
- Recent scans list

### 📊 Attendance Analytics

The separate analytics page shows check-in performance:

```text
analytics.html
```

It tracks:

- Approved tickets
- Checked-in guests
- Not checked in
- Attendance rate
- Total attendees
- Scan count
- Check-in time

---

## 🛠️ Tech Stack

### Frontend

- HTML
- TailwindCSS CDN
- Vanilla JavaScript
- QRCode.js
- html5-qrcode
- Vercel hosting

### Backend

- Python
- FastAPI
- MongoDB Atlas
- Motor async MongoDB driver
- Pydantic validation
- ReportLab PDF generation
- EmailJS API integration
- Render hosting

---

## 📁 Project Structure

```text
psa-rsvp/
├── Images/
│   ├── logo.png
│   ├── pakistan_flag.png
│   ├── email.jpg
│   └── insta.jpg
│
├── index.html          # Countdown / form opening page
├── home.html           # Main RSVP form
├── success.html        # Submission confirmation page
├── ticket.html         # Approved ticket + QR code page
├── admin.html          # Admin approval dashboard
├── analytics.html      # Attendance analytics dashboard
├── scanner.html        # QR scanner / check-in page
├── test.html           # Testing / development page
├── notes.txt           # Development notes
└── README.md           # Project documentation
```

Backend files are usually stored in a separate backend folder:

```text
backend/
├── main.py             # FastAPI backend
├── requirements.txt    # Python dependencies
└── README.md           # Backend-specific documentation
```

---

## 🔐 Security Model

This project uses lightweight admin protection suitable for a student organization event platform.

- Admin dashboard requires a PIN
- Admin-only backend routes require `x-admin-pin`
- Ticket links only work after approval
- Rejected, pending, and waitlisted tickets cannot be viewed as valid tickets
- Duplicate RSVP entries are blocked by email and Hofstra ID

---

## 🏆 Project Goal

The goal of this platform is to give PSA a professional, reliable, and easy-to-use RSVP system that can handle the full event lifecycle:

```text
Invite → RSVP → Approve → Ticket → Scan → Analyze
```

Built for real events, real attendees, and real check-in pressure.

---

## 👤 Built For

**Hofstra Pakistani Student Association**  
A student-run platform designed to make event management smoother, faster, and more professional.