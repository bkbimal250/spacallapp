# Android API Integration Specification
## SPA Call Log System — Branch Manager App

> **Version**: 2.4  
> **Last Updated**: 2026-04-21  
> **Base URL**: `https://apibackend.mastercall.in/api/v1/`

---

## ⚠️ CRITICAL: WHO CAN USE THIS APP

This Android application is **exclusively for Branch Managers**.

| Role | Android App Access |
|---|---|
| `spa_manager` | ✅ Allowed |
| `super_admin` | ❌ Blocked |
| `admin` | ❌ Blocked |

**Android developers MUST enforce this on the client side.** After login, check the `role` field from the API response. If the role is anything other than `spa_manager`, log the user out immediately and show an access denied message.

```kotlin
// Kotlin — Role Validation After Login
val role = loginResponse.user.role
if (role != "spa_manager") {
    authManager.clearTokens()
    showError("Access denied. This app is only available for Branch Managers.")
    navigateTo(LoginScreen)
}
```

---

## ⚠️ CRITICAL: BRANCH DATA ISOLATION

Every branch manager is assigned to **one branch only**. The backend automatically scopes all data to the manager's branch. The Android app must **never** attempt to access or display data from another branch.

This isolation applies to:
- Call logs
- Leads
- Contacts
- Analytics
- Exports / files

**The branch scope is determined by the `branch` field in the login response:**

```json
{
  "role": "spa_manager",
  "branch": "f1f603d8-b96f-4b19-ab8e-1b1065a93842",
  "branch_name": "Spa Empire Turbhe"
}
```

Store `branch` (UUID) and `branch_name` locally after login. Never accept or render data from a branch that does not match this UUID.

---

## 1. Authentication Overview

The system uses **two separate authentication mechanisms**:

| Type | Used For | Header / Token |
|---|---|---|
| **Device Auth** | Call log sync, heartbeat | `X-Device-ID` + `X-Device-Secret` |
| **User Auth (JWT)** | Manager login, call log view, leads, contacts, analytics | `Authorization: Bearer <access_token>` |

These two auth systems are **independent** and serve different purposes. Do not mix them.

---

## 2. Device Registration & Authentication

### Overview — Device Lifecycle

```
Admin creates device in dashboard
        |
        v
Registration Token printed/shared (e.g. "ABC123PX")
        |
        v
Android app calls  POST /devices/claim-registration/
        |
        v
Receives device_id + secret_key  ← Store permanently
        |
        v
Use X-Device-ID + X-Device-Secret headers for all device operations
```

---

### 2A. Claim Device Registration

Used **only once** during first setup. The technician enters the registration token shown on the admin dashboard.

- **URL**: `devices/claim-registration/`
- **Method**: `POST`
- **Auth**: None (public endpoint)

**Request Body**:
```json
{
  "token": "ABC123PX"
}
```

**Response (200 OK)**:
```json
{
  "status": "success",
  "device_id": "SPA-C2C081-93D1F5",
  "secret_key": "7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a",
  "branch_name": "Elegance Spa Mumbai",
  "branch_id": "f1f603d8-b96f-4b19-ab8e-1b1065a93842"
}
```

> **IMPORTANT**: Store `device_id` and `secret_key` immediately using `EncryptedSharedPreferences` or Android Keystore. This token is single-use — once claimed, the registration token is invalidated.

**Error Responses**:
| Code | Meaning |
|---|---|
| `400` | Missing or malformed `token` field |
| `404` | Token is invalid or already used |

---

### 2B. Device Authentication Headers

All device-authenticated endpoints require **both** of these headers:

| Header | Value | Example |
|---|---|---|
| `X-Device-ID` | String — device serial received from claim | `SPA-C2C081-93D1F5` |
| `X-Device-Secret` | String — 64-char secret received from claim | `7f8a9b0c...` |

**OkHttp Interceptor (Kotlin)**:
```kotlin
class DeviceAuthInterceptor(
    private val deviceId: String,
    private val deviceSecret: String
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request().newBuilder()
            .addHeader("X-Device-ID", deviceId)
            .addHeader("X-Device-Secret", deviceSecret)
            .build()
        return chain.proceed(request)
    }
}
```

**Authentication Failure Codes**:
| Code | Meaning | Action |
|---|---|---|
| `401` | Missing headers | Check credentials in storage |
| `401` | Invalid device ID | Device may be deleted from dashboard |
| `401` | Invalid secret | Credential mismatch — contact admin |
| `401` | Device not allowed | Device is **blocked or deactivated** — show alert to manager |

