# CallLog System - Complete Project Summary

## 📱 Project Overview

A sophisticated **multi-branch, multi-device call logging system** designed for spa/salon businesses. It captures incoming, outgoing, and missed calls from Android devices installed at branch locations and provides real-time analytics, reporting, and management dashboards through a web interface.

---

## 🏗️ System Architecture

### Technology Stack
- **Backend**: Django 5.2.11 + Django REST Framework + PostgreSQL
- **Frontend**: Vue 3 + Vite + Tailwind CSS + Redux (State Management)
- **Mobile**: Android (Custom native app with Kotlin)
- **Authentication**: SimpleJWT (JSON Web Tokens)
- **Task Queue**: Celery for async operations
- **Infrastructure**: Docker, Nginx, Terraform (in `/infrastructure/`)

---

## 📊 Core Data Models

### 1. Branches Model (`apps/branches/`)
Represents physical spa/salon locations:
- **Fields**: spa_name, code (unique identifier), location details (state/city/area/postal_code), address, is_active
- **Purpose**: Parent container for devices and call logs
- **Inheritance**: BaseModel (UUIDs), TimeStampedModel (created_at/updated_at), SoftDeleteModel (safe deletion)

**Location migration note**: `state`, `city`, and `area` are legacy text fields
on the branch model and must remain in place during the normalized locations
migration. The safe migration plan is documented in
`LOCATIONS_APP_SAFE_PHASED_MIGRATION_PLAN.md`. New normalized branch mappings
should use nullable FK fields such as `location_state`, `location_city`,
`location_group`, and `location_area` so old text data is not deleted, renamed,
or overwritten until the audit passes and a separate final removal task is
approved.

### 2. Devices Model (`apps/devices/`)
Represents Android smartphone units assigned to branches:
- **Key Fields**: 
  - `device_id` (unique hardware identifier)
  - `secret_key` (auto-generated 64-char hex, acts as API key)
  - `sim_1_number` & `sim_2_number` (phone number tracking)
  - `last_sync` & `last_heartbeat` (health monitoring)
  - `branch` (ForeignKey with cascade delete)
- **Purpose**: Authentication bridge between Android devices and backend
- **Inheritance**: BaseModel, TimeStampedModel, SoftDeleteModel

### 3. Call Logs Model (`apps/calllogs/`)
**Write-heavy, analytics-optimized** table storing individual call records:
- **Key Fields**: 
  - `branch` & `device` (ForeignKeys)
  - `phone_number` (caller ID)
  - `call_type` (incoming/outgoing/missed/rejected)
  - `duration` (seconds)
  - `sim_slot` (1 or 2)
  - `call_time` (exact timestamp)
  - `call_hash` (64-char unique idempotency key preventing duplicates)
- **Indexing Strategy**:
  ```
  - Compound index: [branch, call_time]
  - Individual indexes: call_time, branch, device, phone_number
  ```
- **Purpose**: Transactional store for call data with high read performance for analytics

### 4. Supporting Models
- **Accounts** (`apps/accounts/`): Users with roles (Super Admin, Branch Admin, Staff)
- **Monitoring** (`apps/monitoring/`): Device health metrics (battery, signal, app version, storage)
- **Analytics** (`apps/analytics/`): Aggregated call statistics and trends
- **Exports** (`apps/exports/`): Report generation with S3 integration
- **Dashboard** (`apps/dashboard/`): Summary views and KPIs
- **Common** (`apps/common/`): Shared utilities, filters, permissions, pagination, responses

---

## 🔌 REST API Architecture

**Base URL**: `https://apibackend.mastercall.in/api/v1/`

### 1. Authentication & Accounts (`/auth/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login/` | Email + password → JWT tokens (access + refresh) + user profile |
| POST | `/auth/otp/request/` | Request OTP to email |
| POST | `/auth/otp/verify/` | Verify OTP and authenticate |
| GET/POST | `/auth/users/` | List/create users (Super Admin only) |
| GET/PUT/PATCH/DELETE | `/auth/users/{id}/` | User CRUD operations |

