# 🤝 Pledgos — The Commitment Protocol

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Razorpay](https://img.shields.io/badge/Razorpay-02042B?style=for-the-badge&logo=razorpay&logoColor=white)](https://razorpay.com/)

**Pledgos** is a decentralized-inspired commitment protocol built to solve the trust gap in client-freelancer agreements. It allows clients to secure freelancers by staking funds in a secure escrow layer. 

If the freelancer successfully completes and delivers the work, the funds are released. If they fail to deliver, the money is refunded to the client—but rather than a simple binary outcome, refunds are calculated using a **mathematical, time-based decay curve**, ensuring fairness for both parties based on time elapsed and milestones breached.

---

## ⚙️ How the Protocol Works

The system operates on a highly strict state machine to guarantee that no funds are lost or misplaced:

1. **Draft:** The commitment is created and agreed upon.
2. **Funded/Paid:** The client stakes the required funds into the Pledgos escrow layer.
3. **Locked:** The freelancer locks the commitment, signaling that work has begun and terms are accepted.
4. **Delivered:** The freelancer submits evidence of work (e.g., GitHub PRs, live links, screenshots).
5. **Settled:** Funds are formally released from escrow to the freelancer's payout account.

If a deadline passes without delivery, the **Decay Curve** automatically kicks in, depreciating the freelancer's potential payout over time and refunding the remainder back to the client.

## ✨ Core Features

- **Double-Entry Financial Ledger:** Pledgos doesn't just do basic CRUD operations. It utilizes an append-only, double-entry ledger to guarantee absolute auditability of every payment, hold, payout, and refund.
- **Idempotent Webhook Processing:** Robust payment processing via Razorpay webhooks, designed to safely process duplicate or out-of-order financial events securely.
- **Role-Based Access Control:** Distinct, isolated dashboard experiences for Clients, Freelancers, and Administrators, enforced by Next.js App Router and backend JWT validation.
- **Evidence Validation:** Robust system for delivering "artifacts" (links/images) to prove task completion.

## 🛠️ Technology Stack

**Backend**
- **Framework:** FastAPI (Python)
- **Database:** Neon PostgreSQL (Serverless) + SQLAlchemy ORM
- **Auth:** JWT (Access & Refresh Tokens) + Argon2id Password Hashing
- **Migrations:** Alembic

**Frontend**
- **Framework:** Next.js (React)
- **Styling:** Tailwind CSS

**Infrastructure & Payments**
- **Payment Gateway:** Razorpay (Orders, Webhooks, Payouts)

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [Neon](https://neon.tech/) PostgreSQL Database (or local Postgres)
- [Razorpay](https://razorpay.com/) API Keys

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/pledgos.git
cd pledgos
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment Variables
# Create a .env file in the root directory:
DATABASE_URL=postgresql://user:pass@ep-rest-of-url.neon.tech/neondb
JWT_SECRET_KEY=your_super_secret_key
JWT_REFRESH_SECRET_KEY=your_other_super_secret_key
RAZORPAY_KEY_ID=rzp_test_xxxxxx
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Run Migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --reload
```

### 3. Frontend Setup
```bash
cd commitment-web

# Install dependencies
npm install

# Configure Next.js Environment
# Create a .env.local file:
NEXT_PUBLIC_API_URL=http://localhost:8000

# Run Development Server
npm run dev
```

## 🗺️ Roadmap & Future Improvements

- **Asynchronous Task Queue:** Migrate timeline-based operations (like decay triggering and webhook processing) from basic scheduling to a robust broker like **Celery + Redis**.
- **AI Automated Evidence Validation:** Integrate LLM-powered checks to briefly validate submitted GitHub PRs or image artifacts before permitting funds to unlock.
- **WebSocket Integration:** Transition from HTTP polling to WebSockets for instant UI updates when funds are locked or delivered.

---
*Built with precision and a focus on financial safety.*