> **Security Rule**: Devices can only upload call logs for their own branch. The backend assigns the branch automatically from the device record. The Android app should **never** send a `branch` field in the sync payload.

---

## 3. Manager Authentication (JWT)

Branch managers log in using email/password or OTP.

---

### 3A. Login with Email & Password

- **URL**: `auth/login/`
- **Method**: `POST`
- **Auth**: None

**Request**:
```json
{
  "email": "manager@workspa.in",
  "password": "yourpassword"
}
```

**Response (200 OK)**:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "manager@workspa.in",
    "full_name": "Rahul Sharma",
    "role": "spa_manager",
    "branch": "f1f603d8-b96f-4b19-ab8e-1b1065a93842",
    "branch_name": "Spa Empire Turbhe",
    "is_online": true,
    "last_login_at": "2026-03-29T10:00:00Z",
    "last_seen_at": "2026-03-29T10:05:00Z"
  }
}
```

**Client-Side Role Check — Required**:
```kotlin
fun handleLoginResponse(response: LoginResponse) {
    if (response.user.role != "spa_manager") {
        // Clear any stored tokens immediately
        tokenStore.clear()
        showError("This app is for Branch Managers only. Access denied.")
        return
    }
    // Store tokens securely
    tokenStore.saveAccessToken(response.access)
    tokenStore.saveRefreshToken(response.refresh)
    // Store branch context
    sessionStore.saveBranchId(response.user.branch)
    sessionStore.saveBranchName(response.user.branch_name)
    navigateTo(HomeScreen)
}
```

---

### 3B. OTP Login

**Step 1 — Request OTP**:
- **URL**: `auth/otp/request/`
- **Method**: `POST`

```json
{
  "email": "manager@workspa.in"
}
```

**Step 2 — Verify OTP and Get Tokens**:
- **URL**: `auth/otp/verify/`
- **Method**: `POST`

```json
{
  "email": "manager@workspa.in",
  "otp": "348291"
}
```

Response is the same as the standard login response. Apply the same role check.

---

### 3C. JWT Token Storage & Refresh

**Token Storage (Kotlin)**:
```kotlin
// Use EncryptedSharedPreferences — never plain SharedPreferences
val masterKeyAlias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC)
val prefs = EncryptedSharedPreferences.create(
    "auth_prefs",
    masterKeyAlias,
    context,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)
prefs.edit().putString("access_token", token).apply()
```

**JWT Interceptor (Kotlin)**:
```kotlin
class JwtInterceptor(private val tokenStore: TokenStore) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = tokenStore.getAccessToken()
        val request = chain.request().newBuilder()
            .addHeader("Authorization", "Bearer $token")
            .build()
        val response = chain.proceed(request)
        if (response.code == 401) {
            // Token expired — trigger refresh
            val refreshed = refreshToken()
            if (refreshed) {
                return chain.proceed(
                    chain.request().newBuilder()
                        .addHeader("Authorization", "Bearer ${tokenStore.getAccessToken()}")
                        .build()
                )
            } else {
                // Refresh failed — force logout
                tokenStore.clear()
                navigateTo(LoginScreen)
            }
        }
        return response
    }
}
```

**Token Refresh Endpoint**:
- **URL**: `auth/token/refresh/`
- **Method**: `POST`

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 3D. Get Current User Profile

Retrieves the full profile details for the currently authenticated user.

- **URL**: `auth/profile/`
- **Method**: `GET`
- **Auth**: Bearer JWT Token

**Response (200 OK)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "manager@workspa.in",
  "full_name": "Rahul Sharma",
  "role": "spa_manager",
  "branch": "f1f603d8-b96f-4b19-ab8e-1b1065a93842",
  "branch_name": "Spa Empire Turbhe",
  "is_active": true
}
```

---

## 4. Call Log Sync (Device → Server)

### 4A. Upload Call Logs

Devices batch-upload call logs captured from the Android phone's call history.

- **URL**: `calllogs/sync/`
- **Method**: `POST`
- **Auth**: Device Headers (`X-Device-ID` + `X-Device-Secret`)

**Request Body** (Array of call log objects):
```json
[
  {
    "phone_number": "+919876543210",
    "call_type": "incoming",
    "duration": 120,
    "sim_slot": 1,
    "call_time": "2024-03-06T10:30:00Z",
    "call_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  {
    "phone_number": "+918765432109",
    "call_type": "missed",
    "duration": 0,
    "sim_slot": 2,
    "call_time": "2024-03-06T10:35:00Z",
    "call_hash": "5d41402abc4b2a76b9719d911017c592d0ef2773"
  }
]
```