### 2. Branches (`/branches/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/branches/` | List/create branches |
| GET/PUT/PATCH/DELETE | `/branches/{id}/` | Branch CRUD operations |

**Example Branch Creation**:
```json
{
  "spa_name": "Elegance Spa Center",
  "code": "ESC001",
  "state": "Maharashtra",
  "city": "Mumbai",
  "area": "Andheri West",
  "postal_code": 400053,
  "address": "101, Crystal Plaza, New Link Road",
  "is_active": true
}
```

### 3. Devices (`/devices/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/devices/` | List/register devices (Admin creates record) |
| POST | `/devices/claim-registration/` | Device claiming (returns device_id + secret_key) |
| GET/PUT/PATCH/DELETE | `/devices/{id}/` | Device CRUD operations |

**Device Registration Flow**:
1. Admin creates device via web dashboard
2. System auto-generates secret_key
3. Device claims registration with token
4. Receives device_id + secret_key for future API calls

**Claim Request**:
```json
{
  "token": "ABC123PX"
}
```

**Claim Response**:
```json
{
  "status": "success",
  "device_id": "SPA-AB12-CD34",
  "secret_key": "7f8a9b0c...ad",
  "branch_name": "Elegance Spa Center"
}
```

### 4. Call Logs (`/calllogs/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/calllogs/` | List all call logs with filtering |
| POST | `/calllogs/` | Manually record a call |
| POST | `/calllogs/sync/` | **Bulk sync from Android devices** |
| GET | `/calllogs/{id}/` | Retrieve call details |
| DELETE | `/calllogs/{id}/` | Delete call record |

**Bulk Sync Request** (Android → Backend):
```json
[
  {
    "phone_number": "+919876543210",
    "call_type": "incoming",
    "duration": 120,
    "sim_slot": 1,
    "call_time": "2024-02-22T10:30:00Z",
    "call_hash": "unique_hash_string_1"
  },
  {
    "phone_number": "+919876543211",
    "call_type": "missed",
    "duration": 0,
    "sim_slot": 2,
    "call_time": "2024-02-22T10:35:00Z",
    "call_hash": "unique_hash_string_2"
  }
]
```

**Sync Response**:
```json
{
  "status": "success",
  "synced_count": 2
}
```

### 5. Analytics (`/analytics/`)
- Call trends and volume analysis
- Branch-wise statistics
- Time-based distribution
- Custom date range filtering

### 6. Exports (`/exports/`)
- Generate reports (PDF, Excel)
- S3 integration for storage
- Scheduled exports via Celery

### 7. Monitoring (`/monitoring/`)
- **Heartbeat**: Device health check (every 15 minutes)
- Battery level, signal strength, app version, storage metrics
- Device blocking logic (is_blocked flag)

**Heartbeat Request**:
```json
{
  "battery_level": 85,
  "signal_strength": -75,
  "app_version": "1.0.4",
  "storage_used_mb": 450.5
}
```

---

## 📱 Android-to-Backend Integration

### Authentication Headers
All operational endpoints (except claim) require:
```
X-Device-Id: {device_id_string}
X-Device-Secret: {secret_key_string}
```

### Phase 1: Initial Registration
1. Admin creates **Branch** in web dashboard
2. Admin creates **Device**, specifying branch and phone's hardware `device_id`
3. Django generates 64-character `secret_key`
4. Admin installs Android app and inputs device_id + secret_key (via QR or manual)

### Phase 2: Heartbeat & Health Monitoring
1. Android app pings `/monitoring/heartbeat/` every 15 minutes (WorkManager)
2. Includes battery, signal, app version, storage metrics
3. Backend updates `last_heartbeat` timestamp on Device model
4. If device is `is_blocked=True`, backend rejects ping and forces app halt

**Real-time Status Strategy**:
- **Periodic Sync**: `PeriodicWorkRequest` (minimum 15 minutes)
- **Instant Update**: `ConnectivityManager.NetworkCallback` for connection changes
- **Foreground Trigger**: Immediate heartbeat when app opens

