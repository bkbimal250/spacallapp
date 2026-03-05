# API Endpoints Documentation

All API endpoints are prefixed with `/api/v1/`.

## 1. Authentication & Accounts (`/auth/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `https://api.spa.branch.call.workspa.in/api/v1/auth/login/` | Login with email and password. Returns JWT access and refresh tokens + user profile. |
| POST | `https://api.spa.branch.call.workspa.in/api/v1/auth/otp/request/` | Request an OTP to be sent to an email. |
| POST | `https://api.spa.branch.call.workspa.in/api/v1/auth/otp/verify/` | Verify OTP and return authentication tokens. |
| GET | `https://api.spa.branch.call.workspa.in/api/v1/auth/users/` | List all users (Super Admin only). |
| POST | `https://api.spa.branch.call.workspa.in/api/v1/auth/users/` | Create a new user (Super Admin only). |
| GET | `https://api.spa.branch.call.workspa.in/api/v1/auth/users/{id}/` | Retrieve user details. |
| PUT | `https://api.spa.branch.call.workspa.in/api/v1/auth/users/{id}/` | Update user details. |
| PATCH | `https://api.spa.branch.call.workspa.in/api/v1/auth/users/{id}/` | Partially update user details. |
| DELETE| `https://api.spa.branch.call.workspa.in/api/v1/auth/users/{id}/` | Delete a user. |

### Examples

**Login Request:**
```json
{
  "email": "admin@example.com",
  "password": "securepassword123"
}
```

**Login Response:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "full_name": "Admin User",
    "role": "super_admin",
    "branch": null,
    "is_active": true
  }
}
```

**OTP Request:**
```json
{
  "email": "user@example.com"
}
```

**OTP Verify:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**User Creation:**
```json
{
  "email": "staff@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "branch_admin",
  "branch": "a79201f1-337b-40f4-9043-f66d43e5f206"
}
```

---

## 2. Branches (`/branches/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `https://api.spa.branch.call.workspa.in/api/v1/branches/` | List all branches. |
| POST | `https://api.spa.branch.call.workspa.in/api/v1/branches/` | Create a new branch. |
| GET | `https://api.spa.branch.call.workspa.in/api/v1/branches/{id}/` | Retrieve branch details. |
| PUT | `https://api.spa.branch.call.workspa.in/api/v1/branches/{id}/` | Update branch details. |
| PATCH | `https://api.spa.branch.call.workspa.in/api/v1/branches/{id}/` | Partially update branch details. |
| DELETE| `https://api.spa.branch.call.workspa.in/api/v1/branches/{id}/` | Delete a branch. |

### Examples

**Create Branch:**
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

**Branch List Item:**
```json
{
  "id": "a79201f1-337b-40f4-9043-f66d43e5f206",
  "spa_name": "Elegance Spa Center",
  "code": "ESC001",
  "state": "Maharashtra",
  "city": "Mumbai",
  "created_at": "2024-02-21T10:00:00Z"
}
```

---

## 3. Devices (`/devices/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `https://api.spa.branch.call.workspa.in/api/v1/devices/` | List all devices. |
| POST | `https://api.spa.branch.call.workspa.in/api/v1/devices/` | Register a new device (Admin). Generates a registration token. |
| POST | `https://api.spa.branch.call.workspa.in/api/v1/devices/claim-registration/` | Device claiming endpoint. Returns device_id and secret_key using registration token. |
| GET | `https://api.spa.branch.call.workspa.in/api/v1/devices/{id}/` | Retrieve device details. |
| PUT | `https://api.spa.branch.call.workspa.in/api/v1/devices/{id}/` | Update device details. |
| PATCH | `https://api.spa.branch.call.workspa.in/api/v1/devices/{id}/` | Partially update device details. |
| DELETE| `https://api.spa.branch.call.workspa.in/api/v1/devices/{id}/` | Delete a device. |

### Examples

**Register Device (Admin):**
```json
{
  "branch": "a79201f1-337b-40f4-9043-f66d43e5f206",
  "sim_1_number": "9876543210",
  "sim_2_number": "9876543211"
}
```

**Claim Registration (Device):**
```json
{
  "token": "ABC123PX"
}
```

**Claim Response:**
```json
{
  "status": "success",
  "device_id": "SPA-AB12-CD34",
  "secret_key": "7f8a9b0c... (64 chars)",
  "branch_name": "Elegance Spa Center"
}
```

---

## 4. Call Logs (`/calllogs/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `https://api.spa.branch.call.workspa.in/api/v1/calllogs/` | List all call logs. |
| POST | `https://api.spa.branch.call.workspa.in/api/v1/calllogs/` | Manually record a call log. |
| POST | `https://api.spa.branch.call.workspa.in/api/v1/calllogs/sync/` | Synchronize call logs from a device. |
| GET | `https://api.spa.branch.call.workspa.in/api/v1/calllogs/{id}/` | Retrieve call log details. |
| DELETE| `https://api.spa.branch.call.workspa.in/api/v1/calllogs/{id}/` | Delete a call log record. |

### Examples

**Sync Call Logs:**
```json
[
  {
    "phone_number": "+919988776655",
    "call_type": "incoming",
    "duration": 45,
    "sim_slot": 1,
    "call_time": "2024-02-22T14:30:00Z",
    "call_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  {
    "phone_number": "+918877665544",
    "call_type": "missed",
    "duration": 0,
    "sim_slot": 2,
    "call_time": "2024-02-22T14:35:00Z",
    "call_hash": "5d41402abc4b2a76b9719d911017c592"
  }
]
```