**Field Reference**:
| Field | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | ✅ | Full number with country code |
| `call_type` | string | ✅ | One of: `incoming`, `outgoing`, `missed`, `rejected` |
| `duration` | integer | ✅ | Duration in seconds. Must be `0` for missed/rejected |
| `sim_slot` | integer | ✅ | Raw Android slot index (0 or 1). Backend normalizes to (1 or 2) |
| `call_time` | string | ✅ | ISO 8601 UTC format (`2024-03-06T10:30:00Z`) |
| `call_hash` | string | ✅ | Unique idempotency key. Must not change on retry |

**Response (201 Created)**:
```json
{
  "status": "success",
  "synced_count": 2
}
```

> **Branch Assignment**: The server automatically assigns `branch` from the device's registered branch. Never include a `branch` field in the payload.

---

### 4B. call_hash — Idempotency Key (Critical)

The `call_hash` prevents duplicate call logs on retry. It must be:
- **Unique** per call event
- **Persistent** across retries (same hash if the upload is retried)
- **Generated client-side** before upload

**Recommended hash generation (Kotlin)**:
```kotlin
fun generateCallHash(
    phoneNumber: String,
    callType: String,
    callTime: Long  // Unix timestamp in milliseconds
): String {
    val input = "$phoneNumber|$callType|$callTime"
    val digest = MessageDigest.getInstance("SHA-256")
    val hashBytes = digest.digest(input.toByteArray(Charsets.UTF_8))
    return hashBytes.joinToString("") { "%02x".format(it) }
}
```

---

### 4C. Background Sync with WorkManager

Use `WorkManager` for reliable background upload, even if the app is killed:

```kotlin
class CallLogSyncWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        return try {
            val pendingLogs = localDb.getPendingCallLogs()
            if (pendingLogs.isEmpty()) return Result.success()

            val response = apiService.syncCallLogs(pendingLogs)
            if (response.isSuccessful) {
                localDb.markAsSynced(pendingLogs)
                Result.success()
            } else {
                Result.retry()  // Will retry with exponential backoff
            }
        } catch (e: Exception) {
            Result.retry()
        }
    }
}

// Enqueue periodic sync every 15 minutes
val syncRequest = PeriodicWorkRequestBuilder<CallLogSyncWorker>(15, TimeUnit.MINUTES)
    .setConstraints(Constraints.Builder()
        .setRequiredNetworkType(NetworkType.CONNECTED)
        .build())
    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 1, TimeUnit.MINUTES)
    .build()

WorkManager.getInstance(context).enqueueUniquePeriodicWork(
    "call_log_sync",
    ExistingPeriodicWorkPolicy.KEEP,
    syncRequest
)
```

---

### 4D. Phone Number Normalization (Critical)

To ensure that calls from the same person are matched regardless of formatting (e.g., `+919876543210` vs `09876543210` vs `9876543210`), the server performs **normalization** on every synced call log:

1.  **Digit Extraction**: All non-digit characters are removed (`+`, `-`, spaces).
2.  **Slicing**: The server stores and matches only the **last 10 digits**.
3.  **Cross-Matching**: This normalized number is used to link calls to Contacts, Leads, and Missed Call Follow-ups.

**Developer Requirement**: Android developers should send the most complete number available. The backend handles the cleanup and 10-digit matching automatically.

---

## 5. Device Heartbeat

Heartbeat signals to the dashboard that the device is online and healthy.

- **URL**: `monitoring/heartbeat/`
- **Method**: `POST`
- **Auth**: Device Headers (`X-Device-ID` + `X-Device-Secret`)

**Request Body** (Optional but recommended):
```json
{
  "battery_level": 85,
  "signal_strength": -75,
  "app_version": "1.0.4",
  "storage_used_mb": 450.5,
  "sim_1_number": "+919876543210",
  "sim_2_number": "+918765432109"
}
```

**Response (200 OK)**:
```json
{
  "status": "heartbeat acknowledged"
}
```

---

### 5A. Heartbeat Trigger Strategy

The app must trigger heartbeat in the following situations:

| Trigger | Implementation | Interval |
|---|---|---|
| **Periodic background** | `WorkManager` `PeriodicWorkRequest` | Every 15 min (Android minimum) |
| **Network reconnected** | `ConnectivityManager.NetworkCallback` | Immediately on reconnect |
| **App moved to foreground** | `ProcessLifecycleOwner` observer | Immediately |

