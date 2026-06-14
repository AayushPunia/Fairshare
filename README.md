# FairShare — Shared Expenses App

A full-stack web application for splitting shared flat expenses among flatmates. Built with **Django REST Framework** (backend) and **React + Vite** (frontend).

## 🎯 Purpose

Built for a group of 6 flatmates (Aisha, Rohan, Priya, Meera, Dev, Sam) who need to:
- Track shared expenses with multiple split types (equal, unequal, percentage, shares)
- Import bulk expenses from CSV with intelligent anomaly detection
- Calculate who owes whom with full expense drill-down
- Settle debts with minimum-transaction optimization

## 🏗️ Architecture

```
┌─────────────┐     REST API      ┌──────────────┐     ORM      ┌───────────┐
│   React +   │  ◄──────────────► │   Django +   │ ◄──────────► │  SQLite/  │
│    Vite     │   JSON / Token    │     DRF      │              │ PostgreSQL│
└─────────────┘                   └──────────────┘              └───────────┘
   Port 5173                         Port 8000
```

### Backend (Django)
| App        | Purpose                                           |
|------------|---------------------------------------------------|
| `accounts` | Custom User model, auth (register/login/logout)   |
| `groups`   | Group + GroupMember with join/leave dates           |
| `expenses` | Expense + ExpenseSplit + Settlement + balance calc  |
| `importer` | CSV import: parse → analyze → review → commit      |

### Frontend (React)
| Component       | Purpose                                      |
|-----------------|----------------------------------------------|
| `Login`         | Auth with quick-login buttons for demo       |
| `Dashboard`     | Group overview                               |
| `GroupDetail`    | Members + expenses + balances + settlements  |
| `ImportUpload`   | Drag-and-drop CSV upload                     |
| `ImportReview`   | Anomaly cards with approve/skip controls     |
| `ImportReport`   | Full import audit log                        |
| `ExpenseDetail`  | Split breakdown with drill-down              |

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend
```bash
cd backend
python -m venv ../venv
source ../venv/bin/activate   # Windows: ..\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python seed_demo.py           # Seed users + demo group
python manage.py runserver 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                   # Starts on http://localhost:5173
```

### Login Credentials
All users have `password = username`:
- **aisha** / aisha — Group creator
- **rohan** / rohan
- **priya** / priya
- **meera** / meera — Left group March 31
- **dev** / dev — Guest (Goa trip)
- **sam** / sam — Joined April 8

## 📊 CSV Import Engine

The import engine processes `Expenses Export.csv` through a 3-phase pipeline:

### Phase 1: Parse & Normalize (`parser.py`)
- Strip commas from amounts ("1,200" → 1200)
- Normalize names to title-case
- Parse dates flexibly (DD-MM-YYYY, Mon-DD)
- Default missing currency to INR

### Phase 2: Analyze & Detect (`analyzer.py`)
- **Duplicates**: Fuzzy matching on date + amount + payer + description
- **Settlements**: Keywords like "paid back", "deposit share"
- **Percentage errors**: Sums ≠ 100%
- **Membership issues**: Departed/not-yet-joined members
- **Split conflicts**: split_type vs split_details mismatch

### Phase 3: Review & Commit (`importer.py`)
- User reviews all detected anomalies (Meera's requirement)
- Approve, modify, or skip each anomaly
- Clean data committed to database as Expense/Settlement records

## 💰 Balance Calculation

```
For each expense:
  1. Convert to INR using stored exchange_rate
  2. Calculate each participant's share based on split_type
  3. Payer credited full amount
  4. Each participant debited their share
  5. Skip if user wasn't active member on expense date

Net balance = total_credits - total_debits
  Positive → others owe this person
  Negative → this person owes others
```

### Settlement Optimizer
Uses a greedy min-transactions algorithm:
1. Separate members into creditors (+) and debtors (-)
2. Match largest debtor ↔ largest creditor
3. Settle minimum of |debt| and credit
4. Repeat until all balances are zero

## 🤖 AI Integration (Gemini)

Uses Google Gemini API (optional, graceful degradation):
- **Anomaly descriptions**: AI-enhanced explanations of data issues
- **Expense categorization**: Auto-categorize by description keywords + AI fallback
- **Design principle**: AI enhances but never blocks functionality

Set `GEMINI_API_KEY` environment variable to enable.

## 🛠️ Tech Stack

| Layer     | Technology                    |
|-----------|-------------------------------|
| Backend   | Python, Django 5, DRF         |
| Frontend  | React 19, Vite, Vanilla CSS   |
| Database  | SQLite (dev), PostgreSQL (prod)|
| Auth      | DRF Token Authentication       |
| AI        | Google Gemini API (optional)   |

## 📁 Project Structure

```
expense app/
├── backend/
│   ├── accounts/        # User model + auth API
│   ├── groups/          # Group + membership management
│   ├── expenses/        # Expense CRUD + balance + settlements
│   ├── importer/        # CSV import pipeline + AI service
│   ├── config/          # Django settings + URLs
│   ├── seed_demo.py     # Demo data seeding
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/         # Axios client with auth interceptor
│   │   ├── context/     # Auth context provider
│   │   ├── components/  # Navbar
│   │   └── pages/       # All page components
│   ├── package.json
│   └── vite.config.js
└── Expenses Export.csv  # Sample CSV with intentional anomalies
```