### Phase 3: Call Log Sync (Core Data Flow)
1. Android app reads native dialer via `READ_CALL_LOG` permission
2. For each call, generates `call_hash` (idempotency key combining phone + time + duration)
3. POSTs JSON array to `POST /calllogs/sync/` with auth headers
4. Backend validates `X-Device-Id` + `X-Device-Secret`
5. Looks up Device → Looks up Branch (parent of device)
6. Automatically attaches `branch` + `device` ForeignKeys to each CallLog
7. **Duplicate Detection**: If `call_hash` already exists, safely skips (no errors)
8. Updates `last_sync` timestamp on Device model

**Idempotency Guarantee**: Android can retry sync 10x → backend ignores duplicates via unique call_hash constraint

---

## 🎨 Frontend Architecture

### Directory Structure (`frontend/src/`)
```
app/                → Core config & global providers (providers.jsx, config.js)
assets/             → Images, icons, global CSS
layouts/            → Page shells
  ├─ DashboardLayout.jsx    → Main app with Navbar + Sidebar
  └─ AuthLayout.jsx         → Login/Register pages
modules/            → Feature-based modular architecture
  ├─ {feature}/
  │   ├─ api.js            → Axios endpoints for feature
  │   ├─ components/       → Feature-specific UI components
  │   └─ pages/            → Full-page components (rendered by router)
shared/             → Reusable across features
  ├─ components/           → Generic UI (Button, Table, Modal, etc.)
  ├─ hooks/                → Custom React hooks (useAuth, useLocalStorage)
  ├─ services/             → Global services (axiosInstance)
  └─ utils/                → Helper functions (formatting, validation)
store/              → Redux global state
  ├─ index.js              → Store configuration
  └─ slices/               → Redux Toolkit slices (Auth, Branch, Device)
```

### Key Implementation Patterns

#### 1. Axios Integration (`shared/services/axiosInstance.js`)
- **Base URL**: Uses `VITE_API_BASE_URL` from environment
- **Request Interceptors**: Auto-attaches JWT `Bearer` token to all requests
- **Response Interceptors**: On 401 (Unauthorized), silently refreshes token via SimpleJWT routes before retrying

#### 2. Redux State Management
- **Auth Slice**: User session, permissions (SuperAdmin vs Admin), profile
- **Resource Slices**: Branch, Device (caches lookup data to reduce API calls)

#### 3. Custom Hooks
- **`useAuth()`**: Login/logout logic, permission checks (`isSuperAdmin`)
- Standard **`useEffect` + `useState`**: Data fetching, UI state management

#### 4. Filter Engine (CallLogList.jsx, AnalyticsDashboard.jsx)
- Local `filters` state
- `useEffect` triggers API call on filter changes
- Consolidated API logic in module-specific `api.js`

#### 5. Shared Table Component
- Highly generic, accepts custom render functions
- Built-in checkbox selection + "Select All" (for bulk delete)
- Supports sorting, pagination

#### 6. Responsive Design
- **Tailwind CSS** with mobile-first approach
- Grid layouts optimized for mobile and desktop
- Unified color palette (Sky Blue primary, Red for alerts)

### Features
- **Login/OTP Authentication**
- **Branch Management**: Create, list, edit, delete
- **Device Management**: Register, track status, block/unblock
- **Call Log Dashboard**: Filter by date/branch/call-type, bulk delete
- **Analytics**: Trends, volume charts, time distribution
- **Reports/Exports**: Generate and download PDFs/Excel

---

## 🔐 Security, Quality & Best Practices

### Multi-Tenancy & Data Isolation
- Users scoped to branches (Super Admin sees all, Branch Admin sees only theirs)
- Devices tied to single branch
- ForeignKey cascade deletion with SoftDelete protection

### Idempotency & Duplicate Prevention
- `call_hash` unique constraint prevents duplicate uploads
- Android retries automatically handled safely

