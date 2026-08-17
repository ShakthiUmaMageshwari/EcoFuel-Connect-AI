# 🌿 EcoFuel Connect AI

> **India's AI-powered sustainable fuel marketplace** — connecting local bio-fuel producers with consumers to reduce crude oil dependence and CO₂ emissions.

---

## 📖 Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Project Architecture](#project-architecture)
5. [Database Models](#database-models)
6. [API Reference](#api-reference)
7. [Frontend Pages](#frontend-pages)
8. [User Roles](#user-roles)
9. [How to Run (Local Development)](#how-to-run-local-development)
10. [Default Demo Credentials](#default-demo-credentials)
11. [Folder Structure](#folder-structure)

---

## Project Overview

EcoFuel Connect AI is a full-stack web marketplace for alternative, sustainable fuels produced locally from organic and agricultural waste. It serves **three types of users**:

- **Buyers** — search, browse, and order sustainable fuels (Biogas, Bio-CNG, Biofuel, Biomass).
- **Sellers** — list and manage fuel products, track orders and revenue.
- **Admins** — verify sellers, manage the platform, and view system analytics.

The platform uses a lightweight **AI/ML engine** (scikit-learn) to:
- Recommend the most cost-effective and environmentally relevant fuel for each buyer.
- Predict demand patterns and rank products dynamically.
- Generate real-time savings insights compared to petrol/LPG.

---

## Features

| Feature | Description |
|---|---|
| 🔍 **Fuel Discovery** | Browse and filter Biogas, Bio-CNG, Biofuel, and Biomass listings |
| 🤖 **AI Recommendations** | Personalized fuel suggestions based on use-case, city, and budget |
| 📦 **Order Management** | Place, track, and manage orders with delivery/pickup options |
| 🏪 **Seller Dashboard** | Add/edit products, view sales, manage incoming orders |
| 🛠️ **Admin Panel** | Verify sellers, view all users, manage platform content |
| 📊 **Analytics Page** | Market trends, demand forecasting, savings metrics across India |
| 🔐 **JWT Authentication** | Secure login/signup with role-based access (buyer, seller, admin) |
| 💡 **Savings Calculator** | Real-time comparison of eco-fuel cost vs. petrol/LPG per unit |
| 📱 **Responsive Design** | Mobile-first UI that adapts to all screen sizes |

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.10+** | Server-side language |
| **Flask 3.0** | Web framework & API server |
| **Flask-SQLAlchemy** | ORM for database management |
| **SQLite** | Lightweight embedded database (file: `ecofuel.db`) |
| **Flask-JWT-Extended** | JWT-based authentication & authorization |
| **Flask-CORS** | Cross-Origin Resource Sharing for the frontend |
| **scikit-learn** | ML engine for product recommendations & demand ranking |
| **NumPy** | Numerical computations for the AI engine |
| **Werkzeug** | Password hashing & security utilities |

### Frontend
| Technology | Purpose |
|---|---|
| **HTML5** | Page structure & semantic markup |
| **Vanilla CSS** | Custom design system (no frameworks) |
| **JavaScript (ES6+)** | Interactive UI, API calls, state management |
| **Google Fonts** | Typography: Outfit & Inter |

---

## Project Architecture

```
EcoFuel Connect AI/
├── backend/                  ← Flask application
│   ├── app.py                ← App factory, routes registration, static file serving
│   ├── models.py             ← SQLAlchemy database models
│   ├── seed_data.py          ← Auto-generates demo users, sellers & products on first run
│   ├── requirements.txt      ← Python dependencies
│   ├── ecofuel.db            ← SQLite database (auto-created on first run)
│   └── routes/
│       ├── auth.py           ← /api/auth/* — Login, signup, logout
│       ├── products.py       ← /api/products/* — CRUD for fuel listings
│       ├── orders.py         ← /api/orders/* — Order placement & management
│       ├── analytics.py      ← /api/analytics/* — Market and platform statistics
│       ├── admin.py          ← /api/admin/* — Admin-only management endpoints
│       └── ai.py             ← /api/ai/* — AI recommendations & savings insights
│
└── frontend/                 ← Static HTML/CSS/JS (served by Flask)
    ├── index.html            ← Home page — hero, fuel categories, AI picks
    ├── explore.html          ← Browse marketplace with filters
    ├── product.html          ← Single product detail & order page
    ├── login.html            ← Login / Signup (supports all 3 roles)
    ├── user-dashboard.html   ← Buyer: my orders, profile
    ├── seller-dashboard.html ← Seller: my products, orders, analytics
    ├── admin.html            ← Admin: user list, seller verification
    ├── analytics.html        ← Platform-wide market analytics
    ├── css/
    │   ├── base.css          ← Design tokens, reusable components, grid system
    │   └── pages.css         ← Page-specific layouts (hero, explore, auth, etc.)
    ├── js/
    │   └── api.js            ← Centralized API helper (all fetch calls to backend)
    └── images/               ← Fuel type images & logo (PNG)
```

---

## Database Models

### `User`
Stores all registered users regardless of role.
- Fields: `id`, `name`, `email`, `password_hash`, `phone`, `city`, `pincode`, `role` (`buyer`/`seller`/`admin`)

### `Seller`
Extended profile for users with `role = seller`.
- Fields: `business_name`, `address`, `description`, `verified` (boolean), `rating`, `total_sales`

### `Product`
Fuel listing created by a seller.
- Fields: `name`, `fuel_type` (`biogas`/`bio-cng`/`biofuel`/`biomass`), `price`, `unit`, `quantity_available`, `city`, `use_case` (`home`/`vehicle`/`industrial`/`agricultural`), `views`

### `Order`
A purchase placed by a buyer for a product.
- Fields: `buyer_id`, `product_id`, `quantity`, `total_price`, `status` (`pending`/`confirmed`/`delivered`/`cancelled`), `delivery_type` (`delivery`/`pickup`)

### `Review`
Rating and comment left by a buyer after purchase.
- Fields: `buyer_id`, `product_id`, `rating` (1–5), `comment`

### `SearchLog`
Records search queries for AI training and analytics.

---

## API Reference

### Authentication — `/api/auth`
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/auth/register` | Register a new user | None |
| POST | `/api/auth/login` | Login and get JWT token | None |
| GET | `/api/auth/me` | Get current user info | JWT |

### Products — `/api/products`
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/products` | List all products (with filters) | None |
| GET | `/api/products/<id>` | Get single product details | None |
| POST | `/api/products` | Create new product listing | Seller JWT |
| PUT | `/api/products/<id>` | Update a product | Seller JWT |
| DELETE | `/api/products/<id>` | Delete a product | Seller JWT |

**Filter query params:** `fuel_type`, `city`, `use_case`, `max_price`, `search`, `sort`

### Orders — `/api/orders`
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/orders` | Place a new order | Buyer JWT |
| GET | `/api/orders/my` | Get buyer's order history | Buyer JWT |
| GET | `/api/orders/seller` | Get seller's incoming orders | Seller JWT |
| PUT | `/api/orders/<id>/status` | Update order status | Seller JWT |

### AI Engine — `/api/ai`
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/ai/recommend` | Get AI-ranked fuel recommendations | None |
| GET | `/api/ai/savings/<product_id>` | Get savings vs petrol for a product | None |
| GET | `/api/ai/aggregate-savings` | Platform-wide savings summary | None |

### Analytics — `/api/analytics`
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/analytics/dashboard` | Key platform stats (users, products, sales) | None |
| GET | `/api/analytics/market` | Market breakdown by fuel type and city | None |

### Admin — `/api/admin`
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/admin/users` | List all users | Admin JWT |
| GET | `/api/admin/sellers` | List all sellers | Admin JWT |
| PUT | `/api/admin/sellers/<id>/verify` | Verify / unverify a seller | Admin JWT |

---

## Frontend Pages

| Page | File | Description |
|---|---|---|
| **Home** | `index.html` | Hero banner, fuel categories, AI recommendations, awareness section |
| **Explore** | `explore.html` | Filterable product grid with sidebar (fuel type, city, price, use-case) |
| **Product Detail** | `product.html` | Full product info, reviews, order form, savings calculator |
| **Login/Signup** | `login.html` | Tab-based login form supporting Buyer, Seller, and Admin roles |
| **User Dashboard** | `user-dashboard.html` | Buyer's order history and profile management |
| **Seller Dashboard** | `seller-dashboard.html` | Add/edit products, view sales analytics, manage orders |
| **Admin Panel** | `admin.html` | User list, seller verification controls |
| **Analytics** | `analytics.html` | Platform-wide market trends, fuel demand charts, savings data |

---

## User Roles

| Role | What they can do |
|---|---|
| **Buyer** | Browse, filter, and order fuels; view order history; leave reviews |
| **Seller** | Create and manage product listings; receive and update orders; view revenue |
| **Admin** | Verify sellers; view all users and orders; manage platform settings |

> Roles are assigned at registration and stored in the `users.role` column.

---

## How to Run (Local Development)

### Prerequisites
- **Python 3.10+** (tested on Python 3.13)
- **pip** (comes with Python)
- A terminal / PowerShell

### Step 1 — Clone / Download the project

```
git clone <your-repo-url>
cd "EcoFuel Connect AI"
```

### Step 2 — Create a Python virtual environment

```powershell
cd backend
python -m venv venv
```

### Step 3 — Activate the virtual environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.\venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Run the server

```bash
python app.py
```

You should see:
```
[*] EcoFuel Connect AI Backend running on http://localhost:5000
[OK] Database seeded with demo data
 * Running on http://127.0.0.1:5000
```

### Step 6 — Open in Browser

Navigate to: **[http://localhost:5000](http://localhost:5000)**

The Flask server serves all frontend pages automatically — no separate frontend server is needed.

---

## Default Demo Credentials

These accounts are auto-created when the database is seeded on the first run:

| Role | Email | Password |
|---|---|---|
| **Buyer** | `buyer@ecofuel.com` | `test123` |
| **Seller** | `seller@ecofuel.com` | `test123` |
| **Admin** | `admin@ecofuel.com` | `test123` |

> You can also register a new account from the Login page.

---

## Folder Structure

```
EcoFuel Connect AI/
├── README.md                 ← This file
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── seed_data.py
│   ├── requirements.txt
│   ├── ecofuel.db            ← Auto-created SQLite database
│   └── routes/
│       ├── auth.py
│       ├── products.py
│       ├── orders.py
│       ├── analytics.py
│       ├── admin.py
│       └── ai.py
└── frontend/
    ├── index.html
    ├── explore.html
    ├── product.html
    ├── login.html
    ├── user-dashboard.html
    ├── seller-dashboard.html
    ├── admin.html
    ├── analytics.html
    ├── css/
    │   ├── base.css
    │   └── pages.css
    ├── js/
    │   └── api.js
    └── images/
        ├── logo.png
        ├── biogas.png
        ├── bio-cng.png
        ├── biofuel.png
        └── biomass.png
```

---

## 📌 Notes

- The database (`ecofuel.db`) is automatically created and seeded with demo data on the **first run**. No manual database setup is needed.
- JWT tokens are stored in `localStorage` in the browser and sent as `Authorization: Bearer <token>` headers.
- The backend serves frontend static files directly — there is **no need for a separate HTTP server** for development.
- For production deployment, replace the SQLite database with PostgreSQL and use a WSGI server like Gunicorn.

---

*Made with 🌿 in India — Powering India's Sustainable Energy Future.*