**Kotlin — Heartbeat on Network Reconnect**:
```kotlin
val networkCallback = object : ConnectivityManager.NetworkCallback() {
    override fun onAvailable(network: Network) {
        // Network restored — fire heartbeat immediately
        WorkManager.getInstance(context)
            .enqueue(OneTimeWorkRequestBuilder<HeartbeatWorker>().build())
    }
}
val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
cm.registerDefaultNetworkCallback(networkCallback)
```

**Kotlin — Heartbeat on App Foreground**:
```kotlin
ProcessLifecycleOwner.get().lifecycle.addObserver(object : DefaultLifecycleObserver {
    override fun onStart(owner: LifecycleOwner) {
        // App came to foreground
        CoroutineScope(Dispatchers.IO).launch {
            apiService.sendHeartbeat(HeartbeatRequest(
                batteryLevel = getBatteryLevel(),
                appVersion = BuildConfig.VERSION_NAME
            ))
        }
    }
})
```

---

## 6. Call Log History (Manager View)

Branch managers can view call logs for their assigned branch and device.

- **URL**: `calllogs/`
- **Method**: `GET`
- **Auth**: Bearer JWT Token

**Required Query Parameter**:
```
GET /api/v1/calllogs/?device={device_id}
```

> ⚠️ **Always send `?device={device_id}`** when displaying logs on the device's "Recent Calls" screen. Without it, the response may include logs from other phones registered to the same branch. `device_id` here is the string identifier like `SPA-C2C081-93D1F5`.

**Supported Query Parameters**:
| Parameter | Type | Example | Description |
|---|---|---|---|
| `device` | string | `SPA-C2C081-93D1F5` | Filter logs by this device's serial ID |
| `call_type` | string | `missed` | One of: `incoming`, `outgoing`, `missed`, `rejected` |
| `start_date` | date | `2024-03-01` | Filter from this date (inclusive) |
| `end_date` | date | `2024-03-31` | Filter to this date (inclusive) |
| `search` | string | `9876` | Partial match on phone number |
| `lead_status` | string | `pending` | Filter by lead status (ringing, coming, etc.) |
| `sla_status` | string | `GOOD` | Filter by follow-up speed (GOOD, OK, LATE, MISSED) |

**Response**:
```json
{
  "count": 150,
  "next": "https://api.spa.branch.call.workspa.in/api/v1/calllogs/?page=2",
  "previous": null,
  "results": [
    {
      "id": "76e4b58a-ab27-41bc-be14-557fa1560287",
      "phone_number": "9876543210",
      "call_type": "incoming",
      "duration": 45,
      "sim_slot": 1,
      "receiver_number": "9900112233",
      "call_time": "2024-03-06T12:00:00Z",
      "branch_name": "Spa Empire Turbhe",
      "device_uid": "SPA-C2C081-93D1F5",
      "contact_name": "Amit Sharma",
      "lead_status": "pending",
      "lead_id": "c1f1f2e3-8274-4a25-b34a-7858211e1a53",
      "followup_status": "GOOD",
      "is_followed_up": true,
      "created_at": "2024-03-06T12:01:00Z"
    }
  ]
}
```

**New Follow-up Fields**:
| Field | Type | Description |
|---|---|---|
| `followup_status` | string | SLA status for missed calls: `GOOD`, `OK`, `LATE`, `MISSED` |
| `is_followed_up` | boolean | `true` if an outgoing call was made after the missed call |


> **Backend Enforcement**: The backend always filters call logs by the manager's assigned branch automatically based on the JWT token. Even if the `device` param is omitted, no cross-branch data will ever be returned.

---

## 7. Contact Management

Contacts are customer records matched to call log phone numbers.

- **Auth**: Bearer JWT Token
- **Branch Scope**: Automatic — managers only see contacts linked to their branch's calls.

### 7A. List / Search Contacts

- **URL**: `contacts/`
- **Method**: `GET`
- **Query Params**: `?search=9876543210`

**Response**:
```json
[
  {
    "id": "c1112223-e29b-41d4-a716-446655440222",
    "name": "Amit Sharma",
    "phone_number": "9876543210",
    "email": "amit@example.com",
    "city": "Mumbai",
    "created_at": "2024-03-01T10:00:00Z"
  }
]
```

### 7B. Create Contact

- **URL**: `contacts/`
- **Method**: `POST`

```json
{
  "name": "New Customer",
  "phone_number": "9988776655",
  "email": "customer@gmail.com",
  "city": "Pune"
}
```

---

## 8. Lead Management

Leads are potential bookings generated automatically from call logs, or manually created.

- **Auth**: Bearer JWT Token
- **Branch Scope**: Automatic — managers only see leads belonging to their branch.