### Authentication & Authorization
- JWT tokens with refresh mechanism
- Role-based access control (super_admin, branch_admin, staff)
- Device-level auth via `secret_key` + `device_id` headers

### Data Integrity
- Heavy indexing on CallLog for fast analytics queries
- Soft delete for non-destructive operations
- Automatic timestamp tracking (created_at, updated_at)

### Response Codes
| Status | Meaning | Action |
|--------|---------|--------|
| 200/201 | Success | Continue |
| 401 | Unauthorized | Check headers or device may be blocked |
| 400 | Bad Request | Check JSON format |
| 404 | Not Found | Invalid token during claim |
| 500 | Server Error | Contact admin |

---

## 📈 Scalability & Enterprise Enhancements

### Current Capabilities
- Millions of call records (write-heavy)
- Multiple branches, devices, users
- Real-time sync and monitoring

### Future Enterprise Escalation
- **PostgreSQL Monthly Partitioning**: Partition CallLog by `call_time` for optimal B-Tree performance
- **HMAC Request Signing**: Replace raw secret_key with HMAC(payload + timestamp) for MITM protection
- **Rate Limiting**: Implement Django Ratelimit or NGINX on `/calllogs/` endpoint
- **Device Anomaly Detection**: Flag unusual logging frequencies vs. branch operating hours
- **Encrypted Local Storage**: Android SQLite encryption for physical device compromise protection

---

## 📂 Project Configuration

### Settings (`config/settings/`)
- Environment-based configuration (dev, staging, prod)
- `.env` file for secrets (SECRET_KEY, DB credentials, API URLs)
- CORS enabled for cross-origin requests

### Deployment
- **Docker**: Containerized backend + frontend
- **Nginx**: Reverse proxy, static file serving
- **Terraform**: Infrastructure-as-code for AWS/cloud deployment

### Task Queue
- **Celery**: Async tasks (exports, scheduled reports, data cleanup)
- Broker configuration in `config/celery.py`

### Installed Apps
```
Django Admin & Auth
CORS Headers
Django REST Framework + SimpleJWT
Local Apps:
  - core (base models, auth, utils)
  - accounts (user management)
  - branches (spa locations)
  - devices (android phones)
  - calllogs (call records)
  - monitoring (device health)
  - analytics (statistics)
  - exports (reports)
  - dashboard (summary views)
```

---

## 🚀 Key Features Summary

✅ **Real-time call tracking** from Android devices  
✅ **Multi-branch, multi-device management**  
✅ **Comprehensive analytics & reporting**  
✅ **Role-based access control** (Super Admin, Branch Admin, Staff)  
✅ **Device health monitoring** (battery, signal, app version, storage)  
✅ **Secure API** with JWT + device secret key authentication  
✅ **Idempotent sync** preventing duplicate call entries  
✅ **Responsive web dashboard** (mobile + desktop optimized)  
✅ **Export capabilities** (PDF, Excel, S3 integration)  
✅ **Soft-delete safety** for non-destructive data management  
✅ **Celery async tasks** for background processing  
✅ **Docker containerization** for scalable deployment  

---

## 📋 Development Environment

### Prerequisites
- Python 3.10+
- Node.js 16+ (Frontend)
- PostgreSQL 12+
- Redis (for Celery)

### Getting Started
1. Activate virtual environment: `source venv/bin/activate` (or Windows equivalent)
2. Install backend deps: `pip install -r requirements/base.txt`
3. Install frontend deps: `cd frontend && npm install`
4. Configure `.env` file with database and API settings
5. Run migrations: `python manage.py migrate`
6. Start backend: `python manage.py runserver`
7. Start frontend: `cd frontend && npm run dev`

---

## 🎯 Summary

This is a **production-grade, scalable call management system** designed for multi-location spa/salon businesses. It seamlessly integrates Android devices for real-time call capture with a modern web dashboard for analytics, reporting, and management operations. The architecture emphasizes security, data integrity, and operational efficiency through thoughtful multi-tenancy design, idempotent sync mechanisms, and comprehensive monitoring.
