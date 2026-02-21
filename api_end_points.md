# API Endpoints Documentation

All API endpoints are prefixed with `/api/v1/`.

## 1. Authentication & Accounts (`/auth/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login/` | Login with email and password. Returns JWT access and refresh tokens + user profile. |
| POST | `/auth/otp/request/` | Request an OTP to be sent to an email. |
| POST | `/auth/otp/verify/` | Verify OTP and return authentication tokens. |
| GET | `/auth/users/` | List all users (Super Admin only). |
| POST | `/auth/users/` | Create a new user (Super Admin only). |
| GET | `/auth/users/{id}/` | Retrieve user details. |
| PUT | `/auth/users/{id}/` | Update user details. |
| PATCH | `/auth/users/{id}/` | Partially update user details. |
| DELETE| `/auth/users/{id}/` | Delete a user. |

## 2. Branches (`/branches/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/branches/` | List all branches. |
| POST | `/branches/` | Create a new branch. |
| GET | `/branches/{id}/` | Retrieve branch details. |
| PUT | `/branches/{id}/` | Update branch details. |
| PATCH | `/branches/{id}/` | Partially update branch details. |
| DELETE| `/branches/{id}/` | Delete a branch. |

## 3. Devices (`/devices/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/devices/` | List all devices. |
| POST | `/devices/` | Register a new device (Admin). Generates a registration token. |
| POST | `/devices/claim-registration/` | Device claiming endpoint. Returns device_id and secret_key using registration token. |
| GET | `/devices/{id}/` | Retrieve device details. |

| PUT | `/devices/{id}/` | Update device details. |
| PATCH | `/devices/{id}/` | Partially update device details. |
| DELETE| `/devices/{id}/` | Delete a device. |

## 4. Call Logs (`/calllogs/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/calllogs/` | List all call logs. |
| POST | `/calllogs/` | Manually record a call log. |
| POST | `/calllogs/sync/` | Synchronize call logs from a device. |
| GET | `/calllogs/{id}/` | Retrieve call log details. |
| DELETE| `/calllogs/{id}/` | Delete a call log record. |

## 5. Analytics (`/analytics/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/overview/` | General analytics summary. |
| GET | `/analytics/peak-hours/` | Analysis of peak call volume hours. |

## 6. Exports (`/exports/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/exports/` | List all generated export files. |
| POST | `/exports/generate/` | Initiate a new data export (CSV/Excel). |
| GET | `/exports/{id}/download/` | Download a specific export file. |
| DELETE| `/exports/{id}/` | Remove an export record and file. |

## 7. Monitoring (`/monitoring/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/monitoring/status/` | Current health status summary of all devices. |
| POST | `/monitoring/heartbeat/` | Device heartbeat endpoint to maintain "Online" status. |
| GET | `/monitoring/device-events/` | List system events (offline, battery low, etc.). |
| GET | `/monitoring/device-events/{id}/` | Retrieve specific event details. |

## 8. Dashboard (`/dashboard/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/stats/` | Aggregated statistics for the main dashboard view. |