### 8A. List Branch Leads

- **URL**: `leadmanagement/`
- **Method**: `GET`
- **Query Params**: `?status=pending`, `?search=9876`

**Response**:
```json
{
  "count": 120,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": "c1f1f2e3-8274-4a25-b34a-7858211e1a53",
      "branch_name": "Spa Empire Turbhe",
      "contact_name": "Amit Sharma",
      "phone_number": "9876543210",
      "call_type": "incoming",
      "status": "pending",
      "booking_date": null,
      "remarks": "Wants to visit tomorrow",
      "created_at": "2024-03-05T14:30:00Z"
    }
  ]
}
```

### 8B. Update Lead Status

- **URL**: `leadmanagement/{lead_id}/`
- **Method**: `PATCH`

```json
{
  "status": "coming",
  "booking_date": "2024-03-10",
  "remarks": "Confirmed appointment for 2 PM"
}
```

**Valid Status Values**:
| Status | Meaning |
|---|---|
| `pending` | New lead, not yet contacted |
| `ringing` | Currently trying to reach customer |
| `coming` | Customer confirmed visit |
| `interested` | Customer expressed interest |
| `not_interested` | Customer declined |

### 8C. Create Manual Lead

- **URL**: `leadmanagement/`
- **Method**: `POST`

```json
{
  "phone_number": "9988776655",
  "status": "pending",
  "remarks": "Met in person at the branch"
}
```

> The backend automatically assigns the lead to the logged-in manager's branch.

### 8D. Lead Sync Logic (Automatic)
The system automatically creates a lead whenever a call log is synced via the `/calllogs/sync/` endpoint.
- **Direct Sync**: Leads linked to a `calllog_id` are considered "Directly Synced".
- **Manual**: Leads created via `POST /leadmanagement/` are considered manual records.
- Managers can filter and track performance based on these sources.

---

### 8E. Missed Call Follow-up System

The system tracks how quickly managers call back customers who missed a call. This is handled automatically by the server.

1.  **Trigger**: When a `missed` call is synced, an entry is created in the tracking system.
2.  **Resolution**: When an `outgoing` call is made to the **same number** (using 10-digit matching) at a later time, the missed call is marked as "Followed Up".
3.  **SLA Windows**:
    *   **GOOD**: Called back within 10 minutes.
    *   **OK**: Called back within 30 minutes.
    *   **LATE**: Called back within 60 minutes.
    *   **MISSED**: No call back or > 60 minutes.

**Developer Requirement**: Android developers do not need to call any special endpoints for this. Simply ensuring that **outgoing calls** are synced correctly will trigger the automatic resolution on the backend.

---

## 9. Dashboard Analytics

- **URL**: `analytics/overview/`
- **Method**: `GET`
- **Auth**: Bearer JWT Token
- **Query Params**: `?time_filter=today`

**Supported `time_filter` values**: `today`, `yesterday`, `last_7_days`, `last_30_days`, `this_month`, `custom`

**Response**:
```json
{
  "conversion_rates": [
    {"name": "Incoming", "value": 45},
    {"name": "Outgoing", "value": 12},
    {"name": "Missed", "value": 5},
    {"name": "Rejected", "value": 2}
  ],
  "followed_up": 35,
  "sla_good": 25,
  "sla_missed": 10,
  "unique_count": 85,
  "total": 64
}
```

**Field Descriptions**:
| Field | Description |
|---|---|
| `followed_up` | Total number of missed calls that received a callback |
| `sla_good` | Number of callbacks made within the 10-minute "GOOD" window |
| `sla_missed` | Missed calls with no callback or callback > 60 minutes |
| `unique_count` | Number of unique customer phone numbers (matched via 10-digits) |

> **Branch Scope**: Analytics are automatically scoped to the manager's branch by the backend. No filtering parameter is needed.

---

## 10. Device Inventory & Status

### 10A. Device Statistics
- **URL**: `devices/stats/`
- **Method**: `GET`
- **Auth**: Bearer JWT Token

Returns aggregate statistics for all devices in the manager's branch.

**Response**:
```json
{
  "total": 5,
  "registered": 4,
  "unregistered": 1,
  "online": 2,
  "offline": 2,
  "blocked": 0,
  "inactive": 0
}
```

### 10B. Health Monitoring Status
- **URL**: `monitoring/status/`
- **Method**: `GET`
- **Auth**: Bearer JWT Token

Returns a summary of device health and pending alert counts.

**Response**:
```json
{
  "total_devices": 5,
  "active_devices": 2,
  "online_devices": 2,
  "offline_alerts": 1,
  "sim_change_alerts": 0
}
```