**Sync Response:**
```json
{
  "status": "success",
  "synced_count": 2
}
```

---

## 5. Analytics (`/analytics/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `https://api.spa.branch.call.workspa.in/api/v1/analytics/overview/` | General analytics summary. |
| GET | `https://api.spa.branch.call.workspa.in/api/v1/analytics/peak-hours/` | Analysis of peak call volume hours. |

### Examples

**Overview Response:**
```json
{
  "conversion_rates": [
    {"name": "Incoming", "value": 124},
    {"name": "Outgoing", "value": 89},
    {"name": "Missed", "value": 45},
    {"name": "Rejected", "value": 12}
  ]
}
```

**Peak Hours Response:**
```json
[
  {"hour": "10AM", "calls": 24},
  {"hour": "11AM", "calls": 45},
  {"hour": "12PM", "calls": 38}
]
```

---

## 6. Exports (`/exports/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `https://api.spa.branch.call.workspa.in/api/v1/exports/` | List all generated export files. |
| POST | `https://api.spa.branch.call.workspa.in/api/v1/exports/generate/` | Initiate a new data export (CSV/Excel). |
| GET | `https://api.spa.branch.call.workspa.in/api/v1/exports/{id}/download/` | Download a specific export file. |
| DELETE| `https://api.spa.branch.call.workspa.in/api/v1/exports/{id}/` | Remove an export record and file. |

### Examples

**Generate Export:**
```json
{
  "type": "call_logs"
}
```

**Export Job Status:**
```json
{
  "id": "e4e2c880-...",
  "status": "completed",
  "export_type": "call_logs",
  "file_url": "https://s3.amazonaws.com/exports/call_logs_20240222.csv",
  "created_at": "2024-02-22T10:00:00Z"
}
```

---

## 7. Monitoring (`/monitoring/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `https://api.spa.branch.call.workspa.in/api/v1/monitoring/status/` | Current health status summary of all devices. |
| POST | `https://api.spa.branch.call.workspa.in/api/v1/monitoring/heartbeat/` | Device heartbeat endpoint to maintain "Online" status. |
| GET | `https://api.spa.branch.call.workspa.in/api/v1/monitoring/device-events/` | List system events (offline, battery low, etc.). |
| GET | `https://api.spa.branch.call.workspa.in/api/v1/monitoring/device-events/{id}/` | Retrieve specific event details. |

### Examples

**Monitoring Status Response:**
```json
{
  "total_devices": 25,
  "active_devices": 22,
  "offline_alerts": 3,
  "sim_change_alerts": 1
}
```

**Heartbeat Response:**
```json
{
  "status": "heartbeat acknowledged"
}
```

---

## 8. Dashboard (`/dashboard/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `https://api.spa.branch.call.workspa.in/api/v1/dashboard/stats/` | Aggregated statistics for the main dashboard view. |

### Examples

**Dashboard Stats Response:**
```json
{
  "total_calls": 1250,
  "active_devices": 22,
  "missed_calls": 85,
  "avg_duration": "3m 12s",
  "call_volume_trends": [
    {"name": "Mon", "calls": 150},
    {"name": "Tue", "calls": 230}
  ],
  "branch_performance": [
    {
      "name": "Elegance Spa Mumbai",
      "calls": 450,
      "conversion": 85,
      "status": "Active"
    }
  ]
  ]
}
```

---

## 9. Lead Management (`/leadmanagement/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `https://api.spa.branch.call.workspa.in/api/v1/leadmanagement/` | List all leads. Branch Managers only see leads for their assigned branch. |
| POST | `https://api.spa.branch.call.workspa.in/api/v1/leadmanagement/` | Create a new lead. Supply a `calllog` ID to automatically attach contact information. |
| GET | `https://api.spa.branch.call.workspa.in/api/v1/leadmanagement/{id}/` | Retrieve lead details. |
| PUT | `https://api.spa.branch.call.workspa.in/api/v1/leadmanagement/{id}/` | Fully update lead details (e.g., status, remarks, booking date). |
| PATCH | `https://api.spa.branch.call.workspa.in/api/v1/leadmanagement/{id}/` | Partially update a lead (e.g., updating just the status). |
| DELETE| `https://api.spa.branch.call.workspa.in/api/v1/leadmanagement/{id}/` | Delete a lead. |

### Examples

**Create Lead from Call Log:**
```json
{
  "status": "interested",
  "calllog": 105,
  "remarks": "Customer wants to visit tomorrow."
}
```

**Partial Update (Status Change):**
```json
{
  "status": "coming",
  "booking_date": "2024-02-25"
}
```

**Lead Response:**
```json
{
  "id": "c1f1f2e3-...",
  "status": "interested",
  "phone_number": "+919876543210",
  "booking_date": null,
  "remarks": "Customer wants to visit tomorrow.",
  "branch": "a79201f1-...",
  "branch_name": "Elegance Spa Center",
  "calllog": 105,
  "contact": 12,
  "contact_name": "Bimal Vishwakarma",
  "created_by_name": "Branch Manager 1",
  "created_at": "2024-02-22T10:00:00Z"
}
```
