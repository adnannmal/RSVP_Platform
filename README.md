# 🇵🇰 Hofstra PSA RSVP Platform

> A polished, event-ready RSVP and check-in system built for the **Hofstra Pakistani Student Association (PSA)**.
>
> Collect RSVPs, manage approvals, control capacity, issue QR tickets, scan attendees at the door, and track event analytics from one lightweight web platform.

![Frontend](https://img.shields.io/badge/Frontend-HTML%20%2B%20TailwindCSS-0ea5e9?style=for-the-badge)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge)
![Database](https://img.shields.io/badge/Database-MongoDB-22c55e?style=for-the-badge)
![Deploy](https://img.shields.io/badge/Deploy-Vercel%20%2B%20Render-black?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active%20Development-d4af37?style=for-the-badge)

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