---

## 11. Response Status Code Reference

| Code | Meaning | Recommended Action |
|---|---|---|
| `200` | OK — Request successful | Process response normally |
| `201` | Created — Resource created | Show success confirmation |
| `400` | Bad Request — Validation failed | Read `details` field for field-level errors |
| `401` | Unauthorized | Check token or device credentials. If device: may be blocked |
| `403` | Forbidden | User does not have permission for this action |
| `404` | Not Found | Resource or registration token does not exist |
| `500` | Server Error | Log the error, retry later, contact backend admin |

**Example Validation Error (400)**:
```json
{
  "error": "Validation Error",
  "details": ["phone_number: This field is required."]
}
```

---

## 12. Data Security Rules

These rules are enforced both on the **backend** and must be respected by the **Android client**:

| Rule | Backend Enforcement | Client Requirement |
|---|---|---|
| Branch managers only see their branch data | ✅ JWT-based queryset filtering | ✅ Role check after login |
| Devices can only upload logs for their branch | ✅ Device → branch is server-resolved | ✅ Never send `branch` in payload |
| Unauthorized devices get `401` | ✅ `DeviceAuthentication` class | ✅ Show alert if `401` is persistent |
| Role must be `spa_manager` | ❌ Not enforced by backend login | ✅ **Must be enforced by Android app** |
| Tokens stored securely | N/A | ✅ Use `EncryptedSharedPreferences` |
| Device credentials stored securely | N/A | ✅ Use Android Keystore |

---

## 13. Android Developer Checklist

Use this checklist before releasing any version of the app:

**Networking**
- [ ] Use **Retrofit** with **OkHttp** client
- [ ] Add `DeviceAuthInterceptor` for all device-authenticated endpoints
- [ ] Add `JwtInterceptor` for all manager-authenticated endpoints
- [ ] Implement **token refresh** logic in the JWT interceptor
- [ ] Handle `401` responses for both device and user auth

**Security**
- [ ] Store `access_token` and `refresh_token` in `EncryptedSharedPreferences`
- [ ] Store `device_id` and `secret_key` in `EncryptedSharedPreferences` or Android Keystore
- [ ] **Validate `role == "spa_manager"` after every login attempt**
- [ ] Clear all tokens on logout

**Call Log Sync**
- [ ] Use **WorkManager** for background sync (15-minute periodic + on-demand)
- [ ] Generate and persist `call_hash` before attempting upload
- [ ] Do **not** change `call_hash` on retry
- [ ] Implement exponential backoff with `Result.retry()`
- [ ] Mark logs as synced only after a `201` response

**Heartbeat**
- [ ] Schedule periodic heartbeat (15-minute `PeriodicWorkRequest`)
- [ ] Trigger instant heartbeat on network restore (`ConnectivityManager.NetworkCallback`)
- [ ] Trigger instant heartbeat on app foreground (`ProcessLifecycleOwner`)

**Data Isolation**
- [ ] Always pass `?device={device_id}` when listing call logs
- [ ] Display only data from the manager's assigned `branch_name`
- [ ] Never allow cross-branch navigation or data access

---

## 14. Constants Reference

**Lead Statuses**:
```
pending | ringing | coming | interested | not_interested
```

**Call Types**:
```
incoming | outgoing | missed | rejected
```

**User Roles** (for reference only — only `spa_manager` is allowed):
```
super_admin | admin | spa_manager
```

**Device ID Format**:
```
SPA-XXXXXX-XXXXXX   (e.g. SPA-C2C081-93D1F5)
```

**Secret Key Format**:
```
64 hex characters   (e.g. 7f8a9b0c1d2e3f4a...)
```

**Registration Token Format**:
```
12 uppercase hex characters   (e.g. ABC123PX9D2F)
```

---

## 15. Full Device Registration Flow (Step by Step)

```
1. Admin opens web dashboard
2. Admin creates a Device record, assigns it to a Branch
3. Dashboard displays a Registration Token (e.g. "DF9A3C")

4. Technician installs the Android app on the branch phone
5. App shows "Enter Registration Token" screen
6. Technician types "DF9A3C"

7. App calls: POST /devices/claim-registration/  { "token": "DF9A3C" }
8. Server validates token, marks device as registered, clears token
9. Server returns: device_id + secret_key + branch_name

10. App stores device_id and secret_key in EncryptedSharedPreferences
11. App shows success: "Device registered to Spa Empire Turbhe"

12. From this point, all sync/heartbeat calls use X-Device-ID + X-Device-Secret headers
```

