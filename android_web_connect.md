# Call Log System - Backend Structures & Android Connection Mapping

This document outlines the database structure for the core components of the Call Log tracking system (`Branches`, `Devices`, and `CallLogs`) and explains how the physical Android devices map to these models to sync data.

---

## 1. Apps & Model Structures

### `apps/branches` (Branch Model)
The **Branch** model acts as the parent container for everything. It represents a physical Spa location.
*   **Concepts Used**: Inherits from core models (`BaseModel` for UUIDs, `TimeStampedModel` for `created_at`/`updated_at`, `SoftDeleteModel` for safe deletion padding).
*   **Key Fields**:
    *   `spa_name`: The name of the spa/branch.
    *   `code`: A unique alphanumeric identifier.
    *   `state`, `city`, `area`, `postal_code`, `address`: Geographical tracking.
    *   `is_active`: Boolean toggle to suspend a branch without deleting data.

### `apps/devices` (Device Model)
The **Device** model represents a specialized Android smartphone assigned to a Branch.
*   **Concepts Used**: Also inherits from `BaseModel`, `TimeStampedModel`, and `SoftDeleteModel`. 
*   **Key Fields**:
    *   `branch`: A `ForeignKey` linking the device to a specific Branch. If a branch is deleted, its devices are deleted in a cascade (though `SoftDeleteModel` prevents hard deletions).
    *   `device_id`: A `CharField` (Unique) string representing the immutable hardware ID of the mobile phone (e.g., Android Secure ID or IMEI).
    *   `secret_key`: An auto-generated 64-character hex string created automatically on `save()`. This is essentially an API Key for that specific phone.
    *   `sim_1_number` & `sim_2_number`: Tracks which phone numbers are installed.
    *   `last_sync` & `last_heartbeat`: Tracks connection health.

### `apps/calllogs` (CallLog Model)
The **CallLog** model represents individual phone calls recorded by the Android devices. This table acts as a **write-heavy, analytics-bound transactional store**.
*   **Concepts Used**: Uses heavy database indexing because this table will grow massive very quickly. For optimal read-performance on analytics charts over time, a compound index on `branch` and `call_time` is highly recommended:
    ```python
    class Meta:
        indexes = [
            models.Index(fields=["branch", "call_time"]),
            models.Index(fields=["call_time"]),
            models.Index(fields=["branch"]),
            models.Index(fields=["device"]),
            models.Index(fields=["phone_number"]),
        ]
    ```
*   **Key Fields**:
    *   `branch` & `device`: Foreign keys pinpointing exactly where and through what hardware the call happened.
    *   `phone_number`: The customer's caller ID.
    *   `call_type`: A choice field defining the nature of the call (e.g., `incoming`, `outgoing`, `missed`, `rejected`).
    *   `duration`: Stored purely in seconds.
    *   `sim_slot`: Indicates if SIM 1 or SIM 2 received the call.
    *   `call_time`: The exact timestamp of the call.
    *   `call_hash`: A unique 64-character string designed to prevent the Android app from uploading the exact same call twice (Idempotency Key). Even if an Android device retries uploading a payload 10 times, the database will safely ignore duplicate hashes, preventing corruption.

---

## 2. How Android Devices Map to Models

The connection between the physical Android phones and the Django backend relies strictly on the **Device** table acting as the authentication and routing bridge.

Here is the operational lifecycle of how the app maps to the database:

### Phase 1: Registration (Web to Android)
1.  An Admin logs into the Django Web Dashboard.
2.  They create a new **Branch**.
3.  They create a new **Device**, selecting the Branch and pasting in the phone's hardware `device_id`.
4.  Django instantly generates a 64-character `secret_key` for that record.
5.  The Admin installs the custom Android App on the phone and inputs (or scans via QR) the `device_id` and `secret_key`.

### Phase 2: Heartbeat & Health (Android to Web)
1.  Every few minutes, the Android app pings a `/monitoring/status/` endpoint using its `secret_key` and `device_id`.
2.  Django receives the ping, looks up the `Device` by its `device_id`, verifies the `secret_key`, and updates the `last_heartbeat` timestamp in the database.
3.  If the device is marked `is_blocked = True` in the database, Django rejects the ping and forces the Android app to halt processing.

### Phase 3: Syncing Call Logs (Android to Web)
1.  The Android App uses `READ_CALL_LOG` permissions to monitor the phone's native dialer.
2.  When a call finishes, the App bundles the details (`phone_number`, `duration`, `call_type`, `sim_slot`, `call_time`).
3.  The App generates a locally-computed `call_hash` (likely combining the phone number + exact time + duration) to uniquely identify the call.
4.  The App POSTs a JSON array of these calls to the `/calllogs/` Django API endpoint, authenticating via its `secret_key` header/payload.
5.  Django intercepts the payload:
    *   Looks up the `Device` sending it.
    *   Looks up the `Branch` that `Device` belongs to.
    *   Automatically tags those `Branch` and `Device` ForeignKeys onto every `CallLog` object.
    *   Attempts to save. If the `call_hash` already exists in the database, it safely skips it (ignoring duplicates).
6.  Django updates the `last_sync` timestamp on the `Device` model to log a successful data upload.

---

## 3. Scale & Security Maturity Path

While the current architecture securely bridges multi-tenant isolation with idempotent bulk ingestion rules, preparing for scale (e.g., 30M+ rows or hundreds of branches) will require these enterprise enhancements:

### Database Scaling
- **PostgreSQL Monthly Partitioning**: The `CallLog` table should eventually be structured via declarative PostgreSQL partitioning partitioned by `call_time` (Monthly). This prevents B-Tree index bloat and ensures aggressive aggregation queries remain under 100ms.

### Ingestion Security Hardening
To upgrade the API ingestion layer from Level 2 to Level 3 enterprise security:
- **Request HMAC Signing**: Instead of passing the `secret_key` raw in headers, the Android app should hash the `payload + timestamp` with the `secret_key` and send the HMAC footprint to prevent Man-In-The-Middle manipulation.
- **Strict Rate Limiting**: Implement Django Ratelimit or NGINX layers on the `/calllogs/` endpoint preventing DDoS synchronization floods.
- **Device Anomaly Detection**: Track logging frequencies per-phone relative to branch operating hours.
- **Encrypted Local SQLite**: Ensure the Android app itself encrypts its local Room/SQLite store before transmission in case the physical device is compromised.
