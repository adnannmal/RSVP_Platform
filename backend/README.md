# PSA RSVP Backend

FastAPI + MongoDB backend for the Hofstra PSA RSVP Platform.

## Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Health check |
| POST | `/submit` | Submit a new RSVP |
| GET | `/ticket/{id}` | Fetch ticket data (QR scan) |
| POST | `/verify-pin` | Verify admin PIN |
| GET | `/rsvps` | List all RSVPs (admin) |
| DELETE | `/rsvps` | Clear all RSVPs (admin) |
| GET | `/export.csv` | Download CSV of all RSVPs |

## Local Setup

```bash
# 1. Clone and enter the folder
cd rsvp_backend

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI and PIN

# 5. Run the server
uvicorn main:app --reload
```

The API will be live at http://localhost:8000.
Interactive docs: http://localhost:8000/docs

## Deploy to Render

1. Push this folder to a GitHub repo (can be the same RSVP_Platform repo in a `/backend` subfolder).
2. On [render.com](https://render.com), create a new **Web Service**.
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `MONGO_URI` — your MongoDB Atlas connection string
   - `ADMIN_PIN` — your 6-digit PIN

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `ADMIN_PIN` | 6-digit PIN for ticket & admin access | `123456` |

## Notes

- Duplicate submissions are blocked by email address.
- QR codes expire on the date stored in `qrExpire`.
- The PIN is shared across all tickets (same as the original design).
- All timestamps are stored in EST.