---

## 16. Manager Login Flow (Step by Step)

```
1. Manager opens app
2. App shows login screen (email + password)

3. Manager enters credentials
4. App calls: POST /auth/login/

5. Server returns: access + refresh + user profile

6. App checks: user.role === "spa_manager"
   → If NOT spa_manager: clear tokens, show "Access Denied", stop
   → If spa_manager: continue

7. App stores:
   - access_token (EncryptedSharedPreferences)
   - refresh_token (EncryptedSharedPreferences)
   - branch_id (session store)
   - branch_name (session store)

8. App navigates to Home / Dashboard screen

9. All subsequent API calls include: Authorization: Bearer {access_token}

10. When access_token expires (401 response):
    → App calls POST /auth/token/refresh/ with refresh_token
    → On success: store new access_token, retry original request
    → On failure: clear all tokens, redirect to Login screen
```

---

## 17. Push Notifications (FCM) Integration

The system uses **Firebase Cloud Messaging (FCM)** to send real-time alerts to the device (Battery alerts, Sync issues, Admin announcements).

### 17A. Register/Update FCM Token

The Android app must obtain its FCM registration token and send it to the server immediately after registration and whenever the token changes.

- **URL**: `devices/update-fcm-token/`
- **Method**: `POST`
- **Auth**: Device Headers (`X-Device-ID` + `X-Device-Secret`)

**Request Body**:
```json
{
  "fcm_token": "fcm_token_received_from_firebase_sdk_..."
}
```

**Response (200 OK)**:
```json
{
  "status": "success",
  "message": "FCM token updated"
}
```

---

### 17B. Notification Payload Structure

The server sends notifications as **Data Messages** (not Notification Messages) to give the app full control over display logic.

**Data Payload Sample**:
```json
{
  "title": "Battery Low",
  "body": "Device is at 12%. Please connect to power.",
  "type": "alert",
  "sent_at": "2024-03-06T12:00:00Z"
}
```

**Notification Types**:
| Type | Use Case |
|---|---|
| `reminder` | Sync reminder, daily summary |
| `alert` | **Battery Low (<15%)**, Sync Failures |
| `system` | Admin announcements, App updates |
| `sync_issue` | Device offline for >5 mins |

**Kotlin — Handling FCM in `onMessageReceived`**:
```kotlin
override fun onMessageReceived(remoteMessage: RemoteMessage) {
    val data = remoteMessage.data
    val title = data["title"]
    val body = data["body"]
    val type = data["type"] // e.g., "alert", "sync_issue"

    showLocalNotification(title, body, type)

    // Example logic for specific types
    if (type == "sync_issue") {
        // Suggested action: Trigger an immediate sync log upload
        WorkManager.getInstance(context).enqueue(OneTimeWorkRequestBuilder<SyncWorker>().build())
    }
}
```

---

### 17C. Notification Management (Resolve/Clear)

If the app shows a list of system alerts/notifications, use these endpoints to keep the dashboard and device in sync.

#### 1. Resolve Single Alert (Mark as Read)
- **URL**: `monitoring/device-events/{id}/resolve/`
- **Method**: `POST`
- **Auth**: Bearer JWT

#### 2. Resolve All Alerts
- **URL**: `monitoring/device-events/resolve_all/`
- **Method**: `POST`
- **Auth**: Bearer JWT

#### 3. Delete Alert Log
- **URL**: `monitoring/device-events/{id}/`
- **Method**: `DELETE`
- **Auth**: Bearer JWT

---

### 17D. Notification History & Stats (JWT Auth)

If the app needs to display a history of push notifications sent by the server, use these endpoints:

#### 1. List Notification Logs
- **URL**: `notifications/logs/`
- **Method**: `GET`
- **Auth**: Bearer JWT

#### 2. Get Notification Stats (Delivery Rate)
- **URL**: `notifications/stats/`
- **Method**: `GET`
- **Auth**: Bearer JWT

#### 3. Clear All Notification History
- **URL**: `notifications/logs/delete_all/`
- **Method**: `DELETE`
- **Auth**: Bearer JWT

---

## 18. Automated Alert Triggers (Backend Logic)

The backend monitors device health via the **Heartbeat** and automatically triggers push notifications for these events:

| Event | Logic | Notification Sent |
|---|---|---|
| **Critical Battery** | `battery_level` < 15 in Heartbeat payload | **Immediate** "alert" push |
| **SIM Change** | `sim_1_number` or `sim_2_number` changed in Heartbeat | **Immediate** "alert" push |
| **Offline Device** | No Heartbeat received for >5 minutes | "sync_issue" push to branch |
| **Sync Failure** | Reported sync errors from device | "alert" push |

