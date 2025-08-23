

A full-featured RSVP platform built for the Hofstra Pakistani Student Association (PSA). This system manages user submissions, generates unique QR codes, and includes an administrative dashboard (locally stored) — all with a great user experience in mind.

# Key Features

Seamless User Flow

- **Smooth Submission Experience**: Once a user completes the RSVP form, they are automatically transitioned to a new confirmation screen, providing instant feedback.
- **QR Code Ticket**: Upon successful submission, a unique QR code is generated. This can be scanned at the event for entry verification.
- **QR Code Redirect Page**: When scanned, the QR takes the user to a dedicated page that displays RSVP data after entering a secure token.

--------------------------------------------------------------------------------

Intelligent Form Behavior

- **Flags and UI Polish**: Pakistani flags on either side of the screen are positioned closer and styled to complement the form without overlap.
- **“Contact Us” Button**: A clickable help icon at the bottom opens a pop-up with contact details (Email and Instagram). Helps with form corrections or event questions.
- **Countdown Timer**: A live countdown timer on the form shows exactly how much time remains until the RSVP deadline.
- **Time-Limited Form Access**: The form's submission button is hidden once the deadline passes. This helps enforce a strict RSVP window.
- **Pre-Form Loading Page**: A splash screen with a timer delays access to the form page until a preset unlock time is reached.
- **Real-Time Validation**: User inputs are validated as they type to reduce errors during submission.

--------------------------------------------------------------------------------

Security & Expiry

- **QR Code Expiry**: QR links are embedded with an expiration date (the event date). After that, the code becomes invalid, preventing misuse.
- **QR Code Information Lock**: When QR code is scanned it is directed to a secure page requesting PIN in order to view details about the specific ticket.

--------------------------------------------------------------------------------

Admin Dashboard

- **Live RSVP Table**: An admin-only page displays all current RSVP entries in a formatted table, including:
  - Full name
  - Email
  - Hofstra ID
  - Guest names (or "N/A")
  - Time of submission (automatically converted to est time)

- **Export to CSV**: Admins can export all RSVP data with a single click. The CSV file is named using the current date for clarity.
- **Clear Entries**: A button on the admin dashboard allows clearing all stored submissions if needed for a fresh restart or testing.

--------------------------------------------------------------------------------

Technologies Used

- **Frontend**: HTML, TailwindCSS, vanilla JS
- **Storage**: LocalStorage (for frontend);

--------------------------------------------------------------------------------

## Project Structure

📂 psa-rsvp
├── 📂 Images/ # Icons and graphics (🇵🇰 flag, email, etc.)  
├── 📄 admin.html # Admin dashboard for viewing/exporting submissions  
├── 📄 home.html # Main RSVP form  
├── 📄 index.html # “Coming soon” page with countdown to form opening  
├── 📄 success.html # Confirmation page showing QR code and download option  
├── 📄 ticket.html # Displays ticket information after QR scan and secure PIN entry  
├── 📄 test.html # Extra page for experimenting with UI/code  
├── 📄 README.md # Project overview (what you're reading right now)  
└── 📄 notes.txt # Development notes  

Future Features (Roadmap)

- [ ] Switch to Realtime Database for secure cloud-based storage  
- [ ] Email QR codes directly to users instead of displaying on the page to increase security
- [ ] Admin approval system for each submission before email is sent to validate rsvps
- [ ] Email calendar invite (.ics file) with confirmation so users will be reminded about event date and time.