---

## 19. Android Developer Final Checklist

- [ ] Obtain FCM token and call `update-fcm-token/` on first run.
- [ ] Implement `FirebaseMessagingService` to handle data-type payloads.
- [ ] Ensure `battery_level` (0-100) is always included in the `monitoring/heartbeat/` call.
- [ ] Validate that notifications appear even when the app is in the background.
- [ ] Role check remains in place: `role === "spa_manager"` only.

---

## 20. Backend Architecture & Service Overview

To help you understand how the system works behind the scenes, here is a summary of the backend components that power the Android experience.

### 20A. Notification Engine
The backend uses a **centralized `NotificationService`** that handles both the logic for sending push notifications and logging them for audit.
- **Auto-Initialization**: The Firebase Admin SDK is initialized once when the Django server starts.
- **Audit Logs**: Every notification (sent or failed) is stored in a database table. You can view these logs in the Admin Dashboard to debug delivery issues.

### 20B. Real-time Monitoring & Alert Logic
The backend performs "intelligence" checks based on the data you send in the Heartbeat and Call Log Sync:

1.  **Low Battery Detection**: 
    If you send `battery_level < 15` in the heartbeat, the backend immediately triggers an FCM message with `type: "alert"`.
2.  **Device "Ghosting" (Offline Check)**:
    A background task (Celery) runs every 5 minutes. If it detects a device hasn't sent a heartbeat for a period exceeding the expected interval, it marks the device as "offline" and notifies the relevant branch managers.
3.  **Permission/Storage Health**:
    The backend exposes endpoints to report specific device events. If the app reports `storage_full` or `permission_denied`, the system creates a high-priority alert.

### 20C. Data Scoping & Security
- **JWT Middleware**: All requests to `leadmanagement/` or `calllogs/` (Manager View) pass through a middleware that extracts the `branch_id` from the token. This ensures a manager can **never** even see the existence of data from another branch.
- **Device Authentication**: The `X-Device-ID` and `X-Device-Secret` are validated against a hashed secret in the database, similar to an API key system.

---

## 21. Real-time Notifications & User Tracking (WebSockets)

The system supports real-time WebSockets to deliver branch-scoped notifications instantly while the app is in the foreground, and to track user status.

- **WebSocket URL**: `ws://{domain}/ws/crm/?token={jwt_access_token}`
  - Note: Replace `ws://` with `wss://` in production.
- **Auth**: The JWT token **must** be passed as a query parameter `?token=...`. Standard `Authorization` headers are not supported by the WebSocket connection.
- **Branch Scoping**: Upon connection, the backend checks the manager's `role` and automatically assigns the WebSocket to the group `branch_{branch_id}`. The client will only receive notifications/events for their assigned branch.

**Key Features / Events**:
- **Connection**: Mark user as `is_online = true`.
- **Disconnection**: Mark user as `is_online = false`.
- **Broadcast Events**: The Android app should listen to the WebSocket stream. The server pushes JSON payloads (e.g., `{"type": "notification", "message": "...", "title": "..."}`) directly to the `branch_{branch_id}` channel.

**Kotlin — Connecting with OkHttp**:
```kotlin
val token = tokenStore.getAccessToken()
val request = Request.Builder()
    .url("wss://api.spa.branch.call.workspa.in/ws/crm/?token=$token")
    .build()

val listener = object : WebSocketListener() {
    override fun onMessage(webSocket: WebSocket, text: String) {
        val json = JSONObject(text)
        // Handle incoming real-time branch notifications
        if (json.optString("type") == "notification") {
            showInAppBanner(json.getString("title"), json.getString("message"))
        }
    }
}
val webSocket = okHttpClient.newWebSocket(request, listener)
```

---

## 22. Login History & Audit Logs

Managers and Admins can view a detailed audit log of all login activities across the branch.

### 22A. List Login Records
- **URL**: `auth/login-history/`
- **Method**: `GET`
- **Auth**: Bearer JWT Token
- **Query Params**: `?user={user_id}` (optional)

**Response**:
```json
{
  "count": 45,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "user_name": "Rahul Sharma",
      "user_email": "manager@workspa.in",
      "user_role": "spa_manager",
      "branch_name": "Spa Empire Turbhe",
      "ip_address": "122.161.x.x",
      "user_agent": "Mozilla/5.0 (Linux; Android 13; ...)",
      "login_at": "2026-03-29T10:00:00Z",
      "status": "success"
    }
  ]
}
```
